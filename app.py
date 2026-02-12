from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os, json, jwt, datetime
from config import Config

app = Flask(__name__, static_folder="static")
app.config.from_object(Config)

db = SQLAlchemy(app)

# -------------------------
# MODELOS
# -------------------------
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
    recinto = db.Column(db.String(20))
    superficie = db.Column(db.Float)
    geometria = db.Column(db.Text)

# -------------------------
# MIGRACIÓN SEGURA
# -------------------------
with app.app:
        cols = db.session.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='parcela';
        """))
        colnames = [c[0] for c in cols]

        if "geometria" not in colnames:
            db.session.execute(text("ALTER TABLE parcela ADD COLUMN geometria TEXT"))
            db.session.commit()

        if "recinto" not in colnames:
            db.session.execute(text("ALTER TABLE parcela ADD COLUMN recinto VARCHAR(20)"))
            db.session.commit()

    except Exception as e:
        print("Migración no necesaria:", str(e))
        db.session.rollback()

# -------------------------
# JWT
# -------------------------
def crear_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, app.config["JWT_SECRET"], algorithm="HS256")

def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token requerido"}), 401
        try:
            data = jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
            request.current_user_id = data["user_id"]
        except:
            return jsonify({"error": "Token inválido o expirado"}), 401
        return f(*args, **kwargs)
    return wrapper

# -------------------------
# RUTAS AUTH
# -------------------------

@app.route("/api/auth/register", methods=["POST"])
def registrar():
    data = request.json

    if Usuario.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "El email ya existe"}), 400

    if Usuario.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "El usuario ya existe"}), 400

    if data["password"] != data["confirm_password"]:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400

    u = Usuario(
        username=data["username"],
        email=data["email"],
        password=generate_password_hash(data["password"])
    )

    db.session.add(u)
    db.session.commit()

    return jsonify({
        "token": crear_token(u.id),
        "username": u.username
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    u = Usuario.query.filter(
        (Usuario.email == data["emailOrUsername"]) |
        (Usuario.username == data["emailOrUsername"])
    ).first()

    if u and check_password_hash(u.password, data["password"]):
        return jsonify({"token": crear_token(u.id), "username": u.username})

    return jsonify({"error": "Credenciales inválidas"}), 401


# -------------------------
# RUTAS PARCELAS
# -------------------------

@app.route("/api/parcelas", methods=["POST"])
@login_requerido
def guardar_parcela():
    data = request.json

    p = Parcela(
        user_id=request.current_user_id,
        nombre=data.get("nombre"),
        provincia=data.get("provincia"),
        municipio=data.get("municipio"),
        recinto=data.get("recinto"),
        superficie=data.get("superficie"),
        geometria=json.dumps(data.get("geometria"))
    )

    db.session.add(p)
    db.session.commit()

    return jsonify({"id": p.id}), 201


@app.route("/api/parcelas", methods=["GET"])
@login_requerido
def listar_parcelas():
    parcelas = Parcela.query.filter_by(user_id=request.current_user_id).all()

    return jsonify({
        "parcelas": [
            {
                "id": p.id,
                "nombre": p.nombre,
                "provincia": p.provincia,
                "municipio": p.municipio,
                "superficie": p.superficie
            }
            for p in parcelas
        ]
    })


@app.route("/api/parcelas/<int:pid>", methods=["GET"])
@login_requerido
def obtener_parcela(pid):
    p = Parcela.query.get_or_404(pid)

    if p.user_id != request.current_user_id:
        return jsonify({"error": "No autorizado"}), 403

    return jsonify({
        "id": p.id,
        "nombre": p.nombre,
        "provincia": p.provincia,
        "municipio": p.municipio,
        "recinto": p.recinto,
        "superficie": p.superficie,
        "geometria": json.loads(p.geometria)
    })


@app.route("/api/parcelas/<int:pid>/datos_completos", methods=["GET"])
@login_requerido
def datos_completos(pid):
    p = Parcela.query.get_or_404(pid)

    if p.user_id != request.current_user_id:
        return jsonify({"error": "No autorizado"}), 403

    return jsonify({
        "sigpac": {
            "provincia": p.provincia,
            "municipio": p.municipio,
            "recinto": p.recinto
        },
        "lluvia": {
            "diaria": [],
            "mensual": [],
            "anual": [],
            "historico": []
        }
    })


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run()
