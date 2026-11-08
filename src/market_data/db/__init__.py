"""数据库连接与初始化模块"""
import os
import sqlite3

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
DB_PATH = os.environ.get(
    "MARKET_DATA_DB_PATH",
    os.path.join(_PROJECT_ROOT, "data", "market_data.db"),
)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db_path() -> str:
    return DB_PATH


def get_conn(db_path: str | None = None):
    """获取数据库连接（WAL 模式支持并发读）"""
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db(db_path: str | None = None):
    """初始化数据库表结构"""
    if db_path is None:
        db_path = DB_PATH
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    conn = get_conn(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"✅ Database initialized: {db_path}")
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor]
        print(f"📊 Tables ({len(tables)}): {tables}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
