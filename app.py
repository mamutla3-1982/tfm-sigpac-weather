from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
import jwt
import requests
from functools import wraps

app = Flask(__name__)

# ── CONFIGURACIÓN ──
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sigpac_weather_2026_secret')
app.config['MONGO_URI'] = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/sigpac_weather')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt_secret_2026')
app.config['AEMET_API_KEY'] = os.environ.get('AEMET_API_KEY', '')

mongo = PyMongo(app)

# ── FUNCIONES JWT ──
def crear_token(user_id):
    """Crea un token JWT para el usuario"""
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def verificar_token(token):
    """Verifica el token JWT"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

def login_requerido(f):
    """Decorador para rutas protegidas"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            token = token.replace('Bearer ', '')
            user_id = verificar_token(token)
            if user_id:
                request.current_user_id = user_id
                return f(*args, **kwargs)
        return jsonify({'error': 'No autorizado'}), 401
    return decorated

# ── RUTAS ESTÁTICAS ──
@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir archivos estáticos"""
    return send_from_directory('static', filename)

# ── RUTAS HTML ──
@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

# ── API AUTENTICACIÓN ──
@app.route('/api/auth/registro', methods=['POST'])
def registro():
    """Registrar nuevo usuario"""
    data = request.json
    
    # Validar campos requeridos
    required = ['username', 'nombre', 'email', 'password', 'passwordConfirm']
    if not all(k in data for k in required):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
    
    # Validar que las contraseñas coincidan
    if data['password'] != data['passwordConfirm']:
        return jsonify({'error': 'Las contraseñas no coinciden'}), 400
    
    # Verificar si ya existe el email
    if mongo.db.usuarios.find_one({'email': data['email'].lower()}):
        return jsonify({'error': 'Ya existe una cuenta con ese email'}), 400
    
    # Verificar si ya existe el username
    if mongo.db.usuarios.find_one({'username': data['username']}):
        return jsonify({'error': 'Ese nombre de usuario ya está en uso'}), 400
    
    # Crear usuario
    usuario = {
        'username': data['username'],
        'nombre': data['nombre'],
        'email': data['email'].lower(),
        'password': generate_password_hash(data['password']),
        'created_at': datetime.utcnow()
    }
    
    result = mongo.db.usuarios.insert_one(usuario)
    token = crear_token(result.inserted_id)
    
    return jsonify({
        'token': token,
        'usuario': {
            'id': str(result.inserted_id),
            'username': usuario['username'],
            'nombre': usuario['nombre'],
            'email': usuario['email']
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    data = request.json
    
    # Buscar por email o username
    usuario = mongo.db.usuarios.find_one({
        '$or': [
            {'email': data.get('emailOrUsername', '').lower()},
            {'username': data.get('emailOrUsername', '')}
        ]
    })
    
    if not usuario or not check_password_hash(usuario['password'], data.get('password', '')):
        return jsonify({'error': 'Email/Usuario o contraseña incorrectos'}), 401
    
    token = crear_token(usuario['_id'])
    
    return jsonify({
        'token': token,
        'usuario': {
            'id': str(usuario['_id']),
            'username': usuario['username'],
            'nombre': usuario['nombre'],
            'email': usuario['email']
        }
    })

@app.route('/api/auth/perfil')
@login_requerido
def perfil():
    """Obtener perfil del usuario"""
    usuario = mongo.db.usuarios.find_one({'_id': ObjectId(request.current_user_id)})
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'usuario': {
            'id': str(usuario['_id']),
            'username': usuario['username'],
            'nombre': usuario['nombre'],
            'email': usuario['email']
        }
    })

# ── API PARCELAS ──
@app.route('/api/parcelas', methods=['GET'])
@login_requerido
def obtener_parcelas():
    """Obtener todas las parcelas del usuario"""
    parcelas = list(mongo.db.parcelas.find({'user_id': request.current_user_id}))
    
    for p in parcelas:
        p['_id'] = str(p['_id'])
    
    return jsonify({'parcelas': parcelas})

@app.route('/api/parcelas', methods=['POST'])
@login_requerido
def crear_parcela():
    """Crear nueva parcela"""
    data = request.json
    
    parcela = {
        'user_id': request.current_user_id,
        'nombre': data.get('nombre'),
        'provincia': data.get('provincia', ''),
        'municipio': data.get('municipio', ''),
        'poligono': data.get('poligono', ''),
        'parcela_num': data.get('parcela_num', ''),
        'cultivo': data.get('cultivo', ''),
        'superficie': data.get('superficie', 0),
        'coordenadas': data.get('coordenadas'),
        'centroide': data.get('centroide'),
        'created_at': datetime.utcnow()
    }
    
    result = mongo.db.parcelas.insert_one(parcela)
    parcela['_id'] = str(result.inserted_id)
    
    return jsonify({'parcela': parcela}), 201

@app.route('/api/parcelas/<parcela_id>', methods=['GET'])
@login_requerido
def obtener_parcela(parcela_id):
    """Obtener una parcela específica con datos meteorológicos"""
    parcela = mongo.db.parcelas.find_one({
        '_id': ObjectId(parcela_id),
        'user_id': request.current_user_id
    })
    
    if not parcela:
        return jsonify({'error': 'Parcela no encontrada'}), 404
    
    parcela['_id'] = str(parcela['_id'])
    
    # Obtener datos meteorológicos si hay coordenadas
    if parcela.get('centroide'):
        lat = parcela['centroide']['lat']
        lng = parcela['centroide']['lng']
        
        # Aquí se integraría con AEMET para obtener datos reales
        # Por ahora generamos datos de ejemplo
        parcela['meteo'] = {
            'lluvia_diaria': generar_datos_lluvia_diaria(),
            'lluvia_mensual': generar_datos_lluvia_mensual(),
            'lluvia_anual': generar_datos_lluvia_anual(),
            'lluvia_historico': generar_datos_lluvia_historico()
        }
    
    return jsonify({'parcela': parcela})

@app.route('/api/parcelas/<parcela_id>', methods=['DELETE'])
@login_requerido
def eliminar_parcela(parcela_id):
    """Eliminar parcela"""
    result = mongo.db.parcelas.delete_one({
        '_id': ObjectId(parcela_id),
        'user_id': request.current_user_id
    })
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Parcela no encontrada'}), 404
    
    return jsonify({'mensaje': 'Parcela eliminada'})

# ── API AEMET ──
@app.route('/api/aemet/municipios')
def buscar_municipios():
    """Buscar municipios (para autocompletado)"""
    query = request.args.get('q', '').lower()
    
    # Lista simplificada de municipios (en producción vendría de AEMET o base de datos)
    municipios = [
        {'codigo': '28079', 'nombre': 'Madrid', 'provincia': 'Madrid'},
        {'codigo': '41091', 'nombre': 'Sevilla', 'provincia': 'Sevilla'},
        {'codigo': '08019', 'nombre': 'Barcelona', 'provincia': 'Barcelona'},
        {'codigo': '46250', 'nombre': 'Valencia', 'provincia': 'Valencia'},
        {'codigo': '11012', 'nombre': 'Cádiz', 'provincia': 'Cádiz'},
        {'codigo': '14021', 'nombre': 'Córdoba', 'provincia': 'Córdoba'},
        {'codigo': '18087', 'nombre': 'Granada', 'provincia': 'Granada'},
        {'codigo': '21041', 'nombre': 'Huelva', 'provincia': 'Huelva'},
        {'codigo': '23050', 'nombre': 'Jaén', 'provincia': 'Jaén'},
        {'codigo': '29067', 'nombre': 'Málaga', 'provincia': 'Málaga'},
    ]
    
    resultados = [m for m in municipios if query in m['nombre'].lower()]
    return jsonify({'municipios': resultados[:10]})

# ── FUNCIONES AUXILIARES PARA DATOS METEOROLÓGICOS ──
def generar_datos_lluvia_diaria():
    """Genera datos de lluvia para los últimos 30 días"""
    import random
    datos = []
    for i in range(30):
        fecha = (datetime.now() - timedelta(days=29-i)).strftime('%d/%m')
        datos.append({
            'fecha': fecha,
            'lluvia': round(random.uniform(0, 15), 1)
        })
    return datos

def generar_datos_lluvia_mensual():
    """Genera datos de lluvia mensual del año actual"""
    import random
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    mes_actual = datetime.now().month
    datos = []
    for i in range(mes_actual):
        datos.append({
            'mes': meses[i],
            'lluvia': round(random.uniform(20, 80), 1)
        })
    return datos

def generar_datos_lluvia_anual():
    """Genera datos de lluvia anual de los últimos 5 años"""
    import random
    año_actual = datetime.now().year
    datos = []
    for i in range(5):
        datos.append({
            'año': año_actual - 4 + i,
            'lluvia': round(random.uniform(400, 800), 1)
        })
    return datos

def generar_datos_lluvia_historico():
    """Genera datos de lluvia histórico de los últimos 10 años"""
    import random
    año_actual = datetime.now().year
    datos = []
    for i in range(10):
        datos.append({
            'año': año_actual - 9 + i,
            'lluvia': round(random.uniform(350, 850), 1)
        })
    return datos

# ── API HEALTH (KEEP-ALIVE) ──
@app.route('/api/health')
def health():
    """Endpoint para keep-alive"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'db': 'connected' if mongo.cx else 'disconnected'
    })

# ── GEOCODING REVERSO ──
@app.route('/api/geocode/reverse')
def geocode_reverse():
    """Obtener provincia y municipio de coordenadas"""
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    
    # Aquí se integraría con un servicio de geocoding real
    # Por ahora retornamos datos de ejemplo
    return jsonify({
        'provincia': 'Sevilla',
        'municipio': 'Jerez de la Frontera',
        'lugar': 'Zona Agrícola Norte'
    })

# ── INICIAR APP ──
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
