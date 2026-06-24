import json
import math
import os
import uuid
from datetime import datetime
from pathlib import Path

from .config import BASE_DIR, IMAGE_EXTENSIONS, MODEL_PATH, RESULT_DIR, UPLOAD_DIR, VIDEO_EXTENSIONS

# Pastikan OpenH264 DLL (dibutuhkan FFmpeg bawaan OpenCV untuk encode video
# H.264 yang bisa diputar di browser) ditemukan apa pun direktori kerja saat
# aplikasi dijalankan. DLL diletakkan di root proyek.
os.environ["PATH"] = f"{BASE_DIR}{os.pathsep}{os.environ.get('PATH', '')}"
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(str(BASE_DIR))
    except OSError:
        pass

import cv2
import numpy as np
import torch
import torchvision
from torchvision.models.detection import _utils as det_utils
from torchvision.models.detection import ssd300_vgg16
from torchvision.models.detection.ssd import SSDHead

from .db import execute_standalone


CLASSES = ["background", "pothole"]
NUM_CLASSES = 2
DISTANCE_THRESHOLD = 50
DETECT_EVERY = 10
WIDTH = 480
HEIGHT = 480
THRESHOLD = 0.25
IOU_THRESHOLD = 0.75

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL = None


def get_damage_status(total_potholes):
    if total_potholes == 0:
        return "BAIK"
    if total_potholes <= 5:
        return "RUSAK RINGAN"
    if total_potholes <= 15:
        return "RUSAK SEDANG"
    if total_potholes <= 30:
        return "RUSAK BERAT"
    return "RUSAK SANGAT BERAT"


def get_report_damage_level(status):
    if status == "RUSAK RINGAN":
        return "Ringan"
    if status == "RUSAK SEDANG":
        return "Sedang"
    if status in {"RUSAK BERAT", "RUSAK SANGAT BERAT"}:
        return "Berat"
    return None


def is_new_pothole(center, tracked_centers):
    for existing_center in tracked_centers:
        distance = math.sqrt((center[0] - existing_center[0]) ** 2 + (center[1] - existing_center[1]) ** 2)
        if distance < DISTANCE_THRESHOLD:
            return False
    return True


def load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"File model tidak ditemukan: {MODEL_PATH}")

    model = ssd300_vgg16(weights=None, weights_backbone=None)
    in_channels = det_utils.retrieve_out_channels(model.backbone, (WIDTH, HEIGHT))
    num_anchors = model.anchor_generator.num_anchors_per_location()
    model.head = SSDHead(in_channels=in_channels, num_anchors=num_anchors, num_classes=NUM_CLASSES)

    state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()

    _MODEL = model
    return _MODEL


def preprocess_bbox(prediction):
    scores_mask = prediction["scores"] >= THRESHOLD
    boxes = prediction["boxes"][scores_mask]
    scores = prediction["scores"][scores_mask]
    labels = prediction["labels"][scores_mask]

    if len(boxes) == 0:
        return {
            "boxes": torch.empty((0, 4), device=DEVICE),
            "scores": torch.empty((0,), device=DEVICE),
            "labels": torch.empty((0,), dtype=torch.int64, device=DEVICE),
        }

    nms = torchvision.ops.nms(boxes, scores, iou_threshold=IOU_THRESHOLD)
    return {
        "boxes": boxes[nms],
        "scores": scores[nms],
        "labels": labels[nms],
    }


