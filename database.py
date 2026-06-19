import os
import psycopg2
import psycopg2.extras
import psycopg2.pool

DATABASE_URL = os.environ.get("DATABASE_URL")

# Pool de conexiones reutilizables. minconn=1 mantiene siempre 1 conexion
# abierta lista para usar; maxconn=10 limita el numero maximo simultaneo
# (suficiente para un solo worker gunicorn con trafico personal).
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)


class _PooledConnection:
    """
    Envoltorio fino sobre una conexion psycopg2 obtenida del pool.

    Todo el codigo existente llama a conn.close() al terminar, igual que
    haria con una conexion "normal". En vez de cerrar la conexion real
    (que obligaria a abrir otra desde cero la siguiente vez), close()
    devuelve la conexion al pool para que se reutilice. El resto de
    atributos/metodos (cursor, commit, rollback...) se delegan tal cual
    a la conexion real, asi que no hace falta tocar ningun otro archivo.
    """

    def __init__(self, real_conn):
        object.__setattr__(self, "_real_conn", real_conn)
        object.__setattr__(self, "_released", False)

    def close(self):
        if not self._released:
            _pool.putconn(self._real_conn)
            object.__setattr__(self, "_released", True)

    def __getattr__(self, name):
        return getattr(self._real_conn, name)

    def __setattr__(self, name, value):
        setattr(self._real_conn, name, value)


def get_connection():
    real_conn = _pool.getconn()
    # Si una conexion quedo en mal estado (p.ej. tras un error sin rollback)
    # la descartamos y pedimos una nueva en vez de propagar el problema.
    if real_conn.closed:
        _pool.putconn(real_conn, close=True)
        real_conn = _pool.getconn()
    return _PooledConnection(real_conn)


def get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def close_pool():
    """Util para tests o cierre limpio de la app."""
    _pool.closeall()

def init_db():
    conn = get_connection()
    cur = get_cursor(conn)

    # ── USUARIO ──────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            nivel_general INTEGER DEFAULT 1,
            xp_total INTEGER DEFAULT 0,
            fecha_registro TEXT DEFAULT (CURRENT_DATE::text)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            tipo_stat TEXT NOT NULL,
            xp_actual INTEGER DEFAULT 0,
            nivel_actual INTEGER DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS xp_historial (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            stat_tipo TEXT NOT NULL,
            xp_ganada INTEGER NOT NULL,
            motivo TEXT,
            fecha TEXT DEFAULT (CURRENT_DATE::text),
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    """)

    # ── FINANZAS ──────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gastos_fijos (
            id SERIAL PRIMARY KEY,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS finanzas_mes (
            id SERIAL PRIMARY KEY,
            fecha TEXT NOT NULL,
            sueldo_neto REAL NOT NULL,
            disponible_real REAL NOT NULL,
            porcentajes TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transacciones (
            id SERIAL PRIMARY KEY,
            fecha TEXT NOT NULL,
            categoria TEXT NOT NULL,
            concepto TEXT,
            monto REAL NOT NULL,
            tipo TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS colchon (
            id SERIAL PRIMARY KEY,
            meta_monto REAL NOT NULL,
            acumulado REAL DEFAULT 0,
            completado INTEGER DEFAULT 0,
            fecha_completado TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS etf (
            id SERIAL PRIMARY KEY,
            fecha TEXT NOT NULL,
            aportacion_mensual REAL NOT NULL,
            total_acumulado REAL DEFAULT 0
        )
    """)

    # ── ENTRENAMIENTO ─────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ejercicios_cat (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            grupo_muscular TEXT,
            equipo_default TEXT,
            tipo TEXT DEFAULT 'repeticiones'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rutinas (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            dia_semana TEXT NOT NULL,
            descripcion TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rutina_ejercicios (
            id SERIAL PRIMARY KEY,
            rutina_id INTEGER NOT NULL,
            ejercicio_id INTEGER NOT NULL,
            series INTEGER,
            reps_objetivo INTEGER,
            FOREIGN KEY (rutina_id) REFERENCES rutinas(id),
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios_cat(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            id SERIAL PRIMARY KEY,
            fecha TEXT NOT NULL,
            rutina_id INTEGER,
            duracion_min INTEGER,
            notas TEXT,
            FOREIGN KEY (rutina_id) REFERENCES rutinas(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sesion_sets (
            id SERIAL PRIMARY KEY,
            sesion_id INTEGER NOT NULL,
            ejercicio_id INTEGER NOT NULL,
            serie_num INTEGER,
            reps INTEGER,
            peso_kg REAL,
            equipo TEXT,
            duracion_seg INTEGER,
            FOREIGN KEY (sesion_id) REFERENCES sesiones(id),
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios_cat(id)
        )
    """)

    # ── HABITOS ───────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS habitos_cat (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            stat_asociado TEXT NOT NULL,
            tipo TEXT NOT NULL,
            dias_semana TEXT,
            es_diario INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS habitos_registro (
            id SERIAL PRIMARY KEY,
            fecha TEXT NOT NULL,
            habito_id INTEGER NOT NULL,
            completado INTEGER DEFAULT 0,
            valor INTEGER,
            FOREIGN KEY (habito_id) REFERENCES habitos_cat(id)
        )
    """)

    # ── ZONA DE CASTIGO ───────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS castigos_cat (
            id SERIAL PRIMARY KEY,
            descripcion TEXT NOT NULL,
            nivel_min INTEGER NOT NULL,
            nivel_max INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS castigos_activos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            castigo_id INTEGER NOT NULL,
            fecha_asignado TEXT DEFAULT (CURRENT_DATE::text),
            completado INTEGER DEFAULT 0,
            fecha_completado TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id),
            FOREIGN KEY (castigo_id) REFERENCES habitos_cat(id)
        )
    """)

   # ── GASTOS PERSONALES ─────────────────────────────────
    # NOTA: la tabla se creó originalmente con categoria_id (FK a una lista
    # predefinida). El modelo/rutas/HTML actuales ya usan un esquema libre
    # (nombre + monto, igual que gastos_fijos), así que migramos la tabla
    # si todavía tiene la columna vieja.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gastos_personales (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            monto_estimado REAL NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    # Si la tabla ya existía con el esquema viejo (categoria_id NOT NULL,
    # sin columna nombre), la adaptamos sin perder datos:
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'gastos_personales'
    """)
    columnas = {row["column_name"] for row in cur.fetchall()}

    if "nombre" not in columnas:
        cur.execute("ALTER TABLE gastos_personales ADD COLUMN nombre TEXT")
        # Rellenamos el nombre a partir de la categoría antigua, si existe
        if "categoria_id" in columnas:
            cur.execute("""
                UPDATE gastos_personales gp
                SET nombre = cat.nombre
                FROM gastos_personales_cat cat
                WHERE gp.categoria_id = cat.id AND gp.nombre IS NULL
            """)
        cur.execute("UPDATE gastos_personales SET nombre = 'Sin nombre' WHERE nombre IS NULL")
        cur.execute("ALTER TABLE gastos_personales ALTER COLUMN nombre SET NOT NULL")

    if "categoria_id" in columnas:
        cur.execute("ALTER TABLE gastos_personales ALTER COLUMN categoria_id DROP NOT NULL")

    conn.commit()

    cur.close()
    conn.close()
    print("Base de datos inicializada correctamente.")

if __name__ == "__main__":
    init_db()
