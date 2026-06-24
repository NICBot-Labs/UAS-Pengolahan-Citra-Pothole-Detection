import threading
from datetime import datetime

from flask import flash, jsonify, redirect, render_template, request, url_for

from .analytics import build_report_charts
from .auth import current_user, login_required, role_required
from .config import priority_from_damage
from .db import execute, execute_standalone, query_all, query_one
from .detection import create_detection
from .jobs import create_job, get_job, update_job
from .media import allowed_file, save_uploaded_file


def run_detection_job(job_id, report_id, media_id, stored_filename, now):
    """Jalankan deteksi di thread latar belakang sambil melaporkan progres."""
    try:
        def progress_cb(percent, message):
            update_job(job_id, percent=percent, message=message)

        result = create_detection(report_id, media_id, stored_filename, progress_cb=progress_cb)
        if result.get("damage_level"):
            execute_standalone(
                "UPDATE reports SET damage_level = ?, updated_at = ? WHERE id = ?",
                (result["damage_level"], now, report_id),
            )
        update_job(job_id, status="done", percent=100, message="Deteksi selesai.")
    except Exception as exc:  # noqa: BLE001 - laporkan error apa pun ke frontend
        update_job(job_id, status="error", message="Deteksi gagal.", error=str(exc))


def register_report_routes(app):
    @app.route("/reports/new", methods=["GET", "POST"])
    @login_required
    @role_required("masyarakat")
    def report_new():
        if request.method == "POST":
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            road_name = request.form.get("road_name", "").strip()
            address = request.form.get("address", "").strip()
            latitude = request.form.get("latitude", "").strip()
            longitude = request.form.get("longitude", "").strip()
            additional_note = request.form.get("additional_note", "").strip()
            media = request.files.get("media")

            error = None
            if not title or not description:
                error = "Judul dan deskripsi kerusakan wajib diisi."
            elif not road_name or not latitude or not longitude:
                error = "Ruas jalan wajib dipilih langsung dari map view."
            elif not media or media.filename == "":
                error = "Foto atau video wajib diunggah."
            elif not allowed_file(media.filename):
                error = "Format file tidak didukung."

            if error:
                if is_ajax:
                    return jsonify({"ok": False, "error": error}), 400
                flash(error, "danger")
                return render_template("report_form.html")

            stored_filename, original_name, file_type = save_uploaded_file(media)
            now = datetime.now().isoformat(timespec="seconds")
            cursor = execute(
                """
                INSERT INTO reports
                (user_id, title, description, road_name, address, latitude, longitude, additional_note, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Menunggu Verifikasi', ?, ?)
                """,
                (
                    current_user()["id"],
                    title,
                    description,
                    road_name,
                    address,
                    latitude,
                    longitude,
                    additional_note,
                    now,
                    now,
                ),
            )
            report_id = cursor.lastrowid
            media_cursor = execute(
                "INSERT INTO report_media (report_id, file_path, file_type, original_name, created_at) VALUES (?, ?, ?, ?, ?)",
                (report_id, stored_filename, file_type, original_name, now),
            )
            media_id = media_cursor.lastrowid
            report_url = url_for("report_detail", report_id=report_id)

            if is_ajax:
                # Proses deteksi di thread latar belakang; frontend memantau
                # progres lewat endpoint detection_progress dan menampilkan bar.
                job_id = create_job(current_user()["id"], report_url)
                thread = threading.Thread(
                    target=run_detection_job,
                    args=(job_id, report_id, media_id, stored_filename, now),
                    daemon=True,
                )
                thread.start()
                return jsonify(
                    {
                        "ok": True,
                        "job_id": job_id,
                        "progress_url": url_for("detection_progress", job_id=job_id),
                        "report_url": report_url,
                    }
                )

            # Fallback tanpa JavaScript: jalankan deteksi secara sinkron.
            detection = create_detection(report_id, media_id, stored_filename)
            if detection.get("damage_level"):
                execute("UPDATE reports SET damage_level = ?, updated_at = ? WHERE id = ?", (detection["damage_level"], now, report_id))
            flash("Laporan berhasil dikirim dan media sudah diproses deteksi pothole.", "success")
            return redirect(report_url)
        return render_template("report_form.html")

    @app.route("/reports/detection-progress/<job_id>")
    @login_required
    def detection_progress(job_id):
        job = get_job(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Job deteksi tidak ditemukan."}), 404
        if job["user_id"] != current_user()["id"]:
            return jsonify({"ok": False, "error": "Tidak diizinkan."}), 403
        return jsonify(
            {
                "ok": True,
                "status": job["status"],
                "percent": job["percent"],
                "message": job["message"],
                "report_url": job["report_url"],
                "error": job["error"],
            }
        )

    @app.route("/reports")
    @login_required
    def reports_list():
        user = current_user()
        status = request.args.get("status", "")
        keyword = request.args.get("q", "").strip()
        start_date = request.args.get("start", "").strip()
        end_date = request.args.get("end", "").strip()
        clauses = []
        params = []
        if user["role"] == "masyarakat":
            clauses.append("r.user_id = ?")
            params.append(user["id"])
        elif user["role"] == "petugas":
            clauses.append("r.assigned_officer_id = ?")
            params.append(user["id"])
        if status:
            clauses.append("r.status = ?")
            params.append(status)
        if keyword:
            clauses.append("(r.title LIKE ? OR r.road_name LIKE ? OR u.name LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if start_date:
            clauses.append("substr(r.created_at, 1, 10) >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("substr(r.created_at, 1, 10) <= ?")
            params.append(end_date)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        reports = query_all(
            f"""
            SELECT r.*, u.name AS reporter_name, o.name AS officer_name
            FROM reports r
            JOIN users u ON u.id = r.user_id
            LEFT JOIN users o ON o.id = r.assigned_officer_id
            {where}
            ORDER BY r.created_at DESC
            """,
            params,
        )
        charts = build_report_charts(reports)
        return render_template(
            "reports_list.html",
            reports=reports,
            status=status,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            charts=charts,
        )

    @app.route("/reports/<int:report_id>")
    @login_required
    def report_detail(report_id):
        user = current_user()
        report = query_one(
            """
            SELECT r.*, u.name AS reporter_name, u.email AS reporter_email, o.name AS officer_name
            FROM reports r
            JOIN users u ON u.id = r.user_id
            LEFT JOIN users o ON o.id = r.assigned_officer_id
            WHERE r.id = ?
            """,
            (report_id,),
        )
        if not report:
            flash("Laporan tidak ditemukan.", "danger")
            return redirect(url_for("reports_list"))
        if user["role"] == "masyarakat" and report["user_id"] != user["id"]:
            flash("Anda hanya dapat melihat laporan milik sendiri.", "danger")
            return redirect(url_for("reports_list"))
        if user["role"] == "petugas" and report["assigned_officer_id"] != user["id"]:
            flash("Laporan ini belum ditugaskan kepada Anda.", "danger")
            return redirect(url_for("reports_list"))
        media = query_all("SELECT * FROM report_media WHERE report_id = ?", (report_id,))
        detections = query_all("SELECT * FROM pothole_detections WHERE report_id = ?", (report_id,))
        updates = query_all(
            """
            SELECT h.*, u.name AS officer_name
            FROM handling_updates h
            JOIN users u ON u.id = h.officer_id
            WHERE h.report_id = ?
            ORDER BY h.created_at DESC
            """,
            (report_id,),
        )
        officers = query_all("SELECT * FROM users WHERE role = 'petugas' ORDER BY name") if user["role"] == "admin" else []
        priority = priority_from_damage(report["damage_level"])
        return render_template("report_detail.html", report=report, media=media, detections=detections, updates=updates, officers=officers, priority=priority)
