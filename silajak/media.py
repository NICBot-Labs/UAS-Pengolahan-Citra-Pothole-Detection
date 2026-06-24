from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename

from .config import ALLOWED_EXTENSIONS, UPLOAD_DIR


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_storage):
    original = secure_filename(file_storage.filename)
    suffix = Path(original).suffix.lower()
    filename = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / filename
    file_storage.save(destination)
    file_type = "video" if suffix in {".mp4", ".mov", ".avi"} else "image"
    return filename, original, file_type
