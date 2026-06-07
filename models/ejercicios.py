from database import get_connection
from datetime import date

class Ejercicio:

    @staticmethod
    def agregar(nombre, grupo_muscular=None, equipo_default=None):
        conn = get_connection()
        conn.execute(
            "INSERT INTO ejercicios_cat (nombre, grupo_muscular, equipo_default) VALUES (?, ?, ?)",
            (nombre, grupo_muscular, equipo_default)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_todos():
        conn = get_connection()
        ejercicios = conn.execute(
            "SELECT * FROM ejercicios_cat ORDER BY nombre"
        ).fetchall()
        conn.close()
        return ejercicios

    @staticmethod
    def obtener_por_id(ejercicio_id):
        conn = get_connection()
        ejercicio = conn.execute(
            "SELECT * FROM ejercicios_cat WHERE id = ?",
            (ejercicio_id,)
        ).fetchone()
        conn.close()
        return ejercicio


class Rutina:

    @staticmethod
    def agregar(nombre, dia_semana, descripcion=None):
        conn = get_connection()
        conn.execute(
            "INSERT INTO rutinas (nombre, dia_semana, descripcion) VALUES (?, ?, ?)",
            (nombre, dia_semana, descripcion)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_todas():
        conn = get_connection()
        rutinas = conn.execute(
            "SELECT * FROM rutinas ORDER BY dia_semana"
        ).fetchall()
        conn.close()
        return rutinas

    @staticmethod
    def obtener_por_dia(dia):
        conn = get_connection()
        rutina = conn.execute(
            "SELECT * FROM rutinas WHERE dia_semana = ?",
            (dia,)
        ).fetchone()
        conn.close()
        return rutina

    @staticmethod
    def agregar_ejercicio(rutina_id, ejercicio_id, series=None, reps_objetivo=None):
        conn = get_connection()
        conn.execute(
            """INSERT INTO rutina_ejercicios (rutina_id, ejercicio_id, series, reps_objetivo)
               VALUES (?, ?, ?, ?)""",
            (rutina_id, ejercicio_id, series, reps_objetivo)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_ejercicios(rutina_id):
        conn = get_connection()
        ejercicios = conn.execute(
            """SELECT re.*, ec.nombre, ec.grupo_muscular, ec.equipo_default
               FROM rutina_ejercicios re
               JOIN ejercicios_cat ec ON re.ejercicio_id = ec.id
               WHERE re.rutina_id = ?""",
            (rutina_id,)
        ).fetchall()
        conn.close()
        return ejercicios


class Sesion:

    @staticmethod
    def iniciar(rutina_id=None, notas=None):
        conn = get_connection()
        cursor = conn.execute(
            "INSERT INTO sesiones (fecha, rutina_id, notas) VALUES (?, ?, ?)",
            (date.today().isoformat(), rutina_id, notas)
        )
        sesion_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return sesion_id

    @staticmethod
    def agregar_set(sesion_id, ejercicio_id, serie_num, reps,
                    peso_kg=None, equipo=None):
        conn = get_connection()
        conn.execute(
            """INSERT INTO sesion_sets
               (sesion_id, ejercicio_id, serie_num, reps, peso_kg, equipo)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sesion_id, ejercicio_id, serie_num, reps, peso_kg, equipo)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def cerrar(sesion_id, duracion_min):
        conn = get_connection()
        conn.execute(
            "UPDATE sesiones SET duracion_min = ? WHERE id = ?",
            (duracion_min, sesion_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_todas():
        conn = get_connection()
        sesiones = conn.execute(
            "SELECT * FROM sesiones ORDER BY fecha DESC"
        ).fetchall()
        conn.close()
        return sesiones

    @staticmethod
    def obtener_sets(sesion_id):
        conn = get_connection()
        sets = conn.execute(
            """SELECT ss.*, ec.nombre
               FROM sesion_sets ss
               JOIN ejercicios_cat ec ON ss.ejercicio_id = ec.id
               WHERE ss.sesion_id = ?
               ORDER BY ss.serie_num""",
            (sesion_id,)
        ).fetchall()
        conn.close()
        return sets

    @staticmethod
    def progresion(ejercicio_id):
        """Devuelve el historial de pesos para ver la progresion de un ejercicio."""
        conn = get_connection()
        historial = conn.execute(
            """SELECT s.fecha, ss.peso_kg, ss.reps, ss.serie_num
               FROM sesion_sets ss
               JOIN sesiones s ON ss.sesion_id = s.id
               WHERE ss.ejercicio_id = ?
               ORDER BY s.fecha ASC""",
            (ejercicio_id,)
        ).fetchall()
        conn.close()
        return historial