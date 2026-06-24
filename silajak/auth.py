from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import execute, query_one
from datetime import datetime


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return query_one("SELECT * FROM users WHERE id = ?", (user_id,))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or user["role"] not in roles:
                flash("Anda tidak memiliki akses ke halaman tersebut.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


def register_auth_routes(app):
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            if not name or not email or not password:
                flash("Nama, email, dan password wajib diisi.", "danger")
            elif password != confirm:
                flash("Konfirmasi password tidak sama.", "danger")
            elif query_one("SELECT id FROM users WHERE email = ?", (email,)):
                flash("Email sudah terdaftar.", "danger")
            else:
                now = datetime.now().isoformat(timespec="seconds")
                execute(
                    """
                    INSERT INTO users (name, email, phone, password, role, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'masyarakat', ?, ?)
                    """,
                    (name, email, phone, generate_password_hash(password), now, now),
                )
                flash("Registrasi berhasil. Silakan login.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = query_one("SELECT * FROM users WHERE email = ?", (email,))
            if user and check_password_hash(user["password"], password):
                session.clear()
                session["user_id"] = user["id"]
                flash("Login berhasil.", "success")
                return redirect(url_for("dashboard"))
            flash("Email atau password salah.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Anda sudah logout.", "info")
        return redirect(url_for("index"))
