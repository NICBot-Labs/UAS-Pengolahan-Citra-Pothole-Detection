"""Penyimpan progres job deteksi (in-memory, thread-safe).

Dipakai untuk melaporkan progres proses deteksi yang berjalan di thread latar
belakang ke frontend lewat polling. Cukup untuk server pengembangan single
proses; bukan untuk multi-worker produksi.
"""

import threading
import uuid

_lock = threading.Lock()
_jobs = {}


def create_job(user_id, report_url):
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "user_id": user_id,
            "status": "processing",  # processing | done | error
            "percent": 0,
            "message": "Menyiapkan deteksi...",
            "report_url": report_url,
            "error": None,
        }
    return job_id


def update_job(job_id, **fields):
    with _lock:
        job = _jobs.get(job_id)
        if job is not None:
            job.update(fields)


def get_job(job_id):
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job is not None else None
