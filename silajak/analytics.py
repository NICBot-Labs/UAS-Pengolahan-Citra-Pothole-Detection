"""Agregasi data laporan untuk grafik dashboard."""

from .config import DAMAGE_LEVELS, REPORT_STATUSES


def build_report_charts(reports):
    """Hitung agregat untuk grafik dari daftar laporan yang sudah difilter.

    Setiap item harus punya kunci `created_at`, `status`, `damage_level`.
    """
    # Tren jumlah laporan per tanggal (created_at = ISO, ambil 10 char pertama).
    trend = {}
    for item in reports:
        day = (item["created_at"] or "")[:10]
        if day:
            trend[day] = trend.get(day, 0) + 1
    trend_labels = sorted(trend.keys())

    status_counts = {item: 0 for item in REPORT_STATUSES}
    for item in reports:
        if item["status"] in status_counts:
            status_counts[item["status"]] += 1

    damage_labels = DAMAGE_LEVELS + ["Belum Ada"]
    damage_counts = {item: 0 for item in damage_labels}
    for item in reports:
        key = item["damage_level"] if item["damage_level"] in DAMAGE_LEVELS else "Belum Ada"
        damage_counts[key] += 1

    return {
        "trend": {"labels": trend_labels, "values": [trend[d] for d in trend_labels]},
        "status": {"labels": list(status_counts.keys()), "values": list(status_counts.values())},
        "damage": {"labels": damage_labels, "values": [damage_counts[d] for d in damage_labels]},
    }
