from database import get_connection, get_cursor
from datetime import date
import random

CASTIGOS_POR_NIVEL = {
    (1, 19): [
        "20 flexiones",
        "30 sentadillas",
        "10 minutos de soga",
        "20 zancadas por pierna",
        "30 segundos de plancha x 3"
    ],
    (20, 39): [
        "40 flexiones",
        "60 sentadillas",
        "20 minutos de soga",
        "40 zancadas por pierna",
        "1 minuto de plancha x 3"
    ],
    (40, 59): [
        "60 flexiones",
        "100 sentadillas",
        "30 minutos de soga + 20 flexiones",
        "60 zancadas por pierna",
        "3 series de: 20 flexiones + 30 sentadillas"
    ],
    (60, 79): [
        "80 flexiones",
        "150 sentadillas",
        "Circuito: 10 burpees + 5 min soga x 4 rondas",
        "100 zancadas por pierna",
        "4 series de: 20 flexiones + 40 sentadillas + 1 min plancha"
    ],
    (80, 99): [
        "100 flexiones",
        "200 sentadillas",
        "Circuito completo: 15 burpees + 10 min soga + 50 sentadillas x 3",
        "Tabata: 8 rondas de 20s esfuerzo / 10s descanso x 4 ejercicios",
        "5 series de: 25 flexiones + 50 sentadillas + 1.5 min plancha"
    ],
    (100, 9999): [
        "Circuito legendario: 100 flexiones + 200 sentadillas + 20 min soga",
        "150 flexiones + 300 sentadillas + 30 burpees",
        "Tabata brutal: 10 ejercicios x 8 rondas sin descanso entre ejercicios",
        "5km de carrera + 100 flexiones + 100 sentadillas",
        "Circuito Sin Titulo: lo que temas mas en ese momento x 3"
    ]
}

class Castigo:

    @staticmethod
    def obtener_castigo_por_nivel(nivel):
        for (nivel_min, nivel_max), lista in CASTIGOS_POR_NIVEL.items():
            if nivel_min <= nivel <= nivel_max:
                return random.choice(lista)
        return random.choice(CASTIGOS_POR_NIVEL[(100, 9999)])

    @staticmethod
    def asignar_castigos(usuario_id, fallos, nivel_usuario):
        conn = get_connection()
        cur = get_cursor(conn)
        castigos_asignados = []

        for fallo in fallos:
            descripcion = Castigo.obtener_castigo_por_nivel(nivel_usuario)
            cur.execute(
                """INSERT INTO castigos_activos
                   (usuario_id, castigo_id, fecha_asignado)
                   VALUES (%s, %s, %s) RETURNING id""",
                (usuario_id, fallo["id"], date.today().isoformat())
            )
            castigo_id = cur.fetchone()["id"]
            castigos_asignados.append({
                "habito": fallo["nombre"],
                "castigo": descripcion,
                "id": castigo_id
            })

        conn.commit()
        cur.close()
        conn.close()
        return castigos_asignados

    @staticmethod
    def obtener_castigos_pendientes(usuario_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT ca.*, hc.nombre as habito_nombre
               FROM castigos_activos ca
               JOIN habitos_cat hc ON ca.castigo_id = hc.id
               WHERE ca.usuario_id = %s AND ca.completado = 0
               ORDER BY ca.fecha_asignado DESC""",
            (usuario_id,)
        )
        castigos = cur.fetchall()
        cur.close()
        conn.close()
        return castigos

    @staticmethod
    def completar_castigo(castigo_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """UPDATE castigos_activos
               SET completado = 1, fecha_completado = %s
               WHERE id = %s""",
            (date.today().isoformat(), castigo_id)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_historial(usuario_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT ca.*, hc.nombre as habito_nombre
               FROM castigos_activos ca
               JOIN habitos_cat hc ON ca.castigo_id = hc.id
               WHERE ca.usuario_id = %s
               ORDER BY ca.fecha_asignado DESC""",
            (usuario_id,)
        )
        historial = cur.fetchall()
        cur.close()
        conn.close()
        return historial