"""Migrasi data dari SQLite (instance/silajak.db) ke MySQL Laragon.

Membuat ulang database MySQL `silajak` dengan skema InnoDB, lalu menyalin
seluruh isi tabel apa adanya (mempertahankan nilai id/primary key).

Jalankan sekali: `py migrate_sqlite_to_mysql.py`
PERINGATAN: database MySQL `silajak` akan DIBUAT ULANG (DROP lalu CREATE).
"""

import sqlite3

from silajak import db as dbmod
from silajak.config import MYSQL_DB, SQLITE_DATABASE

# Urutan FK-safe (parent dulu).
TABLES = ["users", "reports", "report_media", "pothole_detections", "assignments", "handling_updates"]


def main():
    if not SQLITE_DATABASE.exists():
        print(f"SQLite tidak ditemukan: {SQLITE_DATABASE}")
        return

    # 1. Buat ulang database MySQL + skema.
    server = dbmod.connect(use_database=False)
    try:
        with server.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{MYSQL_DB}`")
            cursor.execute(
                f"CREATE DATABASE `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        server.commit()
    finally:
        server.close()

    target = dbmod.connect()
    src = sqlite3.connect(str(SQLITE_DATABASE))
    src.row_factory = sqlite3.Row
    total = 0
    try:
        with target.cursor() as cursor:
            for statement in dbmod.SCHEMA:
                cursor.execute(statement)
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        target.commit()

        # 2. Salin tiap tabel.
        for table in TABLES:
            rows = src.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                print(f"  {table}: 0 baris")
                continue
            cols = rows[0].keys()
            col_list = ",".join(f"`{c}`" for c in cols)
            placeholders = ",".join(["%s"] * len(cols))
            insert_sql = f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})"
            with target.cursor() as cursor:
                for row in rows:
                    cursor.execute(insert_sql, tuple(row[c] for c in cols))
            target.commit()
            print(f"  {table}: {len(rows)} baris")
            total += len(rows)

        with target.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        target.commit()
    finally:
        src.close()
        target.close()

    print(f"Selesai. Total {total} baris dipindahkan ke MySQL `{MYSQL_DB}`.")


if __name__ == "__main__":
    main()
