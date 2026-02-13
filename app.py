from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS
from database import SessionLocal, Usuario, Parcela, init_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)

init_db()


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = SessionLocal()
        username = request.form["username"]
        password = request.form["password"]

        user = db.query(Usuario).filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("index"))
        return "Usuario o contraseña incorrectos"

    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        db = SessionLocal()
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        nuevo = Usuario(username=username, email=email, password_hash=password)
        db.add(nuevo)
        db.commit()

        return redirect(url_for("login"))

    return render_template("registro.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/parcelas")
def api_parcelas():
    db = SessionLocal()
    parcelas = db.query(Parcela).all()
    return {"parcelas": [p.nombre for p in parcelas]}


if __name__ == "__main__":
    app.run(debug=True)
