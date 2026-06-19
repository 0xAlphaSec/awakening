from flask import Blueprint, request, jsonify
from models.finanzas import Finanzas

finanzas_bp = Blueprint("finanzas", __name__, url_prefix="/api/finanzas")

# ── GASTOS FIJOS ─────────────────────────────────────────

@finanzas_bp.route("/gastos-fijos", methods=["GET"])
def get_gastos_fijos():
    gastos = Finanzas.obtener_gastos_fijos()
    return jsonify([dict(g) for g in gastos])

@finanzas_bp.route("/gastos-fijos", methods=["POST"])
def add_gasto_fijo():
    data = request.get_json()
    Finanzas.agregar_gasto_fijo(data["concepto"], data["monto"])
    return jsonify({"mensaje": "Gasto fijo añadido correctamente."}), 201

@finanzas_bp.route("/gastos-fijos/<int:gasto_id>", methods=["DELETE"])
def delete_gasto_fijo(gasto_id):
    Finanzas.eliminar_gasto_fijo(gasto_id)
    return jsonify({"mensaje": "Gasto fijo eliminado."})

# ── SUELDO ───────────────────────────────────────────────

@finanzas_bp.route("/sueldo", methods=["POST"])
def registrar_sueldo():
    data = request.get_json()
    disponible = Finanzas.registrar_sueldo(data["sueldo_neto"], data["porcentajes"])
    distribucion = Finanzas.calcular_distribucion(disponible, data["porcentajes"])
    return jsonify({
        "disponible_real": disponible,
        "distribucion": distribucion
    }), 201

@finanzas_bp.route("/sueldo", methods=["GET"])
def get_historial_sueldos():
    historial = Finanzas.obtener_historial_sueldos()
    return jsonify([dict(h) for h in historial])

# ── COLCHÓN ───────────────────────────────────────────────

@finanzas_bp.route("/colchon", methods=["GET"])
def get_colchon():
    colchon = Finanzas.obtener_colchon()
    if not colchon:
        return jsonify({"mensaje": "Colchon no inicializado."}), 404
    return jsonify(dict(colchon))

@finanzas_bp.route("/colchon/inicializar", methods=["POST"])
def inicializar_colchon():
    data = request.get_json()
    Finanzas.inicializar_colchon(data["gastos_esenciales_mes"])
    return jsonify({"mensaje": "Colchon inicializado correctamente."}), 201

@finanzas_bp.route("/colchon/actualizar", methods=["POST"])
def actualizar_colchon():
    data = request.get_json()
    resultado = Finanzas.actualizar_colchon(data["monto"])
    if resultado["completado"]:
        return jsonify({
            "mensaje": "Colchon completado! A partir de ahora el ahorro va a Trade Republic.",
            "acumulado": resultado["acumulado"],
            "completado": True
        })
    return jsonify({
        "mensaje": "Colchon actualizado.",
        "acumulado": resultado["acumulado"],
        "completado": False
    })

# ── TRANSACCIONES ─────────────────────────────────────────

@finanzas_bp.route("/transacciones", methods=["GET"])
def get_transacciones():
    mes = request.args.get("mes")
    transacciones = Finanzas.obtener_transacciones(mes)
    return jsonify([dict(t) for t in transacciones])

@finanzas_bp.route("/transacciones", methods=["POST"])
def add_transaccion():
    data = request.get_json()
    Finanzas.registrar_transaccion(
        data["categoria"],
        data["monto"],
        data["tipo"],
        data.get("concepto")
    )
    return jsonify({"mensaje": "Transaccion registrada."}), 201

# ── ETF ───────────────────────────────────────────────────

@finanzas_bp.route("/etf", methods=["GET"])
def get_etf():
    resumen = Finanzas.obtener_resumen_etf()
    return jsonify([dict(e) for e in resumen])

@finanzas_bp.route("/etf", methods=["POST"])
def registrar_etf():
    data = request.get_json()
    total = Finanzas.registrar_aportacion_etf(data["aportacion"])
    return jsonify({
        "mensaje": "Aportacion ETF registrada.",
        "total_acumulado": total
    }), 201

# ── GASTOS PERSONALES ─────────────────────────────────────

@finanzas_bp.route("/gastos-personales", methods=["GET"])
def get_gastos_personales():
    gastos = Finanzas.obtener_gastos_personales()
    return jsonify([dict(g) for g in gastos])

@finanzas_bp.route("/gastos-personales", methods=["POST"])
def add_gasto_personal():
    data = request.get_json()
    Finanzas.agregar_gasto_personal(data["nombre"], data["monto_estimado"])
    return jsonify({"mensaje": "Gasto personal añadido."}), 201

@finanzas_bp.route("/gastos-personales/<int:gasto_id>", methods=["DELETE"])
def delete_gasto_personal(gasto_id):
    Finanzas.eliminar_gasto_personal(gasto_id)
    return jsonify({"mensaje": "Gasto personal eliminado."})
