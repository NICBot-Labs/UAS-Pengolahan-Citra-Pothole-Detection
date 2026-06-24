import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database SQLite lama (dipakai hanya oleh skrip migrasi ke MySQL).
SQLITE_DATABASE = BASE_DIR / "instance" / "silajak.db"

# Koneksi MySQL (default Laragon: root tanpa password). Bisa di-override via
# environment variable saat deploy.
MYSQL_HOST = os.environ.get("SILAJAK_DB_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("SILAJAK_DB_PORT", "3306"))
MYSQL_USER = os.environ.get("SILAJAK_DB_USER", "root")
MYSQL_PASSWORD = os.environ.get("SILAJAK_DB_PASSWORD", "")
MYSQL_DB = os.environ.get("SILAJAK_DB_NAME", "silajak")

UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = UPLOAD_DIR / "results"
MODEL_PATH = Path(os.environ.get("SILAJAK_MODEL_PATH", BASE_DIR / "models" / "model.pth"))
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "mp4", "mov", "avi"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi"}

REPORT_STATUSES = [
    "Menunggu Verifikasi",
    "Ditugaskan ke Petugas",
    "Ditolak",
    "Dalam Penanganan",
    "Menunggu Verifikasi Selesai",
    "Selesai",
]
DAMAGE_LEVELS = ["Ringan", "Sedang", "Berat"]
ROLES = ["masyarakat", "petugas", "admin"]

# Prioritas penugasan ditentukan otomatis dari tingkat kerusakan jalan.
PRIORITY_BY_DAMAGE = {"Berat": "Tinggi", "Sedang": "Sedang", "Ringan": "Rendah"}


def priority_from_damage(damage_level):
    return PRIORITY_BY_DAMAGE.get(damage_level, "Rendah")

SECRET_KEY = os.environ.get("SECRET_KEY", "silajak-dev-secret")
MAX_CONTENT_LENGTH = 100 * 1024 * 1024
