from flask import Blueprint, request, jsonify
from models.usuario import Usuario, XP_POR_ACCION

usuario_bp = Blueprint("usuario", __name__, url_prefix="/api/usuario")

@usuario_bp.route("/", methods=["POST"])
def crear_usuario():
    data = request.get_json()
    usuario_id = Usuario.crear(data["nombre"])
    return jsonify({
        "mensaje": "Usuario creado.",
        "id": usuario_id
    }), 201

@usuario_bp.route("/", methods=["GET"])
def get_usuario():
    usuario = Usuario.obtener()
    if not usuario:
        return jsonify({"mensaje": "No hay usuario creado."}), 404
    return jsonify(usuario)

@usuario_bp.route("/status", methods=["GET"])
def status_screen():
    status = Usuario.status_screen()
    if not status:
        return jsonify({"mensaje": "No hay usuario creado."}), 404
    return jsonify(status)

@usuario_bp.route("/xp", methods=["POST"])
def ganar_xp():
    data = request.get_json()
    resultado = Usuario.ganar_xp(
        data["stat_tipo"],
        data["xp"],
        data.get("motivo", "")
    )
    return jsonify(resultado)

@usuario_bp.route("/xp/acciones", methods=["GET"])
def get_acciones_xp():
    return jsonify(XP_POR_ACCION)