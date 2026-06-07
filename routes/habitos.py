from flask import Blueprint, request, jsonify
from models.habitos import Habito
from database import get_connection

habitos_bp = Blueprint("habitos", __name__, url_prefix="/api/habitos")

# ── CATALOGO ─────────────────────────────────────────────

@habitos_bp.route("/", methods=["GET"])
def get_habitos():
    habitos = Habito.obtener_todos()
    return jsonify([dict(h) for h in habitos])

@habitos_bp.route("/hoy", methods=["GET"])
def get_habitos_hoy():
    habitos = Habito.obtener_habitos_hoy()
    return jsonify(habitos)

# ── REGISTRO ─────────────────────────────────────────────

@habitos_bp.route("/registrar", methods=["POST"])
def registrar_habito():
    data = request.get_json()
    Habito.registrar(
        data["habito_id"],
        data["completado"],
        data.get("valor")
    )
    return jsonify({"mensaje": "Habito registrado."}), 201

@habitos_bp.route("/hoy/registro", methods=["GET"])
def get_registro_hoy():
    registros = Habito.obtener_registro_hoy()
    return jsonify([dict(r) for r in registros])

# ── ZONA DE CASTIGO ───────────────────────────────────────

@habitos_bp.route("/fallos/ayer", methods=["GET"])
def get_fallos_ayer():
    fallos = Habito.obtener_fallos_ayer()
    return jsonify({
        "fallos": fallos,
        "total": len(fallos)
    })

# ── RACHA ─────────────────────────────────────────────────

@habitos_bp.route("/racha/<int:habito_id>", methods=["GET"])
def get_racha(habito_id):
    racha = Habito.racha(habito_id)
    return jsonify({
        "habito_id": habito_id,
        "racha_dias": racha
    })

# ── EDITAR Y ELIMINAR ─────────────────────────────────────

@habitos_bp.route("/<int:habito_id>", methods=["PUT"])
def edit_habito(habito_id):
    data = request.get_json()
    import json
    conn = get_connection()
    conn.execute(
        """UPDATE habitos_cat
           SET nombre = ?, stat_asociado = ?, tipo = ?, dias_semana = ?, es_diario = ?
           WHERE id = ?""",
        (
            data["nombre"],
            data["stat_asociado"],
            data["tipo"],
            json.dumps(data["dias_semana"]) if data.get("dias_semana") else None,
            data.get("es_diario", 0),
            habito_id
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Habito actualizado."})

@habitos_bp.route("/<int:habito_id>", methods=["DELETE"])
def delete_habito(habito_id):
    conn = get_connection()
    conn.execute("DELETE FROM habitos_cat WHERE id = ?", (habito_id,))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Habito eliminado."})

@habitos_bp.route("/", methods=["POST"])
def add_habito():
    data = request.get_json()
    import json
    conn = get_connection()
    conn.execute(
        """INSERT INTO habitos_cat (nombre, stat_asociado, tipo, dias_semana, es_diario)
           VALUES (?, ?, ?, ?, ?)""",
        (
            data["nombre"],
            data["stat_asociado"],
            data["tipo"],
            json.dumps(data["dias_semana"]) if data.get("dias_semana") else None,
            data.get("es_diario", 0)
        )
    )
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Habito creado."}), 201