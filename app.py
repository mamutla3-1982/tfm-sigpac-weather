from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, jwt
from functools import wraps

app = Flask(__name__)

# --- CONFIGURACIÓN ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'agro_2026_secret')
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'jwt_agro_2026')
uri = os.environ.get('DATABASE_URL', 'sqlite:///sigpac.db')
if uri.startswith("postgres://"): uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (Mantenidos) ---
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
    geometria = db.Column(db.Text)

# --- PARCHE DE MIGRACIÓN AUTOMÁTICA ---
with app.app_context():
    db.create_all()
    try:
        # Esto soluciona el error "column geometria does not exist" sin borrar usuarios
        db.session.execute(text('ALTER TABLE parcela ADD COLUMN geometria TEXT'))
        db.session.commit()
        print("MIGRACIÓN: Columna 'geometria' añadida.")
    except Exception as e:
        db.session.rollback()
        print("MIGRACIÓN: La columna ya existe o la DB es SQLite.")

# --- MIDDLEWARE ---
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

# --- RUTAS PWA ---
@app.route('/manifest.json')
def serve_manifest(): return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def serve_sw(): return send_from_directory('static', 'service-worker.js')

# --- RUTAS API ---
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/auth/registro', methods=['POST'])
def registro():
    data = request.json
    if data['password'] != data.get('confirm_password'):
        return jsonify({'error': 'Las contraseñas no coinciden'}), 400
    u = Usuario(username=data['username'], email=data['email'], 
                password=generate_password_hash(data['password']))
    db.session.add(u); db.session.commit()
    return jsonify({'token': jwt.encode({'user_id': u.id}, app.config['JWT_SECRET']), 'username': u.username}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    u = Usuario.query.filter((Usuario.email == data['emailOrUsername']) | (Usuario.username == data['emailOrUsername'])).first()
    if u and check_password_hash(u.password, data['password']):
        return jsonify({'token': jwt.encode({'user_id': u.id}, app.config['JWT_SECRET']), 'username': u.username})
    return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/api/parcelas', methods=['GET', 'POST'])
@login_requerido
def gestionar_parcelas():
    if request.method == 'POST':
        data = request.json
        p = Parcela(user_id=request.current_user_id, nombre=data['nombre'], provincia=data['provincia'],
                    municipio=data['municipio'], cultivo=data['cultivo'], superficie=data['superficie'],
                    geometria=json.dumps(data['geometria']))
        db.session.add(p); db.session.commit()
        return jsonify({'id': p.id}), 201
    
    parcelas = Parcela.query.filter_by(user_id=request.current_user_id).all()
    return jsonify({'parcelas': [{'id': x.id, 'nombre': x.nombre} for x in parcelas]})

@app.route('/api/parcelas/<int:id>/datos_completos', methods=['GET'])
@login_requerido
def datos_completos(id):
    p = Parcela.query.get_or_404(id)
    return jsonify({
        "parcela": p.nombre,
        "data": {
            "info_sigpac": {"provincia": p.provincia, "municipio": p.municipio, "cultivo": p.cultivo},
            "graficos": {
                "diario": [{"f": "08h", "v": 1.5}, {"f": "20h", "v": 4.2}],
                "mensual": [{"f": "Sem 1", "v": 15}, {"f": "Sem 2", "v": 30}],
                "anual": [{"f": "2025", "v": 450}, {"f": "2026", "v": 120}],
                "historico": [{"f": "Media", "v": 480}, {"f": "Actual", "v": 450}]
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
