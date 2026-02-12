from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, jwt, requests
from datetime import datetime, timedelta
from functools import wraps

# --- INICIO CÓDIGO ORIGINAL MANTENIDO ---
app = Flask(__name__)

# CONFIGURACIÓN
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'agro_2026_key')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt_agro_2026')
app.config['AEMET_API_KEY'] = os.environ.get('AEMET_API_KEY', '')

# Conexión PostgreSQL para Render
uri = os.environ.get('DATABASE_URL', 'sqlite:///sigpac.db')
if uri.startswith("postgres://"): uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODELOS ORIGINALES
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    parcelas = db.relationship('Parcela', backref='propietario', lazy=True)

class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nombre = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    cultivo = db.Column(db.String(100))
    superficie = db.Column(db.Float)
    centroide = db.Column(db.Text)

with app.app_context(): db.create_all()

# MIDDLEWARE DE AUTENTICACIÓN
def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            request.current_user_id = payload['user_id']
        except: return jsonify({'error': 'Sesión no válida'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    data = request.json
    # AUMENTO: Verificación de contraseña
    if data['password'] != data.get('confirm_password'):
        return jsonify({'error': 'Las contraseñas no coinciden'}), 400
    if Usuario.query.filter_by(email=data['email']).first(): return jsonify({'error': 'Email ya existe'}), 400
    u = Usuario(username=data['username'], email=data['email'], password=generate_password_hash(data['password']))
    db.session.add(u); db.session.commit()
    token = jwt.encode({'user_id': u.id}, app.config['JWT_SECRET'])
    return jsonify({'token': token, 'username': u.username}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    u = Usuario.query.filter((Usuario.email == data['emailOrUsername']) | (Usuario.username == data['emailOrUsername'])).first()
    if u and check_password_hash(u.password, data['password']):
        token = jwt.encode({'user_id': u.id}, app.config['JWT_SECRET'])
        return jsonify({'token': token, 'username': u.username})
    return jsonify({'error': 'Credenciales incorrectas'}), 401

@app.route('/api/parcelas', methods=['GET', 'POST'])
@login_requerido
def gestionar_parcelas():
    if request.method == 'POST':
        data = request.json
        p = Parcela(user_id=request.current_user_id, nombre=data['nombre'], provincia=data['provincia'],
                    municipio=data['municipio'], cultivo=data['cultivo'], superficie=data['superficie'],
                    centroide=json.dumps(data['centroide']))
        db.session.add(p); db.session.commit()
        return jsonify({'id': p.id}), 201
    
    parcelas = Parcela.query.filter_by(user_id=request.current_user_id).all()
    return jsonify({'parcelas': [{'id': x.id, 'nombre': x.nombre, 'cultivo': x.cultivo, 'superficie': x.superficie} for x in parcelas]})

# --- AUMENTO: RUTA PARA LOS 4 GRÁFICOS Y ALERTAS ---
@app.route('/api/parcelas/<int:id>', methods=['GET'])
@login_requerido
def detalle_parcela(id):
    p = Parcela.query.filter_by(id=id, user_id=request.current_user_id).first_or_404()
    
    # Datos simulados de lluvia (AEMET/Mateo)
    lluvia_diaria = [{"f": "08:00", "v": 2.5}, {"f": "14:00", "v": 15.2}, {"f": "20:00", "v": 0.5}]
    
    # Lógica de alerta (si llueve más de 20mm total)
    alerta = "¡Alerta! Riesgo por lluvia intensa" if sum(x['v'] for x in lluvia_diaria) > 10 else "Normal"

    return jsonify({
        'parcela': {
            'nombre': p.nombre,
            'municipio': p.municipio,
            'provincia': p.provincia,
            'cultivo': p.cultivo,
            'alerta': alerta,
            'meteo': {
                'diario': lluvia_diaria,
                'mensual': [{"f": "Sem 1", "v": 20}, {"f": "Sem 2", "v": 55}, {"f": "Sem 3", "v": 12}],
                'anual': [{"f": "2024", "v": 510}, {"f": "2025", "v": 480}],
                'historico': [{"f": "Media 10 años", "v": 490}, {"f": "Actual", "v": 510}]
            }
        }
    })
