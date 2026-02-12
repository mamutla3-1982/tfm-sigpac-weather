from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, requests
from datetime import datetime, timedelta
import jwt
from functools import wraps

app = Flask(__name__)

# ── CONFIGURACIÓN ──
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'agro_secret_2026')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt_agro_2026')
app.config['AEMET_API_KEY'] = os.environ.get('AEMET_API_KEY', '')

# Configuración PostgreSQL para Render
uri = os.environ.get('DATABASE_URL', 'sqlite:///sigpac.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── MODELOS DE DATOS ──
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    parcelas = db.relationship('Parcela', backref='propietario', lazy=True)

class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nombre = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    poligono = db.Column(db.String(50))
    parcela_num = db.Column(db.String(50))
    cultivo = db.Column(db.String(100))
    superficie = db.Column(db.Float)
    coordenadas = db.Column(db.Text)
    centroide = db.Column(db.Text)

with app.app_context():
    db.create_all()

# ── AUTENTICACIÓN ──
def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            request.current_user_id = payload['user_id']
        except:
            return jsonify({'error': 'Sesión expirada'}), 401
        return f(*args, **kwargs)
    return decorated

# ── RUTAS API ──
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    data = request.json
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'El email ya existe'}), 400
    u = Usuario(
        username=data['username'], nombre=data['nombre'], email=data['email'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(u); db.session.commit()
    token = jwt.encode({'user_id': u.id, 'exp': datetime.utcnow() + timedelta(days=7)}, app.config['JWT_SECRET'])
    return jsonify({'token': token}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    u = Usuario.query.filter((Usuario.email == data['emailOrUsername']) | (Usuario.username == data['emailOrUsername'])).first()
    if u and check_password_hash(u.password, data['password']):
        token = jwt.encode({'user_id': u.id, 'exp': datetime.utcnow() + timedelta(days=7)}, app.config['JWT_SECRET'])
        return jsonify({'token': token, 'username': u.username})
    return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/api/parcelas', methods=['GET', 'POST'])
@login_requerido
def gestionar_parcelas():
    if request.method == 'POST':
        data = request.json
        p = Parcela(
            user_id=request.current_user_id,
            nombre=data['nombre'], provincia=data.get('provincia'),
            municipio=data.get('municipio'), cultivo=data.get('cultivo'),
            superficie=data.get('superficie'),
            coordenadas=json.dumps(data.get('coordenadas')),
            centroide=json.dumps(data.get('centroide'))
        )
        db.session.add(p); db.session.commit()
        return jsonify({'id': p.id}), 201
    
    parcelas = Parcela.query.filter_by(user_id=request.current_user_id).all()
    return jsonify({'parcelas': [{
        'id': x.id, 'nombre': x.nombre, 'cultivo': x.cultivo, 
        'superficie': x.superficie, 'municipio': x.municipio
    } for x in parcelas]})

@app.route('/api/parcelas/<int:id>', methods=['GET'])
@login_requerido
def detalle_parcela(id):
    p = Parcela.query.get_or_404(id)
    # Aumento: Generador de datos para 4 gráficos (Diario, Mensual, Anual, Histórico)
    meteo = {
        "diario": [{"fecha": "08:00", "v": 0.2}, {"fecha": "12:00", "v": 1.5}, {"fecha": "18:00", "v": 0.8}],
        "mensual": [{"fecha": "Sem 1", "v": 20}, {"fecha": "Sem 2", "v": 15}, {"fecha": "Sem 3", "v": 35}],
        "anual": [{"fecha": "2024", "v": 520}, {"fecha": "2025", "v": 480}],
        "historico": [{"fecha": "Media 10 años", "v": 500}, {"fecha": "Actual", "v": 490}]
    }
    return jsonify({'parcela': {'nombre': p.nombre, 'cultivo': p.cultivo, 'meteo': meteo}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
