from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text # Para arreglar la base de datos
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, jwt
from functools import wraps

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'agro_secret_2026')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt_agro_key')
uri = os.environ.get('DATABASE_URL', 'sqlite:///sigpac.db')
if uri.startswith("postgres://"): uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS ---
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
    geometria = db.Column(db.Text) # Esta es la columna que falta en tu Render

# --- AUTO-CORRECCIÓN DE BASE DE DATOS ---
with app.app_context():
    db.create_all()
    # Este bloque detecta si falta la columna y la añade por ti:
    try:
        db.session.execute(text('ALTER TABLE parcela ADD COLUMN geometria TEXT'))
        db.session.commit()
        print("Columna 'geometria' añadida con éxito.")
    except Exception as e:
        db.session.rollback()
        print("La columna ya existía o hubo un error menor:", e)

# --- RUTAS PWA ---
@app.route('/manifest.json')
def serve_manifest(): return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def serve_sw(): return send_from_directory('static', 'service-worker.js')

# --- AUTH MIDDLEWARE ---
def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            request.current_user_id = payload['user_id']
        except: return jsonify({'error': 'Sesión caducada'}), 401
        return f(*args, **kwargs)
    return decorated

# --- RUTAS API ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    data = request.json
    if data.get('password') != data.get('confirm_password'):
        return jsonify({'error': 'Las contraseñas no coinciden'}), 400
    u = Usuario(username=data['username'], email=data['email'], 
                password=generate_password_hash(data['password']))
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
        p = Parcela(user_id=request.current_user_id, nombre=data['nombre'], 
                    provincia=data['provincia'], municipio=data['municipio'], 
                    cultivo=data['cultivo'], superficie=data['superficie'],
                    geometria=json.dumps(data['geometria']))
        db.session.add(p); db.session.commit()
        return jsonify({'id': p.id}), 201
    
    parcelas = Parcela.query.filter_by(user_id=request.current_user_id).all()
    return jsonify({'parcelas': [{'id': x.id, 'nombre': x.nombre, 'provincia': x.provincia} for x in parcelas]})

@app.route('/api/parcelas/<int:id>/datos_completos', methods=['GET'])
@login_requerido
def datos_completos(id):
    p = Parcela.query.get_or_404(id)
    return jsonify({
        "parcela": p.nombre,
        "data": {
            "info_sigpac": {"provincia": p.provincia, "municipio": p.municipio, "cultivo": p.cultivo},
            "graficos": {
                "diario": [{"f": "08h", "v": 2}, {"f": "14h", "v": 15}, {"f": "20h", "v": 5}],
                "mensual": [{"f": "Sem 1", "v": 20}, {"f": "Sem 2", "v": 55}, {"f": "Sem 3", "v": 15}],
                "anual": [{"f": "2024", "v": 510}, {"f": "2025", "v": 480}],
                "historico": [{"f": "Media", "v": 490}, {"f": "Actual", "v": 480}]
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
