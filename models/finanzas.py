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
        cur.execute("SELECT id, concepto, monto, activo FROM gastos_fijos WHERE activo = 1")
        gastos = cur.fetchall()
        cur.close()
        conn.close()
        # Si viene como tupla, lo transformamos en diccionario manualmente para asegurar compatibilidad
        if gastos and isinstance(gastos[0], tuple):
            return [{"id": g[0], "concepto": g[1], "monto": float(g[2])} for g in gastos]
        return gastos

    @staticmethod
    def total_gastos_fijos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT SUM(monto) FROM gastos_fijos WHERE activo = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return 0.0
        total = row["sum"] if isinstance(row, dict) else row[0]
        return float(total) if total is not None else 0.0

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
    def calcular_distribucion(disponible, aportaciones):
        # 'aportaciones' contiene importes fijos en € (no porcentajes).
        # Se devuelve tal cual; el 'disponible' se usa solo para validar que cuadre.
        return {key: round(monto, 2) for key, monto in aportaciones.items()}

    @staticmethod
    def obtener_historial_sueldos():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT id, fecha, sueldo_neto, disponible_real, porcentajes FROM finanzas_mes ORDER BY fecha DESC")
        historial = cur.fetchall()
        cur.close()
        conn.close()
        if historial and isinstance(historial[0], tuple):
            return [{
                "id": h[0], 
                "fecha": str(h[1]), 
                "sueldo_neto": float(h[2]), 
                "disponible_real": float(h[3]), 
                "porcentajes": h[4]
            } for h in historial]
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
    # Ahora son libres: nombre + monto, igual que los gastos fijos.
    # (las categorías predefinidas ya no se usan)

    @staticmethod
    def agregar_gasto_personal(nombre, monto_estimado):
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute(
            "INSERT INTO gastos_personales (nombre, monto_estimado) VALUES (%s, %s)",
            (nombre, monto_estimado)
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def obtener_gastos_personales():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT id, nombre, monto_estimado, activo FROM gastos_personales WHERE activo = 1 ORDER BY nombre")
        gastos = cur.fetchall()
        cur.close()
        conn.close()
        if gastos and isinstance(gastos[0], tuple):
            return [{"id": g[0], "nombre": g[1], "monto_estimado": float(g[2])} for g in gastos]
        return gastos

    @staticmethod
    def total_gastos_personales():
        conn = get_connection()
        cur = get_cursor(conn)
        cur.execute("SELECT SUM(monto_estimado) FROM gastos_personales WHERE activo = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return 0.0
        total = row["sum"] if isinstance(row, dict) else row[0]
        return float(total) if total is not None else 0.0

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
