from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
import os
from pyzbar.pyzbar import decode
from PIL import Image
import qrcode
import barcode
from barcode.writer import ImageWriter

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filename)

    # Открываем изображение
    img = cv2.imread(filename)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Распознаём штрих-коды
    detected_codes = decode(gray)

    if not detected_codes:
        return jsonify({"success": False, "error": "Не удалось распознать код"}), 400

    barcode_data = detected_codes[0].data.decode("utf-8")  # Берём первый найденный код
    barcode_type = detected_codes[0].type

    # Генерация нового изображения штрих-кода
    output_path = os.path.join(RESULT_FOLDER, f"{barcode_data}.png")

    if barcode_type in ["EAN13", "EAN8", "CODE128"]:
        barcode_class = barcode.get_barcode_class(barcode_type)
        barcode_obj = barcode_class(barcode_data, writer=ImageWriter())
        barcode_obj.save(output_path)
    else:
        qr = qrcode.make(barcode_data)
        qr.save(output_path)

    return jsonify({"success": True, "image_url": f"/get_barcode/{barcode_data}.png"})

@app.route("/get_barcode/<path:filename>")
def get_barcode(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
