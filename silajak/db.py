import pymysql
from datetime import datetime

from flask import g
from pymysql.cursors import DictCursor
from werkzeug.security import generate_password_hash

from .config import (
    MYSQL_DB,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    UPLOAD_DIR,
)


def connect(use_database=True):
    """Buka koneksi MySQL baru (DictCursor agar baris berperilaku seperti dict)."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB if use_database else None,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def _q(sql):
    """Terjemahkan placeholder gaya SQLite ('?') ke gaya MySQL ('%s')."""
    return sql.replace("?", "%s")


def get_db():
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_one(sql, params=()):
    with get_db().cursor() as cursor:
        cursor.execute(_q(sql), params)
        return cursor.fetchone()


def query_all(sql, params=()):
    with get_db().cursor() as cursor:
        cursor.execute(_q(sql), params)
        return cursor.fetchall()


def execute(sql, params=()):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(_q(sql), params)
    db.commit()
    return cursor


def execute_standalone(sql, params=()):
    """Operasi tulis memakai koneksi sendiri (untuk thread latar belakang)."""
    conn = connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(_q(sql), params)
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


# Skema tabel (MySQL/InnoDB). Urutan penting karena ada foreign key.
SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone VARCHAR(50),
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'masyarakat',
        created_at VARCHAR(32) NOT NULL,
        updated_at VARCHAR(32) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        road_name VARCHAR(255) NOT NULL,
        selected_road_id VARCHAR(255),
        road_geometry TEXT,
        address TEXT,
        latitude VARCHAR(64) NOT NULL,
        longitude VARCHAR(64) NOT NULL,
        additional_note TEXT,
        status VARCHAR(64) NOT NULL DEFAULT 'Menunggu Verifikasi',
        damage_level VARCHAR(32),
        verification_note TEXT,
        assigned_officer_id INT,
        created_at VARCHAR(32) NOT NULL,
        updated_at VARCHAR(32) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (assigned_officer_id) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS report_media (
        id INT AUTO_INCREMENT PRIMARY KEY,
        report_id INT NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        file_type VARCHAR(32) NOT NULL,
        original_name VARCHAR(255) NOT NULL,
        created_at VARCHAR(32) NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS pothole_detections (
        id INT AUTO_INCREMENT PRIMARY KEY,
        report_id INT NOT NULL,
        media_id INT NOT NULL,
        detected INT NOT NULL,
        pothole_count INT NOT NULL,
        confidence DOUBLE NOT NULL,
        result_file_path VARCHAR(255),
        damage_status VARCHAR(64) NOT NULL,
        raw_result TEXT,
        created_at VARCHAR(32) NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id),
        FOREIGN KEY (media_id) REFERENCES report_media(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        report_id INT NOT NULL,
        officer_id INT NOT NULL,
        assigned_by INT NOT NULL,
        priority VARCHAR(32) NOT NULL,
        task_note TEXT,
        assigned_at VARCHAR(32) NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id),
        FOREIGN KEY (officer_id) REFERENCES users(id),
        FOREIGN KEY (assigned_by) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS handling_updates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        report_id INT NOT NULL,
        officer_id INT NOT NULL,
        status VARCHAR(64) NOT NULL,
        note TEXT,
        proof_file_path VARCHAR(255),
        created_at VARCHAR(32) NOT NULL,
        FOREIGN KEY (report_id) REFERENCES reports(id),
        FOREIGN KEY (officer_id) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def init_db():
    UPLOAD_DIR.mkdir(exist_ok=True)
    (UPLOAD_DIR / "results").mkdir(exist_ok=True)

    # Buat database bila belum ada.
    server = connect(use_database=False)
    try:
        with server.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        server.commit()
    finally:
        server.close()

    # Buat tabel + seed user demo.
    db = connect()
    try:
        with db.cursor() as cursor:
            for statement in SCHEMA:
                cursor.execute(statement)
        db.commit()
        seed_demo_users(db)
        db.commit()
    finally:
        db.close()


def seed_demo_users(db):
    now = datetime.now().isoformat(timespec="seconds")
    users = [
        ("Admin SILAJAK", "admin@silajak.test", "0811000001", "admin123", "admin"),
        ("Petugas Lapangan", "petugas@silajak.test", "0811000002", "petugas123", "petugas"),
        ("Warga Demo", "user@silajak.test", "0811000003", "user123", "masyarakat"),
    ]
    with db.cursor() as cursor:
        for name, email, phone, password, role in users:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                continue
            cursor.execute(
                """
                INSERT INTO users (name, email, phone, password, role, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (name, email, phone, generate_password_hash(password), role, now, now),
            )
