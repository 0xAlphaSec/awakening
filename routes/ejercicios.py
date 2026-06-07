from flask import Blueprint, request, jsonify
from models.ejercicios import Ejercicio, Rutina, Sesion
from database import get_connection

ejercicios_bp = Blueprint("ejercicios", __name__, url_prefix="/api/ejercicios")

# ── EJERCICIOS ───────────────────────────────────────────

@ejercicios_bp.route("/catalogo", methods=["GET"])
def get_ejercicios():
    ejercicios = Ejercicio.obtener_todos()
    return jsonify([dict(e) for e in ejercicios])

@ejercicios_bp.route("/catalogo", methods=["POST"])
def add_ejercicio():
    data = request.get_json()
    Ejercicio.agregar(
        data["nombre"],
        data.get("grupo_muscular"),
        data.get("equipo_default")
    )
    return jsonify({"mensaje": "Ejercicio añadido."}), 201

# ── RUTINAS ──────────────────────────────────────────────

@ejercicios_bp.route("/rutinas", methods=["GET"])
def get_rutinas():
    rutinas = Rutina.obtener_todas()
    return jsonify([dict(r) for r in rutinas])

@ejercicios_bp.route("/rutinas", methods=["POST"])
def add_rutina():
    data = request.get_json()
    Rutina.agregar(
        data["nombre"],
        data["dia_semana"],
        data.get("descripcion")
    )
    return jsonify({"mensaje": "Rutina añadida."}), 201

@ejercicios_bp.route("/rutinas/<dia>", methods=["GET"])
def get_rutina_dia(dia):
    rutina = Rutina.obtener_por_dia(dia)
    if not rutina:
        return jsonify({"mensaje": "No hay rutina para este dia."}), 404
    ejercicios = Rutina.obtener_ejercicios(rutina["id"])
    return jsonify({
        "rutina": dict(rutina),
        "ejercicios": [dict(e) for e in ejercicios]
    })

@ejercicios_bp.route("/rutinas/<int:rutina_id>/ejercicios", methods=["POST"])
def add_ejercicio_rutina(rutina_id):
    data = request.get_json()
    Rutina.agregar_ejercicio(
        rutina_id,
        data["ejercicio_id"],
        data.get("series"),
        data.get("reps_objetivo")
    )
    return jsonify({"mensaje": "Ejercicio añadido a la rutina."}), 201

# ── SESIONES ─────────────────────────────────────────────

@ejercicios_bp.route("/sesiones", methods=["GET"])
def get_sesiones():
    sesiones = Sesion.obtener_todas()
    return jsonify([dict(s) for s in sesiones])

@ejercicios_bp.route("/sesiones", methods=["POST"])
def iniciar_sesion():
    data = request.get_json()
    sesion_id = Sesion.iniciar(
        data.get("rutina_id"),
        data.get("notas")
    )
    return jsonify({
        "mensaje": "Sesion iniciada.",
        "sesion_id": sesion_id
    }), 201

@ejercicios_bp.route("/sesiones/<int:sesion_id>/sets", methods=["POST"])
def add_set(sesion_id):
    data = request.get_json()
    Sesion.agregar_set(
        sesion_id,
        data["ejercicio_id"],
        data["serie_num"],
        data["reps"],
        data.get("peso_kg"),
        data.get("equipo")
    )
    return jsonify({"mensaje": "Set registrado."}), 201

@ejercicios_bp.route("/sesiones/<int:sesion_id>/sets", methods=["GET"])
def get_sets(sesion_id):
    sets = Sesion.obtener_sets(sesion_id)
    return jsonify([dict(s) for s in sets])

@ejercicios_bp.route("/sesiones/<int:sesion_id>/cerrar", methods=["POST"])
def cerrar_sesion(sesion_id):
    data = request.get_json()
    Sesion.cerrar(sesion_id, data["duracion_min"])
    return jsonify({"mensaje": "Sesion cerrada."}), 200

@ejercicios_bp.route("/progresion/<int:ejercicio_id>", methods=["GET"])
def get_progresion(ejercicio_id):
    historial = Sesion.progresion(ejercicio_id)
    return jsonify([dict(h) for h in historial])

# ── EDITAR Y ELIMINAR ─────────────────────────────────────

@ejercicios_bp.route("/catalogo/<int:ejercicio_id>", methods=["DELETE"])
def delete_ejercicio(ejercicio_id):
    conn = get_connection()
    conn.execute("DELETE FROM ejercicios_cat WHERE id = ?", (ejercicio_id,))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Ejercicio eliminado."})

@ejercicios_bp.route("/catalogo/<int:ejercicio_id>", methods=["PUT"])
def edit_ejercicio(ejercicio_id):
    data = request.get_json()
    conn = get_connection()
    conn.execute(
        """UPDATE ejercicios_cat
           SET nombre = ?, grupo_muscular = ?, equipo_default = ?
           WHERE id = ?""",
        (data["nombre"], data.get("grupo_muscular"), data.get("equipo_default"), ejercicio_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Ejercicio actualizado."})

@ejercicios_bp.route("/rutinas/<int:rutina_id>", methods=["DELETE"])
def delete_rutina(rutina_id):
    conn = get_connection()
    conn.execute("DELETE FROM rutina_ejercicios WHERE rutina_id = ?", (rutina_id,))
    conn.execute("DELETE FROM rutinas WHERE id = ?", (rutina_id,))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Rutina eliminada."})

@ejercicios_bp.route("/rutinas/<int:rutina_id>", methods=["PUT"])
def edit_rutina(rutina_id):
    data = request.get_json()
    conn = get_connection()
    conn.execute(
        """UPDATE rutinas SET nombre = ?, dia_semana = ?, descripcion = ?
           WHERE id = ?""",
        (data["nombre"], data["dia_semana"], data.get("descripcion"), rutina_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Rutina actualizada."})

@ejercicios_bp.route("/rutinas/<int:rutina_id>/ejercicios/<int:ejercicio_id>", methods=["DELETE"])
def delete_ejercicio_rutina(rutina_id, ejercicio_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM rutina_ejercicios WHERE rutina_id = ? AND ejercicio_id = ?",
        (rutina_id, ejercicio_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Ejercicio eliminado de la rutina."})