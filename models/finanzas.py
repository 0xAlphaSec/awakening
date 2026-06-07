from database import get_connection
import json

class Finanzas:

    # ── GASTOS FIJOS ─────────────────────────────────────

    @staticmethod
    def agregar_gasto_fijo(concepto, monto):
        conn = get_connection()
        conn.execute(
            "INSERT INTO gastos_fijos (concepto, monto) VALUES (?, ?)",
            (concepto, monto)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_gastos_fijos():
        conn = get_connection()
        gastos = conn.execute(
            "SELECT * FROM gastos_fijos WHERE activo = 1"
        ).fetchall()
        conn.close()
        return gastos

    @staticmethod
    def total_gastos_fijos():
        conn = get_connection()
        total = conn.execute(
            "SELECT SUM(monto) FROM gastos_fijos WHERE activo = 1"
        ).fetchone()[0]
        conn.close()
        return total or 0.0

    @staticmethod
    def eliminar_gasto_fijo(gasto_id):
        conn = get_connection()
        conn.execute(
            "UPDATE gastos_fijos SET activo = 0 WHERE id = ?",
            (gasto_id,)
        )
        conn.commit()
        conn.close()

    # ── SUELDO Y DISPONIBLE ───────────────────────────────

    @staticmethod
    def registrar_sueldo(sueldo_neto, porcentajes):
        total_fijos = Finanzas.total_gastos_fijos()
        total_personales = Finanzas.total_gastos_personales()
        disponible = sueldo_neto - total_fijos - total_personales

        from datetime import date
        conn = get_connection()
        conn.execute(
            """INSERT INTO finanzas_mes (fecha, sueldo_neto, disponible_real, porcentajes)
               VALUES (?, ?, ?, ?)""",
            (date.today().isoformat(), sueldo_neto, disponible, json.dumps(porcentajes))
        )
        conn.commit()
        conn.close()
        return disponible

    @staticmethod
    def calcular_distribucion(disponible, porcentajes):
        """Devuelve el monto en EUR para cada bucket según los porcentajes."""
        return {
            key: round(disponible * (pct / 100), 2)
            for key, pct in porcentajes.items()
        }

    @staticmethod
    def obtener_historial_sueldos():
        conn = get_connection()
        historial = conn.execute(
            "SELECT * FROM finanzas_mes ORDER BY fecha DESC"
        ).fetchall()
        conn.close()
        return historial

    # ── COLCHÓN ───────────────────────────────────────────

    @staticmethod
    def inicializar_colchon(gastos_esenciales_mes):
        """Meta = gastos esenciales x 3."""
        meta = gastos_esenciales_mes * 3
        conn = get_connection()
        existente = conn.execute("SELECT id FROM colchon").fetchone()
        if not existente:
            conn.execute(
                "INSERT INTO colchon (meta_monto, acumulado) VALUES (?, 0)",
                (meta,)
            )
            conn.commit()
        conn.close()

    @staticmethod
    def actualizar_colchon(monto_añadido):
        conn = get_connection()
        colchon = conn.execute("SELECT * FROM colchon ORDER BY id DESC LIMIT 1").fetchone()
        if not colchon:
            conn.close()
            return None

        nuevo_acumulado = colchon["acumulado"] + monto_añadido
        completado = 1 if nuevo_acumulado >= colchon["meta_monto"] else 0
        fecha_completado = None

        if completado:
            from datetime import date
            fecha_completado = date.today().isoformat()

        conn.execute(
            """UPDATE colchon SET acumulado = ?, completado = ?, fecha_completado = ?
               WHERE id = ?""",
            (nuevo_acumulado, completado, fecha_completado, colchon["id"])
        )
        conn.commit()
        conn.close()
        return {"acumulado": nuevo_acumulado, "completado": bool(completado)}

    @staticmethod
    def obtener_colchon():
        conn = get_connection()
        colchon = conn.execute("SELECT * FROM colchon ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        return colchon

    # ── TRANSACCIONES ─────────────────────────────────────

    @staticmethod
    def registrar_transaccion(categoria, monto, tipo, concepto=None):
        from datetime import date
        conn = get_connection()
        conn.execute(
            """INSERT INTO transacciones (fecha, categoria, concepto, monto, tipo)
               VALUES (?, ?, ?, ?, ?)""",
            (date.today().isoformat(), categoria, concepto, monto, tipo)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_transacciones(mes=None):
        conn = get_connection()
        if mes:
            transacciones = conn.execute(
                "SELECT * FROM transacciones WHERE fecha LIKE ? ORDER BY fecha DESC",
                (f"{mes}%",)
            ).fetchall()
        else:
            transacciones = conn.execute(
                "SELECT * FROM transacciones ORDER BY fecha DESC"
            ).fetchall()
        conn.close()
        return transacciones

    # ── ETF ───────────────────────────────────────────────

    @staticmethod
    def registrar_aportacion_etf(aportacion):
        from datetime import date
        conn = get_connection()
        ultimo = conn.execute(
            "SELECT total_acumulado FROM etf ORDER BY id DESC LIMIT 1"
        ).fetchone()
        total = (ultimo["total_acumulado"] if ultimo else 0) + aportacion
        conn.execute(
            "INSERT INTO etf (fecha, aportacion_mensual, total_acumulado) VALUES (?, ?, ?)",
            (date.today().isoformat(), aportacion, total)
        )
        conn.commit()
        conn.close()
        return total

    @staticmethod
    def obtener_resumen_etf():
        conn = get_connection()
        resumen = conn.execute(
            "SELECT * FROM etf ORDER BY fecha DESC"
        ).fetchall()
        conn.close()
        return resumen
    
    # ── GASTOS PERSONALES ─────────────────────────────────

    @staticmethod
    def obtener_categorias_gastos_personales():
        conn = get_connection()
        cats = conn.execute(
            "SELECT * FROM gastos_personales_cat ORDER BY es_predefinida DESC, nombre"
        ).fetchall()
        conn.close()
        return cats

    @staticmethod
    def agregar_categoria_personal(nombre):
        conn = get_connection()
        conn.execute(
            "INSERT INTO gastos_personales_cat (nombre, es_predefinida) VALUES (?, 0)",
            (nombre,)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def agregar_gasto_personal(categoria_id, monto_estimado):
        conn = get_connection()
        existente = conn.execute(
            "SELECT id FROM gastos_personales WHERE categoria_id = ? AND activo = 1",
            (categoria_id,)
        ).fetchone()
        if existente:
            conn.execute(
                "UPDATE gastos_personales SET monto_estimado = ? WHERE id = ?",
                (monto_estimado, existente["id"])
            )
        else:
            conn.execute(
                "INSERT INTO gastos_personales (categoria_id, monto_estimado) VALUES (?, ?)",
                (categoria_id, monto_estimado)
            )
        conn.commit()
        conn.close()

    @staticmethod
    def obtener_gastos_personales():
        conn = get_connection()
        gastos = conn.execute(
            """SELECT gp.*, gc.nombre
               FROM gastos_personales gp
               JOIN gastos_personales_cat gc ON gp.categoria_id = gc.id
               WHERE gp.activo = 1"""
        ).fetchall()
        conn.close()
        return gastos

    @staticmethod
    def total_gastos_personales():
        conn = get_connection()
        total = conn.execute(
            """SELECT SUM(gp.monto_estimado)
               FROM gastos_personales gp
               WHERE gp.activo = 1"""
        ).fetchone()[0]
        conn.close()
        return total or 0.0

    @staticmethod
    def eliminar_gasto_personal(gasto_id):
        conn = get_connection()
        conn.execute(
            "UPDATE gastos_personales SET activo = 0 WHERE id = ?",
            (gasto_id,)
        )
        conn.commit()
        conn.close()