def frame_to_tensor(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_tensor = frame_rgb / 255.0
    frame_tensor = np.transpose(frame_tensor, (2, 0, 1))
    return torch.as_tensor(frame_tensor, dtype=torch.float32).to(DEVICE)


def draw_bbox(frame, prediction, total_potholes):
    boxes = prediction["boxes"].detach().cpu().numpy().astype(int)
    scores = prediction["scores"].detach().cpu().numpy()
    labels = prediction["labels"].detach().cpu().numpy()
    status = get_damage_status(total_potholes)

    for box, score, label in zip(boxes, scores, labels):
        x1, y1, x2, y2 = box
        class_name = CLASSES[int(label)] if int(label) < len(CLASSES) else "pothole"
        text = f"{class_name}: {score:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        y_text = y1 - 10 if y1 - 10 > 10 else y1 + 20
        cv2.putText(frame, text, (x1, y_text), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"Total Lubang: {total_potholes}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, f"Status: {status}", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    return frame


def scale_prediction(prediction, scale_x, scale_y):
    scaled_prediction = {
        "boxes": prediction["boxes"].clone(),
        "scores": prediction["scores"],
        "labels": prediction["labels"],
    }
    if len(scaled_prediction["boxes"]) > 0:
        scaled_prediction["boxes"][:, 0] *= scale_x
        scaled_prediction["boxes"][:, 2] *= scale_x
        scaled_prediction["boxes"][:, 1] *= scale_y
        scaled_prediction["boxes"][:, 3] *= scale_y
    return scaled_prediction


def output_filename(source_path, suffix):
    return f"results/{Path(source_path).stem}-{uuid.uuid4().hex[:10]}{suffix}"


# Codec yang dicoba berurutan agar video hasil deteksi bisa diputar langsung
# di tag <video> HTML5. "avc1"/"H264" menghasilkan MP4 H.264 yang didukung
# browser; "mp4v" dipakai sebagai cadangan terakhir bila H.264 tidak tersedia.
BROWSER_VIDEO_CODECS = ("avc1", "H264", "h264", "mp4v")


def create_video_writer(path, fps, size):
    for codec in BROWSER_VIDEO_CODECS:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(str(path), fourcc, fps, size)
        if writer.isOpened():
            return writer, codec
        writer.release()
    return None, None


def report_progress(progress_cb, percent, message):
    if progress_cb is not None:
        progress_cb(percent, message)


def detect_image(file_path, progress_cb=None):
    report_progress(progress_cb, 15, "Memuat model deteksi...")
    model = load_model()
    frame = cv2.imread(str(file_path))
    if frame is None:
        raise ValueError("Gagal membaca gambar.")

    report_progress(progress_cb, 55, "Menjalankan deteksi pada gambar...")
    original_h, original_w = frame.shape[:2]
    scale = min(WIDTH / original_w, HEIGHT / original_h)
    new_width = max(1, int(original_w * scale))
    new_height = max(1, int(original_h * scale))
    resized_frame = cv2.resize(frame, (new_width, new_height))

    with torch.inference_mode():
        prediction = preprocess_bbox(model([frame_to_tensor(resized_frame)])[0])

    prediction = scale_prediction(prediction, original_w / new_width, original_h / new_height)
    total_potholes = len(prediction["boxes"])
    status = get_damage_status(total_potholes)
    scores = prediction["scores"].detach().cpu().numpy()
    confidence = round(float(scores.max()), 2) if len(scores) else 0.0

    report_progress(progress_cb, 85, "Menyimpan hasil deteksi...")
    result = draw_bbox(frame.copy(), prediction, total_potholes)
    result_file_path = output_filename(file_path, ".jpg")
    absolute_result_path = UPLOAD_DIR / result_file_path
    absolute_result_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(absolute_result_path), result)

    return {
        "detected": total_potholes > 0,
        "pothole_count": total_potholes,
        "confidence": confidence,
        "damage_status": status,
        "damage_level": get_report_damage_level(status),
        "result_file_path": result_file_path,
        "type": "image",
    }


def detect_video(file_path, progress_cb=None):
    report_progress(progress_cb, 0, "Memuat model deteksi...")
    model = load_model()
    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        raise ValueError("Video tidak bisa dibuka.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    result_file_path = output_filename(file_path, ".mp4")
    absolute_result_path = UPLOAD_DIR / result_file_path
    absolute_result_path.parent.mkdir(parents=True, exist_ok=True)
    out, _ = create_video_writer(absolute_result_path, fps, (video_width, video_height))
    if out is None:
        cap.release()
        raise ValueError("VideoWriter gagal dibuat.")

    tracked_centers = []
    frame_count = 0
    last_percent = -1
    confidences = []
    last_prediction = {
        "boxes": torch.empty((0, 4), device=DEVICE),
        "scores": torch.empty((0,), device=DEVICE),
        "labels": torch.empty((0,), dtype=torch.int64, device=DEVICE),
    }

    with torch.inference_mode():
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            original_frame = frame.copy()
            original_h, original_w = frame.shape[:2]
            resized_frame = cv2.resize(frame, (WIDTH, HEIGHT))

            if frame_count == 1 or frame_count % DETECT_EVERY == 0:
                prediction = preprocess_bbox(model([frame_to_tensor(resized_frame)])[0])
                last_prediction = scale_prediction(prediction, original_w / WIDTH, original_h / HEIGHT)

                scores = last_prediction["scores"].detach().cpu().numpy()
                confidences.extend(float(score) for score in scores)

                boxes_np = last_prediction["boxes"].detach().cpu().numpy()
                for box in boxes_np:
                    x1, y1, x2, y2 = box
                    center = (int((x1 + x2) / 2), int((y1 + y2) / 2))
                    if is_new_pothole(center, tracked_centers):
                        tracked_centers.append(center)

            result_frame = draw_bbox(original_frame, last_prediction, len(tracked_centers))
            out.write(result_frame)

            if progress_cb is not None:
                if total_frames > 0:
                    percent = min(99, int(frame_count / total_frames * 100))
                    if percent != last_percent:
                        last_percent = percent
                        progress_cb(percent, f"Memproses frame {frame_count}/{total_frames}")
                else:
                    progress_cb(None, f"Memproses frame {frame_count}")

    cap.release()
    out.release()

    total_potholes = len(tracked_centers)
    status = get_damage_status(total_potholes)
    confidence = round(max(confidences), 2) if confidences else 0.0

    return {
        "detected": total_potholes > 0,
        "pothole_count": total_potholes,
        "confidence": confidence,
        "damage_status": status,
        "damage_level": get_report_damage_level(status),
        "result_file_path": result_file_path,
        "type": "video",
        "processed_frames": frame_count,
    }


def run_pothole_detection(file_path, progress_cb=None):
    ext = Path(file_path).suffix.lower().lstrip(".")
    if ext in IMAGE_EXTENSIONS:
        return detect_image(file_path, progress_cb=progress_cb)
    if ext in VIDEO_EXTENSIONS:
        return detect_video(file_path, progress_cb=progress_cb)
    raise ValueError("Format file tidak didukung untuk deteksi.")


def create_detection(report_id, media_id, stored_filename, progress_cb=None):
    result = run_pothole_detection(str(UPLOAD_DIR / stored_filename), progress_cb=progress_cb)
    execute_standalone(
        """
        INSERT INTO pothole_detections
        (report_id, media_id, detected, pothole_count, confidence, result_file_path, damage_status, raw_result, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report_id,
            media_id,
            1 if result["detected"] else 0,
            result["pothole_count"],
            result["confidence"],
            result["result_file_path"],
            result["damage_status"],
            json.dumps(result, ensure_ascii=False),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return result
