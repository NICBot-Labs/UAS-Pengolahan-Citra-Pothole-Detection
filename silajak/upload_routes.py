from flask import current_app, send_from_directory

from .auth import login_required


def register_upload_routes(app):
    @app.route("/uploads/<path:filename>")
    @login_required
    def uploaded_file(filename):
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
