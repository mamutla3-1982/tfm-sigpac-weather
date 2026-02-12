from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "cambia_esto_por_un_secreto_seguro"

# --- "Base de datos" en memoria (para ejemplo) ---
USUARIOS = {}          # email/username -> {id, username, email, password_hash}
PARCELAS = []          # lista de dicts con info de parcelas
NEXT_USER_ID = 1
NEXT_PARCELA_ID = 1


def crear_token(usuario_id, username):
    payload = {
        "user_id": usuario_id,
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def verificar_token(token):
    try:
        data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return data
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html")


# ========== AUTH ==========

@app.route("/api/auth/registro", methods=["POST"])
def registro():
    global NEXT_USER_ID
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    confirm = data.get("confirm_password")

    if not username or not email or not password:
        return jsonify({"error": "Faltan campos"}), 400
    if password != confirm:
        return jsonify({"error": "Las contraseñas no coinciden"}), 400
    if username in USUARIOS or email in USUARIOS:
        return jsonify({"error": "Usuario o email ya existe"}), 400

    password_hash = generate_password_hash(password)
    user_data = {
        "id": NEXT_USER_ID,
        "username": username,
        "email": email,
        "password_hash": password_hash
    }
    USUARIOS[username] = user_data
    USUARIOS[email] = user_data
    NEXT_USER_ID += 1

    token = crear_token(user_data["id"], username)
    return jsonify({"token": token, "username": username})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email_or_username = data.get("emailOrUsername")
    password = data.get("password")

    user = USUARIOS.get(email_or_username)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 400

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Contraseña incorrecta"}), 400

    token = crear_token(user["id"], user["username"])
    return jsonify({"token": token, "username": user["username"]})


def usuario_desde_header():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    return verificar_token(token)


# ========== PARCELAS ==========

@app.route("/api/parcelas", methods=["GET"])
def listar_parcelas():
    user = usuario_desde_header()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    user_id = user["user_id"]
    parcelas_user = [p for p in PARCELAS if p["user_id"] == user_id]
    return jsonify({"parcelas": parcelas_user})


@app.route("/api/parcelas", methods=["POST"])
def crear_parcela():
    global NEXT_PARCELA_ID
    user = usuario_desde_header()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    nombre = data.get("nombre")
    provincia = data.get("provincia")
    municipio = data.get("municipio")
    cultivo = data.get("cultivo")
    superficie = data.get("superficie")
    geometria = data.get("geometria")

    if not nombre or not geometria:
        return jsonify({"error": "Faltan datos"}), 400

    parcela = {
        "id": NEXT_PARCELA_ID,
        "user_id": user["user_id"],
        "nombre": nombre,
        "provincia": provincia,
        "municipio": municipio,
        "cultivo": cultivo,
        "superficie": superficie,
        "geometria": geometria
    }
    PARCELAS.append(parcela)
    NEXT_PARCELA_ID += 1

    return jsonify({"ok": True, "parcela": parcela})


@app.route("/api/parcelas/<int:parcela_id>", methods=["PUT"])
def editar_parcela(parcela_id):
    user = usuario_desde_header()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    nuevo_nombre = data.get("nombre")

    for p in PARCELAS:
        if p["id"] == parcela_id and p["user_id"] == user["user_id"]:
            if nuevo_nombre:
                p["nombre"] = nuevo_nombre
            return jsonify({"ok": True, "parcela": p})

    return jsonify({"error": "Parcela no encontrada"}), 404


@app.route("/api/parcelas/<int:parcela_id>", methods=["DELETE"])
def eliminar_parcela(parcela_id):
    user = usuario_desde_header()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    global PARCELAS
    antes = len(PARCELAS)
    PARCELAS = [p for p in PARCELAS if not (p["id"] == parcela_id and p["user_id"] == user["user_id"])]
    if len(PARCELAS) == antes:
        return jsonify({"error": "Parcela no encontrada"}), 404

    return jsonify({"ok": True})


@app.route("/api/parcelas/<int:parcela_id>/datos_completos", methods=["GET"])
def datos_completos(parcela_id):
    user = usuario_desde_header()
    if not user:
        return jsonify({"error": "No autorizado"}), 401

    parcela = None
    for p in PARCELAS:
        if p["id"] == parcela_id and p["user_id"] == user["user_id"]:
            parcela = p
            break

    if not parcela:
        return jsonify({"error": "Parcela no encontrada"}), 404

    # Simulación de datos de lluvia y SIGPAC
    datos = {
        "info_sigpac": {
            "provincia": parcela.get("provincia") or "Desconocida",
            "municipio": parcela.get("municipio") or "Desconocido"
        },
        "graficos": {
            "diario": [{"v": 0}, {"v": 2}, {"v": 5}, {"v": 0}, {"v": 1}]
        }
    }

    return jsonify({
        "parcela": parcela["nombre"],
        "data": datos
    })


if __name__ == "__main__":
    app.run(debug=True)
