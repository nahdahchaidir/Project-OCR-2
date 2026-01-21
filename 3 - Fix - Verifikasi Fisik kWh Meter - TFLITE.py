#pip install numpy pillow tensorflow

import os
import shutil
import csv
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf

# =====================================================
# CONFIG DEFAULT
# =====================================================
MODEL_PATH = "./0_model_training/model_unquant.tflite"
LABELS_PATH = "./0_model_training/labels.txt"
SRC_DIR = "./2_images"
DST_DIR = "./3_scan_output"
LOG_PATH = "./tm_scan_log.csv"

NEG_THRESHOLD = 0.7   # NEG minimal untuk dicopy
IMG_EXT = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"]

# =====================================================
# ARGUMENT PARSER
# =====================================================
def parse_args():
    p = argparse.ArgumentParser("TFLite Scanner – Teachable Machine Compatible")
    p.add_argument("--model", default=MODEL_PATH)
    p.add_argument("--labels", default=LABELS_PATH)
    p.add_argument("--src", default=SRC_DIR)
    p.add_argument("--dst", default=DST_DIR)
    p.add_argument("--log", default=LOG_PATH)
    return p.parse_args()

# =====================================================
# LOAD LABELS
# =====================================================
def load_labels(path):
    labels = [x.strip() for x in open(path, "r", encoding="utf-8") if x.strip()]
    if len(labels) != 2:
        raise ValueError("Model harus 2 kelas: KWH & NEG")

    kwh_idx = next(i for i,l in enumerate(labels) if "kwh" in l.lower())
    neg_idx = 1 - kwh_idx
    return labels, kwh_idx, neg_idx

# =====================================================
# LOAD MODEL
# =====================================================
def load_interpreter(model_path):
    itp = tf.lite.Interpreter(model_path=model_path)
    itp.allocate_tensors()

    in_det = itp.get_input_details()[0]
    out_det = itp.get_output_details()[0]

    h, w = in_det["shape"][1:3]
    dtype = in_det["dtype"]

    return itp, in_det, out_det, (h, w, dtype)

# =====================================================
# PREPROCESS (TEACHABLE MACHINE STYLE)
# =====================================================
def preprocess_image(img_path, size, dtype):
    img = Image.open(img_path).convert("RGB")

    # resize + center crop (IDENTIK TM)
    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)

    arr = np.asarray(img).astype(np.float32)

    # normalize: [-1, 1]
    arr = (arr / 127.5) - 1.0

    if dtype == np.uint8:
        arr = ((arr + 1) * 127.5).clip(0, 255).astype(np.uint8)

    return np.expand_dims(arr, axis=0)

# =====================================================
# SOFTMAX SAFE
# =====================================================
def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()

# =====================================================
# MAIN
# =====================================================
def main():
    args = parse_args()

    labels, kwh_idx, neg_idx = load_labels(args.labels)
    itp, in_det, out_det, meta = load_interpreter(args.model)
    h, w, dtype = meta

    Path(args.dst).mkdir(parents=True, exist_ok=True)

    total = copied = 0

    with open(args.log, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "P(KWH)", "P(NEG)", "copied_to"])

        for img_path in Path(args.src).rglob("*"):
            if img_path.suffix.lower() not in IMG_EXT:
                continue

            try:
                inp = preprocess_image(img_path, (w, h), dtype)

                itp.set_tensor(in_det["index"], inp)
                itp.invoke()

                raw = np.squeeze(itp.get_tensor(out_det["index"]))

                # handle sigmoid / softmax output
                if raw.ndim == 0:
                    probs = np.array([1 - raw, raw], dtype=np.float32)
                else:
                    probs = softmax(raw.astype(np.float32))

                p_kwh = float(probs[kwh_idx])
                p_neg = float(probs[neg_idx])

                copied_to = ""

                # COPY JIKA NEG > KWH DAN > THRESHOLD
                if p_neg > p_kwh and p_neg > NEG_THRESHOLD:
                    dst = Path(args.dst) / img_path.name
                    shutil.copy2(img_path, dst)
                    copied_to = str(dst)
                    copied += 1

                writer.writerow([
                    img_path.name,
                    f"{p_kwh:.4f}",
                    f"{p_neg:.4f}",
                    copied_to
                ])

                total += 1
                if total % 25 == 0:
                    print(f"[INFO] {total} image diproses...")

            except Exception as e:
                print(f"[ERROR] {img_path.name}: {e}")

    print("\n=== SELESAI ===")
    print(f"Total diproses : {total}")
    print(f"Dicopy (NEG)   : {copied}")
    print(f"Log            : {args.log}")

# =====================================================
if __name__ == "__main__":
    main()
