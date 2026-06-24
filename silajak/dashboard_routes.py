from flask import redirect, render_template, url_for

from .auth import current_user, login_required
from .db import query_all


def register_dashboard_routes(app):
    @app.route("/dashboard")
    @login_required
    def dashboard():
        user = current_user()
        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))
        if user["role"] == "petugas":
            return redirect(url_for("officer_dashboard"))
        reports = query_all("SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC", (user["id"],))
        stats = {
            "total": len(reports),
            "waiting": sum(1 for item in reports if item["status"] == "Menunggu Verifikasi"),
            "progress": sum(1 for item in reports if item["status"] in {"Ditugaskan ke Petugas", "Dalam Penanganan", "Menunggu Verifikasi Selesai"}),
            "done": sum(1 for item in reports if item["status"] == "Selesai"),
        }
        return render_template("dashboard_user.html", reports=reports, stats=stats)
