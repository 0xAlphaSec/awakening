from database import get_connection, get_cursor
from datetime import date

NIVELES = [
    (1,   4,   "Dormido",            0),
    (5,   9,   "Despertando",        500),
    (10,  19,  "Cazador E",          1500),
    (20,  29,  "Cazador D",          3500),
    (30,  39,  "Cazador C",          7000),
    (40,  49,  "Cazador B",          15000),
    (50,  59,  "Cazador A",          30000),
    (60,  69,  "Cazador S",          60000),
    (70,  79,  "Cazador Nacional",   120000),
    (80,  89,  "Monarca en Ascenso", 250000),
    (90,  99,  "Monarca",            500000),
    (100, 9999,"Sin Titulo",         1000000),
]

STATS = ["Fuerza", "Resistencia", "Conocimiento", "Riqueza", "Vitalidad", "Disciplina"]

XP_POR_ACCION = {
    "sesion_fuerza":       50,
    "sesion_cardio":       40,
    "habito_bool":         20,
    "habito_minutos":      1,
    "ahorro_registrado":   30,
    "racha_7dias":         100,
    "racha_30dias":        500,
}

def nombre_nivel(nivel):
    for (nmin, nmax, nombre, _) in NIVELES:
        if nmin <= nivel <= nmax:
            return nombre
    return "Sin Titulo"

def xp_para_nivel(nivel):
    for i, (nmin, nmax, _, xp) in enumerate(NIVELES):
        if nmin <= nivel <= nmax:
            if i + 1 < len(NIVELES):
                return NIVELES[i + 1][3]
            return None
    return None

class Usuario:

    @staticmethod
    def crear(nombre):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT id FROM usuario LIMIT 1")
        existente = cur.fetchone()
        if existente:
            cur.close()
            conn.close()
            return existente["id"]

        cur.execute(
            "INSERT INTO usuario (nombre, nivel_general, xp_total) VALUES (%s, 1, 0) RETURNING id",
            (nombre,)
        )
        usuario_id = cur.fetchone()["id"]

        for stat in STATS:
            cur.execute(
                "INSERT INTO stats (usuario_id, tipo_stat, xp_actual, nivel_actual) VALUES (%s, %s, 0, 1)",
                (usuario_id, stat)
            )

        conn.commit()
        cur.close()
        conn.close()
        return usuario_id

    @staticmethod
    def obtener():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM usuario LIMIT 1")
        usuario = cur.fetchone()
        cur.close()
        conn.close()
        return dict(usuario) if usuario else None

    @staticmethod
    def ganar_xp(stat_tipo, xp, motivo=""):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM usuario LIMIT 1")
        usuario = cur.fetchone()
        if not usuario:
            cur.close()
            conn.close()
            return None

        usuario_id = usuario["id"]

        cur.execute(
            "SELECT * FROM stats WHERE usuario_id = %s AND tipo_stat = %s",
            (usuario_id, stat_tipo)
        )
        stat = cur.fetchone()

        nueva_xp = stat["xp_actual"] + xp
        nuevo_nivel = stat["nivel_actual"]

        for (nmin, nmax, _, xp_req) in NIVELES:
            if nueva_xp >= xp_req:
                nuevo_nivel = nmin
            else:
                break

        cur.execute(
            "UPDATE stats SET xp_actual = %s, nivel_actual = %s WHERE id = %s",
            (nueva_xp, nuevo_nivel, stat["id"])
        )

        cur.execute(
            """INSERT INTO xp_historial (usuario_id, stat_tipo, xp_ganada, motivo, fecha)
               VALUES (%s, %s, %s, %s, %s)""",
            (usuario_id, stat_tipo, xp, motivo, date.today().isoformat())
        )

        nueva_xp_total = usuario["xp_total"] + xp
        cur.execute(
            "SELECT nivel_actual FROM stats WHERE usuario_id = %s",
            (usuario_id,)
        )
        stats_niveles = cur.fetchall()
        nivel_general = round(sum(s["nivel_actual"] for s in stats_niveles) / len(stats_niveles))

        cur.execute(
            "UPDATE usuario SET xp_total = %s, nivel_general = %s WHERE id = %s",
            (nueva_xp_total, nivel_general, usuario_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        return {
            "stat": stat_tipo,
            "xp_ganada": xp,
            "xp_total_stat": nueva_xp,
            "nivel_stat": nuevo_nivel,
            "nombre_nivel": nombre_nivel(nuevo_nivel)
        }

    @staticmethod
    def status_screen():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM usuario LIMIT 1")
        usuario = cur.fetchone()
        if not usuario:
            cur.close()
            conn.close()
            return None

        cur.execute(
            "SELECT * FROM stats WHERE usuario_id = %s",
            (usuario["id"],)
        )
        stats = cur.fetchall()
        cur.close()
        conn.close()

        resultado = {
            "nombre": usuario["nombre"],
            "nivel_general": usuario["nivel_general"],
            "nombre_nivel": nombre_nivel(usuario["nivel_general"]),
            "xp_total": usuario["xp_total"],
            "stats": []
        }

        for s in stats:
            resultado["stats"].append({
                "stat": s["tipo_stat"],
                "nivel": s["nivel_actual"],
                "nombre_nivel": nombre_nivel(s["nivel_actual"]),
                "xp_actual": s["xp_actual"],
                "xp_siguiente_nivel": xp_para_nivel(s["nivel_actual"] + 1) if s["nivel_actual"] < 100 else None
            })

        return resultado