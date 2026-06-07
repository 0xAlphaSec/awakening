from database import get_connection
from datetime import date, datetime

DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

def dia_semana_hoy():
    return DIAS_SEMANA[datetime.today().weekday()]

class Habito:

    @staticmethod
    def inicializar_habitos():
        """Inserta los habitos predefinidos de Awakening si no existen."""
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
        existentes = conn.execute("SELECT COUNT(*) FROM habitos_cat").fetchone()[0]
        if existentes == 0:
            conn.executemany(
                """INSERT INTO habitos_cat
                   (nombre, stat_asociado, tipo, dias_semana, es_diario)
                   VALUES (?, ?, ?, ?, ?)""",
                habitos
            )
            conn.commit()
        conn.close()

    @staticmethod
    def obtener_todos():
        conn = get_connection()
        habitos = conn.execute("SELECT * FROM habitos_cat").fetchall()
        conn.close()
        return habitos

    @staticmethod
    def obtener_habitos_hoy():
        """Devuelve solo los habitos que corresponden al dia de hoy."""
        import json
        dia_hoy = dia_semana_hoy()
        conn = get_connection()
        habitos = conn.execute("SELECT * FROM habitos_cat").fetchall()
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
        """
        completado: 1 o 0
        valor: minutos de estudio si el tipo es 'minutos', None en otros casos
        """
        hoy = date.today().isoformat()
        conn = get_connection()

        existente = conn.execute(
            "SELECT id FROM habitos_registro WHERE fecha = ? AND habito_id = ?",
            (hoy, habito_id)
        ).fetchone()

        if existente:
            conn.execute(
                "UPDATE habitos_registro SET completado = ?, valor = ? WHERE id = ?",
                (completado, valor, existente["id"])
            )
        else:
            conn.execute(
                """INSERT INTO habitos_registro (fecha, habito_id, completado, valor)
                   VALUES (?, ?, ?, ?)""",
                (hoy, habito_id, completado, valor)
            )

        conn.commit()
        conn.close()

    @staticmethod
    def obtener_registro_hoy():
        hoy = date.today().isoformat()
        conn = get_connection()
        registros = conn.execute(
            """SELECT hr.*, hc.nombre, hc.stat_asociado
               FROM habitos_registro hr
               JOIN habitos_cat hc ON hr.habito_id = hc.id
               WHERE hr.fecha = ?""",
            (hoy,)
        ).fetchall()
        conn.close()
        return registros

    @staticmethod
    def obtener_fallos_ayer():
        """Devuelve los habitos que correspondian ayer y no se completaron."""
        import json
        from datetime import timedelta

        ayer = (date.today() - timedelta(days=1)).isoformat()
        dia_ayer = DIAS_SEMANA[
            (datetime.today().weekday() - 1) % 7
        ]

        conn = get_connection()
        habitos = conn.execute("SELECT * FROM habitos_cat").fetchall()

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
                registro = conn.execute(
                    """SELECT * FROM habitos_registro
                       WHERE fecha = ? AND habito_id = ? AND completado = 1""",
                    (ayer, h["id"])
                ).fetchone()
                if not registro:
                    fallos.append(dict(h))

        conn.close()
        return fallos

    @staticmethod
    def racha(habito_id):
        """Calcula los dias consecutivos que se ha cumplido un habito."""
        conn = get_connection()
        registros = conn.execute(
            """SELECT fecha FROM habitos_registro
               WHERE habito_id = ? AND completado = 1
               ORDER BY fecha DESC""",
            (habito_id,)
        ).fetchall()
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