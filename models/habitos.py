from database import get_connection, get_cursor
from datetime import date, datetime
import json

DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

def dia_semana_hoy():
    return DIAS_SEMANA[datetime.today().weekday()]

class Habito:

    @staticmethod
    def inicializar_habitos():
        habitos = [
            ("Entrenamiento de fuerza", "Fuerza",      "datos",   '["Lunes","Jueves","Viernes"]', 0),
            ("Cardio",                  "Resistencia",  "datos",   '["Martes","Sabado"]',          0),
            ("Alimentacion saludable",  "Vitalidad",    "bool",    None,                           1),
            ("Hidratacion",             "Vitalidad",    "bool",    None,                           1),
            ("Dormir bien",             "Vitalidad",    "bool",    None,                           1),
            ("Estudio hacking",         "Conocimiento", "minutos", '["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado"]', 0),
            ("Estudio idiomas",         "Conocimiento", "minutos", '["Martes","Jueves","Sabado"]',  0),
            ("Lectura",                 "Conocimiento", "bool",    None,                           1),
            ("Control financiero",      "Riqueza",      "datos",   None,                           0),
            ("NoFap",                   "Disciplina",   "bool",    None,                           1),
            ("No groserias",            "Disciplina",   "bool",    None,                           1),
            ("Mantener la calma",       "Disciplina",   "bool",    None,                           1),
            ("Pensar antes de hablar",  "Disciplina",   "bool",    None,                           1),
        ]

        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT COUNT(*) FROM habitos_cat")
        existentes = cur.fetchone()["count"]
        if existentes == 0:
            cur.executemany(
                """INSERT INTO habitos_cat
                   (nombre, stat_asociado, tipo, dias_semana, es_diario)
                   VALUES (%s, %s, %s, %s, %s)""",
                habitos
            )
            conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_todos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM habitos_cat")
        habitos = cur.fetchall()
        cur.close()
        conn.close()
        return habitos

    @staticmethod
    def obtener_habitos_hoy():
        dia_hoy = dia_semana_hoy()
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM habitos_cat")
        habitos = cur.fetchall()
        cur.close()
        conn.close()

        resultado = []
        for h in habitos:
            if h["es_diario"]:
                resultado.append(dict(h))
            elif h["dias_semana"]:
                dias = json.loads(h["dias_semana"])
                if dia_hoy in dias:
                    resultado.append(dict(h))
        return resultado

    @staticmethod
    def registrar(habito_id, completado, valor=None):
        hoy = date.today().isoformat()
        conn = get_connection()
        cur = get_cursor(conn)

        cur.execute(
            "SELECT id FROM habitos_registro WHERE fecha = %s AND habito_id = %s",
            (hoy, habito_id)
        )
        existente = cur.fetchone()

        if existente:
            cur.execute(
                "UPDATE habitos_registro SET completado = %s, valor = %s WHERE id = %s",
                (completado, valor, existente["id"])
            )
        else:
            cur.execute(
                """INSERT INTO habitos_registro (fecha, habito_id, completado, valor)
                   VALUES (%s, %s, %s, %s)""",
                (hoy, habito_id, completado, valor)
            )

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_registro_hoy():
        hoy = date.today().isoformat()
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT hr.*, hc.nombre, hc.stat_asociado
               FROM habitos_registro hr
               JOIN habitos_cat hc ON hr.habito_id = hc.id
               WHERE hr.fecha = %s""",
            (hoy,)
        )
        registros = cur.fetchall()
        cur.close()
        conn.close()
        return registros

    @staticmethod
    def obtener_fallos_ayer():
        from datetime import timedelta

        ayer = (date.today() - timedelta(days=1)).isoformat()
        dia_ayer = DIAS_SEMANA[(datetime.today().weekday() - 1) % 7]

        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM habitos_cat")
        habitos = cur.fetchall()

        fallos = []
        for h in habitos:
            aplicaba = False
            if h["es_diario"]:
                aplicaba = True
            elif h["dias_semana"]:
                dias = json.loads(h["dias_semana"])
                if dia_ayer in dias:
                    aplicaba = True

            if aplicaba:
                cur.execute(
                    """SELECT * FROM habitos_registro
                       WHERE fecha = %s AND habito_id = %s AND completado = 1""",
                    (ayer, h["id"])
                )
                registro = cur.fetchone()
                if not registro:
                    fallos.append(dict(h))

        cur.close()
        conn.close()
        return fallos

    @staticmethod
    def racha(habito_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT fecha FROM habitos_registro
               WHERE habito_id = %s AND completado = 1
               ORDER BY fecha DESC""",
            (habito_id,)
        )
        registros = cur.fetchall()
        cur.close()
        conn.close()

        if not registros:
            return 0

        from datetime import timedelta
        racha = 0
        fecha_esperada = date.today()

        for r in registros:
            fecha_registro = date.fromisoformat(r["fecha"])
            if fecha_registro == fecha_esperada:
                racha += 1
                fecha_esperada -= timedelta(days=1)
            else:
                break

        return racha