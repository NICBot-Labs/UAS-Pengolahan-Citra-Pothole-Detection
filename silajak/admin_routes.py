import csv
from datetime import datetime
from io import StringIO

from flask import Response, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from .analytics import build_report_charts
from .auth import current_user, login_required, role_required
from .config import REPORT_STATUSES, ROLES, priority_from_damage
from .db import execute, query_all, query_one


def register_admin_routes(app):
    @app.route("/admin")
    @login_required
    @role_required("admin")
    def admin_dashboard():
        stats = {status: query_one("SELECT COUNT(*) AS count FROM reports WHERE status = ?", (status,))["count"] for status in REPORT_STATUSES}
        total = query_one("SELECT COUNT(*) AS count FROM reports")["count"]
        reports = query_all(
            """
            SELECT r.*, u.name AS reporter_name
            FROM reports r
            JOIN users u ON u.id = r.user_id
            ORDER BY r.created_at DESC
            LIMIT 8
            """
        )
        # Laporan yang sudah Selesai/Ditolak diarsipkan dari peta sebaran
        # (titik lokasinya hilang), tetapi tetap tampil di tabel & rekap.
        all_reports_rows = query_all(
            "SELECT id, title, road_name, latitude, longitude, status, damage_level "
            "FROM reports WHERE status NOT IN ('Selesai', 'Ditolak')"
        )
        all_reports = [dict(item) for item in all_reports_rows]
        # Grafik dihitung dari seluruh laporan (termasuk yang sudah diarsipkan).
        chart_rows = query_all("SELECT created_at, status, damage_level FROM reports")
        charts = build_report_charts(chart_rows)
        return render_template(
            "dashboard_admin.html",
            stats=stats,
            total=total,
            reports=reports,
            all_reports=all_reports,
            charts=charts,
        )

    @app.route("/admin/reports/<int:report_id>/verify", methods=["POST"])
    @login_required
    @role_required("admin")
    def report_verify(report_id):
        report = query_one("SELECT * FROM reports WHERE id = ?", (report_id,))
        if not report:
            flash("Laporan tidak ditemukan.", "danger")
            return redirect(url_for("reports_list"))

        action = request.form.get("action", "")
        note = request.form.get("verification_note", "").strip()
        now = datetime.now().isoformat(timespec="seconds")

        if action not in {"Ditugaskan ke Petugas", "Ditolak", "Selesai"}:
            flash("Aksi verifikasi tidak valid.", "danger")
            return redirect(url_for("report_detail", report_id=report_id))

        if action == "Ditugaskan ke Petugas":
            officer = query_one(
                "SELECT * FROM users WHERE id = ? AND role = 'petugas'",
                (request.form.get("officer_id"),),
            )
            if not officer:
                flash("Pilih petugas yang valid untuk penugasan.", "danger")
                return redirect(url_for("report_detail", report_id=report_id))
            # Prioritas otomatis dari tingkat kerusakan jalan.
            priority = priority_from_damage(report["damage_level"])
            execute(
                "INSERT INTO assignments (report_id, officer_id, assigned_by, priority, task_note, assigned_at) VALUES (?, ?, ?, ?, ?, ?)",
                (report_id, officer["id"], current_user()["id"], priority, note, now),
            )
            execute(
                "UPDATE reports SET assigned_officer_id = ?, status = 'Ditugaskan ke Petugas', verification_note = ?, updated_at = ? WHERE id = ?",
                (officer["id"], note, now, report_id),
            )
            flash(f"Laporan ditugaskan ke {officer['name']} dengan prioritas {priority}.", "success")
        else:
            execute(
                "UPDATE reports SET status = ?, verification_note = ?, updated_at = ? WHERE id = ?",
                (action, note, now, report_id),
            )
            flash(f"Laporan ditandai \"{action}\".", "success")
        return redirect(url_for("report_detail", report_id=report_id))

    @app.route("/admin/recap.csv")
    @login_required
    @role_required("admin")
    def recap_csv():
        reports = query_all(
            """
            SELECT r.id, r.title, u.name AS reporter, r.road_name, r.status, r.damage_level, r.created_at
            FROM reports r
            JOIN users u ON u.id = r.user_id
            ORDER BY r.created_at DESC
            """
        )
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Judul", "Pelapor", "Ruas Jalan", "Status", "Tingkat Kerusakan", "Tanggal"])
        for item in reports:
            writer.writerow([item["id"], item["title"], item["reporter"], item["road_name"], item["status"], item["damage_level"], item["created_at"]])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=rekap_silajak.csv"},
        )

    @app.route("/admin/users")
    @login_required
    @role_required("admin")
    def manage_users():
        users = query_all("SELECT * FROM users ORDER BY role, name")
        return render_template("manage_users.html", users=users, roles=ROLES)

    @app.route("/admin/users/create", methods=["POST"])
    @login_required
    @role_required("admin")
    def user_create():
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "masyarakat")

        if not name or not email or not password:
            flash("Nama, email, dan password wajib diisi.", "danger")
        elif role not in ROLES:
            flash("Role tidak valid.", "danger")
        elif query_one("SELECT id FROM users WHERE email = ?", (email,)):
            flash("Email sudah terdaftar.", "danger")
        else:
            now = datetime.now().isoformat(timespec="seconds")
            execute(
                """
                INSERT INTO users (name, email, phone, password, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, email, phone, generate_password_hash(password), role, now, now),
            )
            flash(f"Pengguna {name} berhasil ditambahkan sebagai {role}.", "success")
        return redirect(url_for("manage_users"))

    @app.route("/admin/users/<int:user_id>/update", methods=["POST"])
    @login_required
    @role_required("admin")
    def user_update(user_id):
        user = query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("manage_users"))

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", user["role"])
        # Admin tidak boleh mengubah role akun sendiri (cegah kehilangan akses).
        if user_id == current_user()["id"]:
            role = user["role"]

        if not email:
            flash("Email wajib diisi.", "danger")
        elif role not in ROLES:
            flash("Role tidak valid.", "danger")
        elif query_one("SELECT id FROM users WHERE email = ? AND id <> ?", (email, user_id)):
            flash("Email sudah dipakai pengguna lain.", "danger")
        elif password and len(password) < 6:
            flash("Password baru minimal 6 karakter.", "danger")
        else:
            now = datetime.now().isoformat(timespec="seconds")
            if password:
                execute(
                    "UPDATE users SET email = ?, role = ?, password = ?, updated_at = ? WHERE id = ?",
                    (email, role, generate_password_hash(password), now, user_id),
                )
                flash(f"Akun {user['name']} diperbarui (termasuk password baru).", "success")
            else:
                execute(
                    "UPDATE users SET email = ?, role = ?, updated_at = ? WHERE id = ?",
                    (email, role, now, user_id),
                )
                flash(f"Akun {user['name']} berhasil diperbarui.", "success")
        return redirect(url_for("manage_users"))

    @app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
    @login_required
    @role_required("admin")
    def user_delete(user_id):
        user = query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not user:
            flash("Pengguna tidak ditemukan.", "danger")
            return redirect(url_for("manage_users"))
        if user_id == current_user()["id"]:
            flash("Anda tidak dapat menghapus akun sendiri.", "danger")
            return redirect(url_for("manage_users"))
        # Cegah hapus akun yang masih terkait data (jaga integritas referensi).
        in_use = query_one(
            """
            SELECT
              (SELECT COUNT(*) FROM reports WHERE user_id = ? OR assigned_officer_id = ?)
              + (SELECT COUNT(*) FROM assignments WHERE officer_id = ? OR assigned_by = ?)
              + (SELECT COUNT(*) FROM handling_updates WHERE officer_id = ?) AS total
            """,
            (user_id, user_id, user_id, user_id, user_id),
        )["total"]
        if in_use:
            flash(f"Akun {user['name']} tidak bisa dihapus karena masih memiliki laporan/penugasan terkait.", "danger")
        else:
            execute("DELETE FROM users WHERE id = ?", (user_id,))
            flash(f"Pengguna {user['name']} berhasil dihapus.", "success")
        return redirect(url_for("manage_users"))
