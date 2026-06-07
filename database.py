import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "awakening.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ── USUARIO ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            nivel_general INTEGER DEFAULT 1,
            xp_total INTEGER DEFAULT 0,
            fecha_registro TEXT DEFAULT (date('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo_stat TEXT NOT NULL,
            xp_actual INTEGER DEFAULT 0,
            nivel_actual INTEGER DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xp_historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            stat_tipo TEXT NOT NULL,
            xp_ganada INTEGER NOT NULL,
            motivo TEXT,
            fecha TEXT DEFAULT (date('now')),
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    """)

    # ── FINANZAS ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_fijos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finanzas_mes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            sueldo_neto REAL NOT NULL,
            disponible_real REAL NOT NULL,
            porcentajes TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            categoria TEXT NOT NULL,
            concepto TEXT,
            monto REAL NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colchon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meta_monto REAL NOT NULL,
            acumulado REAL DEFAULT 0,
            completado INTEGER DEFAULT 0,
            fecha_completado TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etf (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            aportacion_mensual REAL NOT NULL,
            total_acumulado REAL DEFAULT 0
        )
    """)

    # ── ENTRENAMIENTO ─────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ejercicios_cat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            grupo_muscular TEXT,
            equipo_default TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rutinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            dia_semana TEXT NOT NULL,
            descripcion TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rutina_ejercicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rutina_id INTEGER NOT NULL,
            ejercicio_id INTEGER NOT NULL,
            series INTEGER,
            reps_objetivo INTEGER,
            FOREIGN KEY (rutina_id) REFERENCES rutinas(id),
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios_cat(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            rutina_id INTEGER,
            duracion_min INTEGER,
            notas TEXT,
            FOREIGN KEY (rutina_id) REFERENCES rutinas(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sesion_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesion_id INTEGER NOT NULL,
            ejercicio_id INTEGER NOT NULL,
            serie_num INTEGER,
            reps INTEGER,
            peso_kg REAL,
            equipo TEXT,
            FOREIGN KEY (sesion_id) REFERENCES sesiones(id),
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios_cat(id)
        )
    """)

    # ── HABITOS ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habitos_cat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            stat_asociado TEXT NOT NULL,
            tipo TEXT NOT NULL,
            dias_semana TEXT,
            es_diario INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habitos_registro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            habito_id INTEGER NOT NULL,
            completado INTEGER DEFAULT 0,
            valor INTEGER,
            FOREIGN KEY (habito_id) REFERENCES habitos_cat(id)
        )
    """)

    # ── ZONA DE CASTIGO ───────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS castigos_cat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            nivel_min INTEGER NOT NULL,
            nivel_max INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS castigos_activos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            castigo_id INTEGER NOT NULL,
            fecha_asignado TEXT DEFAULT (date('now')),
            completado INTEGER DEFAULT 0,
            fecha_completado TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id),
            FOREIGN KEY (castigo_id) REFERENCES castigos_cat(id)
        )
    """)

    # ── GASTOS PERSONALES ─────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_personales_cat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            es_predefinida INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos_personales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL,
            monto_estimado REAL NOT NULL,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (categoria_id) REFERENCES gastos_personales_cat(id)
        )
    """)

    conn.commit()
    # Categorías predefinidas de gastos personales
    cats = conn.execute(
        "SELECT COUNT(*) FROM gastos_personales_cat"
    ).fetchone()[0]
    if cats == 0:
        predefinidas = [
            ("Gimnasio",), ("Transporte",), ("Alimentacion saludable",),
            ("Ropa",), ("Formacion / Cursos",), ("Higiene personal",),
            ("Ocio",), ("Suplementos",)
        ]
        conn.executemany(
            "INSERT INTO gastos_personales_cat (nombre) VALUES (?)",
            predefinidas
        )
        conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")

if __name__ == "__main__":
    init_db()