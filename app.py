from flask import Flask, render_template
from database import init_db
from routes.finanzas import finanzas_bp
from routes.ejercicios import ejercicios_bp
from routes.habitos import habitos_bp
from routes.castigos import castigos_bp
from routes.usuario import usuario_bp
from models.habitos import Habito

app = Flask(__name__)
app.register_blueprint(finanzas_bp)
app.register_blueprint(ejercicios_bp)
app.register_blueprint(habitos_bp)
app.register_blueprint(castigos_bp)
app.register_blueprint(usuario_bp)

@app.route("/")
@app.route("/status")
def index():
    return render_template("status.html")

@app.route("/habitos")
def habitos():
    return render_template("habitos.html")

@app.route("/entrenamiento")
def entrenamiento():
    return render_template("entrenamiento.html")

@app.route("/finanzas")
def finanzas():
    return render_template("finanzas.html")

if __name__ == "__main__":
    init_db()
    Habito.inicializar_habitos()
    app.run(debug=True)