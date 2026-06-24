from flask import Flask

from silajak.admin_routes import register_admin_routes
from silajak.auth import current_user, register_auth_routes
from silajak.config import DAMAGE_LEVELS, MAX_CONTENT_LENGTH, REPORT_STATUSES, SECRET_KEY, UPLOAD_DIR
from silajak.dashboard_routes import register_dashboard_routes
from silajak.db import close_db, init_db
from silajak.officer_routes import register_officer_routes
from silajak.public_routes import register_public_routes
from silajak.report_routes import register_report_routes
from silajak.upload_routes import register_upload_routes


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_globals():
        return {
            "current_user": current_user(),
            "report_statuses": REPORT_STATUSES,
            "damage_levels": DAMAGE_LEVELS,
        }

    register_public_routes(app)
    register_auth_routes(app)
    register_dashboard_routes(app)
    register_report_routes(app)
    register_admin_routes(app)
    register_officer_routes(app)
    register_upload_routes(app)

    return app


app = create_app()


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

