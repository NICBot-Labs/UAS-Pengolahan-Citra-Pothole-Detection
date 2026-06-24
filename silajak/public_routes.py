from flask import redirect, render_template, session, url_for


def register_public_routes(app):
    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        return render_template("index.html")
