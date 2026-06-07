from database import get_connection, get_cursor
import json

class Finanzas:

    # ── GASTOS FIJOS ─────────────────────────────────────

    @staticmethod
    def agregar_gasto_fijo(concepto, monto):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "INSERT INTO gastos_fijos (concepto, monto) VALUES (%s, %s)",
            (concepto, monto)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_gastos_fijos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM gastos_fijos WHERE activo = 1")
        gastos = cur.fetchall()
        cur.close()
        conn.close()
        return gastos

    @staticmethod
    def total_gastos_fijos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT SUM(monto) FROM gastos_fijos WHERE activo = 1")
        total = cur.fetchone()["sum"]
        cur.close()
        conn.close()
        return total or 0.0

    @staticmethod
    def eliminar_gasto_fijo(gasto_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "UPDATE gastos_fijos SET activo = 0 WHERE id = %s",
            (gasto_id,)
        )
        conn.commit()
        cur.close()
        conn.close()

    # ── SUELDO Y DISPONIBLE ───────────────────────────────

    @staticmethod
    def registrar_sueldo(sueldo_neto, porcentajes):
        total_fijos = Finanzas.total_gastos_fijos()
        total_personales = Finanzas.total_gastos_personales()
        disponible = sueldo_neto - total_fijos - total_personales

        from datetime import date
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """INSERT INTO finanzas_mes (fecha, sueldo_neto, disponible_real, porcentajes)
               VALUES (%s, %s, %s, %s)""",
            (date.today().isoformat(), sueldo_neto, disponible, json.dumps(porcentajes))
        )
        conn.commit()
        cur.close()
        conn.close()
        return disponible

    @staticmethod
    def calcular_distribucion(disponible, porcentajes):
        return {
            key: round(disponible * (pct / 100), 2)
            for key, pct in porcentajes.items()
        }

    @staticmethod
    def obtener_historial_sueldos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM finanzas_mes ORDER BY fecha DESC")
        historial = cur.fetchall()
        cur.close()
        conn.close()
        return historial

    # ── COLCHÓN ───────────────────────────────────────────

    @staticmethod
    def inicializar_colchon(gastos_esenciales_mes):
        meta = gastos_esenciales_mes * 3
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT id FROM colchon")
        existente = cur.fetchone()
        if not existente:
            cur.execute(
                "INSERT INTO colchon (meta_monto, acumulado) VALUES (%s, 0)",
                (meta,)
            )
            conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def actualizar_colchon(monto_añadido):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM colchon ORDER BY id DESC LIMIT 1")
        colchon = cur.fetchone()
        if not colchon:
            cur.close()
            conn.close()
            return None

        nuevo_acumulado = colchon["acumulado"] + monto_añadido
        completado = 1 if nuevo_acumulado >= colchon["meta_monto"] else 0
        fecha_completado = None

        if completado:
            from datetime import date
            fecha_completado = date.today().isoformat()

        cur.execute(
            """UPDATE colchon SET acumulado = %s, completado = %s, fecha_completado = %s
               WHERE id = %s""",
            (nuevo_acumulado, completado, fecha_completado, colchon["id"])
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"acumulado": nuevo_acumulado, "completado": bool(completado)}

    @staticmethod
    def obtener_colchon():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM colchon ORDER BY id DESC LIMIT 1")
        colchon = cur.fetchone()
        cur.close()
        conn.close()
        return colchon

    # ── TRANSACCIONES ─────────────────────────────────────

    @staticmethod
    def registrar_transaccion(categoria, monto, tipo, concepto=None):
        from datetime import date
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """INSERT INTO transacciones (fecha, categoria, concepto, monto, tipo)
               VALUES (%s, %s, %s, %s, %s)""",
            (date.today().isoformat(), categoria, concepto, monto, tipo)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_transacciones(mes=None):
        conn = get_connection()
        cur = get_cursor(conn)
        if mes:
            cur.execute(
                "SELECT * FROM transacciones WHERE fecha LIKE %s ORDER BY fecha DESC",
                (f"{mes}%",)
            )
        else:
            cur.execute("SELECT * FROM transacciones ORDER BY fecha DESC")
        transacciones = cur.fetchall()
        cur.close()
        conn.close()
        return transacciones

    # ── ETF ───────────────────────────────────────────────

    @staticmethod
    def registrar_aportacion_etf(aportacion):
        from datetime import date
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT total_acumulado FROM etf ORDER BY id DESC LIMIT 1")
        ultimo = cur.fetchone()
        total = (ultimo["total_acumulado"] if ultimo else 0) + aportacion
        cur.execute(
            "INSERT INTO etf (fecha, aportacion_mensual, total_acumulado) VALUES (%s, %s, %s)",
            (date.today().isoformat(), aportacion, total)
        )
        conn.commit()
        cur.close()
        conn.close()
        return total

    @staticmethod
    def obtener_resumen_etf():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM etf ORDER BY fecha DESC")
        resumen = cur.fetchall()
        cur.close()
        conn.close()
        return resumen

    # ── GASTOS PERSONALES ─────────────────────────────────

    @staticmethod
    def obtener_categorias_gastos_personales():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT * FROM gastos_personales_cat ORDER BY es_predefinida DESC, nombre")
        cats = cur.fetchall()
        cur.close()
        conn.close()
        return cats

    @staticmethod
    def agregar_categoria_personal(nombre):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "INSERT INTO gastos_personales_cat (nombre, es_predefinida) VALUES (%s, 0)",
            (nombre,)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def agregar_gasto_personal(categoria_id, monto_estimado):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT id FROM gastos_personales WHERE categoria_id = %s AND activo = 1",
            (categoria_id,)
        )
        existente = cur.fetchone()
        if existente:
            cur.execute(
                "UPDATE gastos_personales SET monto_estimado = %s WHERE id = %s",
                (monto_estimado, existente["id"])
            )
        else:
            cur.execute(
                "INSERT INTO gastos_personales (categoria_id, monto_estimado) VALUES (%s, %s)",
                (categoria_id, monto_estimado)
            )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_gastos_personales():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            """SELECT gp.*, gc.nombre
               FROM gastos_personales gp
               JOIN gastos_personales_cat gc ON gp.categoria_id = gc.id
               WHERE gp.activo = 1"""
        )
        gastos = cur.fetchall()
        cur.close()
        conn.close()
        return gastos

    @staticmethod
    def total_gastos_personales():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "SELECT SUM(monto_estimado) FROM gastos_personales WHERE activo = 1"
        )
        total = cur.fetchone()["sum"]
        cur.close()
        conn.close()
        return total or 0.0

    @staticmethod
    def eliminar_gasto_personal(gasto_id):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "UPDATE gastos_personales SET activo = 0 WHERE id = %s",
            (gasto_id,)
        )
        conn.commit()
        cur.close()
        conn.close()