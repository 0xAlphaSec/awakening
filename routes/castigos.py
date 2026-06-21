from flask import Blueprint, request, jsonify
from models.castigos import Castigo
from models.habitos import Habito

castigos_bp = Blueprint("castigos", __name__, url_prefix="/api/castigos")

@castigos_bp.route("/pendientes/<int:usuario_id>", methods=["GET"])
def get_castigos_pendientes(usuario_id):
    # Antes de devolver los pendientes, comprobamos si ya toca revisar el
    # día anterior. Si hay hábitos fallados y aún no se revisó hoy, se
    # asignan automáticamente aquí. Es idempotente: si ya se revisó hoy,
    # no hace nada.
    Castigo.verificar_y_asignar_si_corresponde(usuario_id)
    castigos = Castigo.obtener_castigos_pendientes(usuario_id)
    return jsonify([dict(c) for c in castigos])

@castigos_bp.route("/asignar/<int:usuario_id>", methods=["POST"])
def asignar_castigos(usuario_id):
    """
    Detecta fallos de ayer y asigna castigos aleatorios.
    Requiere el nivel actual del usuario en el body.
    """
    data = request.get_json()
    nivel = data.get("nivel", 1)
    fallos = Habito.obtener_fallos_ayer()

    if not fallos:
        return jsonify({"mensaje": "Sin fallos ayer. Sin castigos.", "castigos": []})

    castigos = Castigo.asignar_castigos(usuario_id, fallos, nivel)
    return jsonify({
        "mensaje": f"{len(castigos)} castigo(s) asignado(s).",
        "castigos": castigos
    }), 201

@castigos_bp.route("/completar/<int:castigo_id>", methods=["POST"])
def completar_castigo(castigo_id):
    Castigo.completar_castigo(castigo_id)
    return jsonify({"mensaje": "Castigo completado. Bien hecho."})

@castigos_bp.route("/historial/<int:usuario_id>", methods=["GET"])
def get_historial(usuario_id):
    historial = Castigo.obtener_historial(usuario_id)
    return jsonify([dict(h) for h in historial])
