from datetime import datetime

from flask import flash, redirect, render_template, request, url_for

from .auth import current_user, login_required, role_required
from .db import execute, query_all, query_one
from .media import allowed_file, save_uploaded_file


def register_officer_routes(app):
    @app.route("/officer")
    @login_required
    @role_required("petugas")
    def officer_dashboard():
        user = current_user()
        reports = query_all(
            """
            SELECT r.*, u.name AS reporter_name
            FROM reports r
            JOIN users u ON u.id = r.user_id
            WHERE r.assigned_officer_id = ?
            ORDER BY r.updated_at DESC
            """,
            (user["id"],),
        )
        stats = {
            "new": sum(1 for item in reports if item["status"] == "Ditugaskan ke Petugas"),
            "progress": sum(1 for item in reports if item["status"] == "Dalam Penanganan"),
            "pending_final": sum(1 for item in reports if item["status"] == "Menunggu Verifikasi Selesai"),
            "done": sum(1 for item in reports if item["status"] == "Selesai"),
        }
        return render_template("dashboard_officer.html", reports=reports, stats=stats)

    @app.route("/officer/reports/<int:report_id>/update", methods=["POST"])
    @login_required
    @role_required("petugas")
    def handling_update(report_id):
        user = current_user()
        report = query_one("SELECT * FROM reports WHERE id = ? AND assigned_officer_id = ?", (report_id, user["id"]))
        if not report:
            flash("Laporan ini belum ditugaskan kepada Anda.", "danger")
            return redirect(url_for("reports_list"))
        status = request.form.get("status", "Dalam Penanganan")
        note = request.form.get("note", "").strip()
        proof = request.files.get("proof")

        # Petugas hanya boleh sampai "Menunggu Verifikasi Selesai"; status final
        # "Selesai" hanya boleh ditetapkan admin lewat verifikasi.
        allowed_statuses = {"Dalam Penanganan", "Menunggu Verifikasi Selesai"}
        if status not in allowed_statuses:
            flash("Status penanganan tidak valid. Penyelesaian laporan harus diverifikasi admin.", "danger")
            return redirect(url_for("report_detail", report_id=report_id))
        if status == "Menunggu Verifikasi Selesai" and not (proof and proof.filename):
            flash("Bukti perbaikan wajib diunggah sebelum meminta verifikasi selesai.", "danger")
            return redirect(url_for("report_detail", report_id=report_id))

        proof_file_path = None
        if proof and proof.filename:
            if not allowed_file(proof.filename):
                flash("Format bukti penanganan tidak didukung.", "danger")
                return redirect(url_for("report_detail", report_id=report_id))
            proof_file_path, _, _ = save_uploaded_file(proof)
        now = datetime.now().isoformat(timespec="seconds")
        execute(
            "INSERT INTO handling_updates (report_id, officer_id, status, note, proof_file_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (report_id, user["id"], status, note, proof_file_path, now),
        )
        execute("UPDATE reports SET status = ?, updated_at = ? WHERE id = ?", (status, now, report_id))
        flash("Status penanganan berhasil diperbarui.", "success")
        return redirect(url_for("report_detail", report_id=report_id))
