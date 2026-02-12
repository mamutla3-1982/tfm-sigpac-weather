from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import SessionLocal, Usuario, Parcela, init_db
from flask_cors import CORS
import jwt
import datetime
import os

app = Flask(__name__)
CORS(app)

# Clave secreta para JWT
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambia_esto_por_una_clave_segura")

# Inicializar base de datos (crea tablas si no existen)
init_db()


# ------------------ JWT ------------------

def crear_token(usuario):
    payload = {
        "user_id": usuario.id,
        "username": usuario.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def verificar_token(token):
    try:
        return jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    except:
        return None


def usuario_desde_header():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ")[1]
    return verificar_token(token)


# ------------------ RUTA PRINCIPAL ------------------

@app.route("/")
def index():
    return render_template("index.html")


# ------------------ AUTH ------------------

@app.route("/api/auth/registro", methods=["POST"])
def registro():
    db = SessionLocal()
    data = request.get_json()

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Faltan datos"}), 400

    # Comprobar si existe usuario
    if db.query(Usuario).filter((Usuario.username == username) | (Usuario.email == email)).first():
        return jsonify({"error": "Usuario o email ya existe"}), 400

    user = Usuario(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )

    db.add(user)
    db.commit()

    token = crear_token(user)
    return jsonify({"token": token, "username": username})


@app.route("/api/auth/login", methods=["POST"])
def login():
    db = SessionLocal()
    data = request.get_json()

    emailOrUsername = data.get("emailOrUsername")
    password = data.get("password")

    user = db.query(Usuario).filter(
        (Usuario.username == emailOrUsername) |
        (Usuario.email == emailOrUsername)
    ).first()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 400

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Contraseña incorrecta"}), 400

    token = crear_token(user)
    return jsonify({"token": token, "username": user.username})


# ------------------ PARCELAS ------------------

@app.route("/api/parcelas", methods=["GET"])
def listar_parcelas():
    db = SessionLocal()
    user = usuario_desde_header()

    if not user:
        return jsonify({"error": "No autorizado"}), 401

    parcelas = db.query(Parcela).filter(Parcela.user_id == user["user_id"]).all()

    return jsonify({
        "parcelas": [
            {
                "id": p.id,
                "nombre": p.nombre,
                "provincia": p.provincia,
                "municipio": p.municipio,
                "cultivo": p.cultivo,
                "superficie": p.superficie
            }
            for p in parcelas
        ]
    })


@app.route("/api/parcelas", methods=["POST"])
def crear_parcela():
    db = SessionLocal()
    user = usuario_desde_header()

    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()

    parcela = Parcela(
        user_id=user["user_id"],
        nombre=data.get("nombre"),
        provincia=data.get("provincia"),
        municipio=data.get("municipio"),
        cultivo=data.get("cultivo"),
        superficie=data.get("superficie"),
        geometria=data.get("geometria")
    )

    db.add(parcela)
    db.commit()

    return jsonify({"ok": True})


@app.route("/api/parcelas/<int:id>", methods=["PUT"])
def editar_parcela(id):
    db = SessionLocal()
    user = usuario_desde_header()

    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()

    parcela = db.query(Parcela).filter(
        Parcela.id == id,
        Parcela.user_id == user["user_id"]
    ).first()

    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404

    parcela.nombre = data.get("nombre")
    db.commit()

    return jsonify({"ok": True})


@app.route("/api/parcelas/<int:id>", methods=["DELETE"])
def eliminar_parcela(id):
    db = SessionLocal()
    user = usuario_desde_header()

    if not user:
        return jsonify({"error": "No autorizado"}), 401

    parcela = db.query(Parcela).filter(
        Parcela.id == id,
        Parcela.user_id == user["user_id"]
    ).first()

    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404

    db.delete(parcela)
    db.commit()

    return jsonify({"ok": True})


@app.route("/api/parcelas/<int:id>/datos_completos", methods=["GET"])
def datos_completos(id):
    db = SessionLocal()
    user = usuario_desde_header()

    if not user:
        return jsonify({"error": "No autorizado"}), 401

    parcela = db.query(Parcela).filter(
        Parcela.id == id,
        Parcela.user_id == user["user_id"]
    ).first()

    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404

    # Datos simulados (puedes reemplazar por AEMET real)
    datos = {
        "info_sigpac": {
            "provincia": parcela.provincia,
            "municipio": parcela.municipio
        },
        "graficos": {
            "diario": [{"v": 0}, {"v": 2}, {"v": 5}]
        }
    }

    return jsonify({
        "parcela": parcela.nombre,
        "data": datos
    })


# ------------------ MAIN ------------------

if __name__ == "__main__":
    app.run(debug=True)
