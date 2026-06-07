from database import get_connection, get_cursor
from datetime import date

class Ejercicio:

    @staticmethod
    def agregar(nombre, grupo_muscular=None, equipo_default=None):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "INSERT INTO ejercicios_cat (nombre, grupo_muscular, equipo_default) VALUES (%s, %s, %s)",
            (nombre, grupo_muscular, equipo_default)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_todos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM ejercicios_cat ORDER BY nombre")
        ejercicios = cur.fetchall()
        cur.close()
        conn.close()
        return ejercicios

    @staticmethod
    def obtener_por_id(ejercicio_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM ejercicios_cat WHERE id = %s", (ejercicio_id,))
        ejercicio = cur.fetchone()
        cur.close()
        conn.close()
        return ejercicio


class Rutina:

    @staticmethod
    def agregar(nombre, dia_semana, descripcion=None):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "INSERT INTO rutinas (nombre, dia_semana, descripcion) VALUES (%s, %s, %s)",
            (nombre, dia_semana, descripcion)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_todas():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM rutinas ORDER BY dia_semana")
        rutinas = cur.fetchall()
        cur.close()
        conn.close()
        return rutinas

    @staticmethod
    def obtener_por_dia(dia):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM rutinas WHERE dia_semana = %s", (dia,))
        rutina = cur.fetchone()
        cur.close()
        conn.close()
        return rutina

    @staticmethod
    def agregar_ejercicio(rutina_id, ejercicio_id, series=None, reps_objetivo=None):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """INSERT INTO rutina_ejercicios (rutina_id, ejercicio_id, series, reps_objetivo)
               VALUES (%s, %s, %s, %s)""",
            (rutina_id, ejercicio_id, series, reps_objetivo)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_ejercicios(rutina_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT re.*, ec.nombre, ec.grupo_muscular, ec.equipo_default
               FROM rutina_ejercicios re
               JOIN ejercicios_cat ec ON re.ejercicio_id = ec.id
               WHERE re.rutina_id = %s""",
            (rutina_id,)
        )
        ejercicios = cur.fetchall()
        cur.close()
        conn.close()
        return ejercicios


class Sesion:

    @staticmethod
    def iniciar(rutina_id=None, notas=None):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "INSERT INTO sesiones (fecha, rutina_id, notas) VALUES (%s, %s, %s) RETURNING id",
            (date.today().isoformat(), rutina_id, notas)
        )
        sesion_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        return sesion_id

    @staticmethod
    def agregar_set(sesion_id, ejercicio_id, serie_num, reps,
                    peso_kg=None, equipo=None):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """INSERT INTO sesion_sets
               (sesion_id, ejercicio_id, serie_num, reps, peso_kg, equipo)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (sesion_id, ejercicio_id, serie_num, reps, peso_kg, equipo)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def cerrar(sesion_id, duracion_min):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "UPDATE sesiones SET duracion_min = %s WHERE id = %s",
            (duracion_min, sesion_id)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_todas():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM sesiones ORDER BY fecha DESC")
        sesiones = cur.fetchall()
        cur.close()
        conn.close()
        return sesiones

    @staticmethod
    def obtener_sets(sesion_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT ss.*, ec.nombre
               FROM sesion_sets ss
               JOIN ejercicios_cat ec ON ss.ejercicio_id = ec.id
               WHERE ss.sesion_id = %s
               ORDER BY ss.serie_num""",
            (sesion_id,)
        )
        sets = cur.fetchall()
        cur.close()
        conn.close()
        return sets

    @staticmethod
    def progresion(ejercicio_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT s.fecha, ss.peso_kg, ss.reps, ss.serie_num
               FROM sesion_sets ss
               JOIN sesiones s ON ss.sesion_id = s.id
               WHERE ss.ejercicio_id = %s
               ORDER BY s.fecha ASC""",
            (ejercicio_id,)
        )
        historial = cur.fetchall()
        cur.close()
        conn.close()
        return historial
    
    @staticmethod
    def obtener_por_id(rutina_id): 
        conn = get_connection()
        cur = conn.cursor(cursor_factory=__import__('psycopg2').extras.RealDictCursor)
        cur.execute("SELECT * FROM rutinas WHERE id = %s", (rutina_id,))
        rutina = cur.fetchone()
        cur.close()
        conn.close()
        return rutina