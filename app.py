from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy  # CAMBIO: SQLAlchemy en lugar de PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import jwt
import requests
from functools import wraps
import json

app = Flask(__name__)

# ── CONFIGURACIÓN ──
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sigpac_weather_2026_secret')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt_secret_2026')
app.config['AEMET_API_KEY'] = os.environ.get('AEMET_API_KEY', '')

# CAMBIO: Configuración para PostgreSQL (Render)
uri = os.environ.get('DATABASE_URL', 'sqlite:///sigpac.db')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ── MODELOS DE BASE DE DATOS (NUEVO) ──
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nombre = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    superficie = db.Column(db.Float, default=0.0)
    coordenadas = db.Column(db.Text) # Guardamos JSON como texto
    centroide = db.Column(db.Text)    # Guardamos JSON como texto
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Crear las tablas automáticamente
with app.app_context():
    db.create_all()

# ── FUNCIONES JWT (IGUAL QUE ANTES) ──
def crear_token(user_id):
    payload = {
        'user_id': int(user_id), # Aseguramos que sea entero para SQL
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, app.config['JWT_SECRET'], algorithm='HS256')

def verificar_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

def login_requerido(f):
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

# ── RUTAS ESTÁTICAS Y HTML (IGUAL) ──
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return render_template('index.html')

# ── API AUTENTICACIÓN (MODIFICADA PARA SQL) ──
@app.route('/api/auth/registro', methods=['POST'])
def registro():
    data = request.json
    required = ['username', 'nombre', 'email', 'password', 'passwordConfirm']
    if not all(k in data for k in required):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
    
    if data['password'] != data['passwordConfirm']:
        return jsonify({'error': 'Las contraseñas no coinciden'}), 400
    
    # CAMBIO: Consulta SQL
    if Usuario.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Ya existe una cuenta con ese email'}), 400
    
    if Usuario.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Ese nombre de usuario ya está en uso'}), 400
    
    nuevo_usuario = Usuario(
        username=data['username'],
        nombre=data['nombre'],
        email=data['email'].lower(),
        password=generate_password_hash(data['password'])
    )
    
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    token = crear_token(nuevo_usuario.id)
    return jsonify({
        'token': token,
        'usuario': {
            'id': nuevo_usuario.id,
            'username': nuevo_usuario.username,
            'nombre': nuevo_usuario.nombre,
            'email': nuevo_usuario.email
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    # CAMBIO: Búsqueda con SQLAlchemy
    login_id = data.get('emailOrUsername', '').lower()
    usuario = Usuario.query.filter((Usuario.email == login_id) | (Usuario.username == data.get('emailOrUsername'))).first()
    
    if not usuario or not check_password_hash(usuario.password, data.get('password', '')):
        return jsonify({'error': 'Email/Usuario o contraseña incorrectos'}), 401
    
    token = crear_token(usuario.id)
    return jsonify({
        'token': token,
        'usuario': {
            'id': usuario.id,
            'username': usuario.username,
            'nombre': usuario.nombre,
            'email': usuario.email
        }
    })

@app.route('/api/auth/perfil')
@login_requerido
def perfil():
    usuario = Usuario.query.get(request.current_user_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'usuario': {
            'id': usuario.id,
            'username': usuario.username,
            'nombre': usuario.nombre,
            'email': usuario.email
        }
    })

# ── API PARCELAS (MODIFICADA PARA SQL) ──
@app.route('/api/parcelas', methods=['GET'])
@login_requerido
def obtener_parcelas():
    # CAMBIO: Consulta SQL filtrada por usuario
    parcelas_db = Parcela.query.filter_by(user_id=request.current_user_id).all()
    
    parcelas = []
    for p in parcelas_db:
        parcelas.append({
            'id': p.id,
            'nombre': p.nombre,
            'provincia': p.provincia,
            'municipio': p.municipio,
            'poligono': p.poligono,
            'parcela_num': p.parcela_num,
            'cultivo': p.cultivo,
            'superficie': p.superficie,
            'coordenadas': json.loads(p.coordenadas) if p.coordenadas else None,
            'centroide': json.loads(p.centroide) if p.centroide
