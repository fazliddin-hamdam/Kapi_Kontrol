import os
from datetime import datetime
import sqlite3
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from ultralytics import YOLO
import easyocr
import re

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

MODEL_PATH = 'model/best.pt'
try:
    model = YOLO(MODEL_PATH)
    print("✅ YOLOv8 model yüklendi")
except Exception as e:
    print(f"❌ Model yükleme hatası: {e}")
    exit(1)

# EasyOCR başlatılıyor (ilk açılış uzun sürebilir)
reader = easyocr.Reader(['tr', 'en'], gpu=False)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect('plakalar.db')
    conn.row_factory = sqlite3.Row
    return conn

def clean_plate(plate):
    return re.sub(r'[^A-Z0-9]', '', plate.upper())

@app.route('/', methods=['GET', 'POST'])
def index():
    detected_image = None
    msg = None

    if request.method == 'POST':
        file = request.files['file']
        if file and (file.filename.lower().endswith('.jpg') or file.filename.lower().endswith('.png') or file.filename.lower().endswith('.jpeg')):
            filename = f"uploaded_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image = cv2.imread(filepath)
            if image is not None:
                res_img, msg = detect_and_draw(image)
                result_filename = f"result_{filename}"
                result_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
                cv2.imwrite(result_path, res_img)
                detected_image = url_for('uploaded_file', filename=result_filename)
            else:
                msg = "Resim dosyası açılamadı."
        else:
            msg = "Yalnızca .jpg veya .png dosyası yükleyebilirsiniz!"

    conn = get_db_connection()
    plakalar = conn.execute('SELECT * FROM plakalar').fetchall()
    conn.close()
    return render_template('index.html', plakalar=plakalar, detected_image=detected_image, msg=msg)

def detect_and_draw(image):
    font = cv2.FONT_HERSHEY_SIMPLEX
    msg = ""
    conn = sqlite3.connect('plakalar.db')
    cursor = conn.cursor()

    results = model(image)[0]
    detected_truck = False
    found_plate = None

    ocr_results = []

    for box in results.boxes:
        xyxy = box.xyxy[0].cpu().numpy().astype(int)
        cls = int(box.cls[0].cpu().numpy())
        cls_name = model.names[cls].lower()
        x1, y1, x2, y2 = xyxy
        color = (0, 255, 0) if cls_name == 'car' else (255, 140, 0) if cls_name == 'truck' else (0, 255, 255)
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(image, cls_name.upper(), (x1, y1 - 10), font, 0.7, color, 2)
        if cls_name == 'truck':
            detected_truck = True

    if detected_truck:
        cursor.execute('SELECT plaka FROM plakalar')
        all_db_plates = [clean_plate(row[0]) for row in cursor.fetchall()]
        print(f"Veritabanındaki plakalar: {all_db_plates}")

        for box in results.boxes:
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            cls = int(box.cls[0].cpu().numpy())
            cls_name = model.names[cls].lower()
            if cls_name == 'plate':
                x1, y1, x2, y2 = xyxy
                h, w, _ = image.shape
                if y1 < 0 or x1 < 0 or x2 > w or y2 > h or x2 - x1 < 10 or y2 - y1 < 10:
                    continue
                crop = image[y1:y2, x1:x2]
                debug_plate_path = f"debug_plate_{x1}_{y1}.jpg"
                cv2.imwrite(debug_plate_path, crop)  # Kaydet

                # GELİŞMİŞ OCR ÖN İŞLEME (aynı şekilde kullan)
                try:
                    crop = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    gray = cv2.equalizeHist(gray)
                    blur = cv2.GaussianBlur(gray, (3,3), 0)
                    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                   cv2.THRESH_BINARY, 41, 15)
                    cv2.imwrite("ocr_oncesi_filtreli.jpg", thresh)

                    # EASY OCR
                    result = reader.readtext(thresh)
                    if result:
                        text = result[0][1].strip().upper()
                    else:
                        text = ''
                except Exception as e:
                    print("OCR Hatası:", e)
                    text = ""

                ocr_plate = clean_plate(text)
                print(f"OCR okunan plaka: '{text}', temiz: '{ocr_plate}'")
                ocr_results.append(ocr_plate)
                if ocr_plate and len(ocr_plate) > 4 and any(c.isdigit() for c in ocr_plate):
                    if ocr_plate in all_db_plates:
                        found_plate = ocr_plate
                        cv2.putText(image, f"✅ {ocr_plate} - Kapı Açıldı", (x1, y1 - 40), font, 0.8, (0,255,0), 2)
                    else:
                        cv2.putText(image, f"❌ {ocr_plate} - Buzzer!", (x1, y1 - 40), font, 0.8, (0,0,255), 2)
                else:
                    cv2.putText(image, "??? Plaka okunamadı?!", (x1, y1 - 40), font, 0.8, (0,0,255), 2)

    if found_plate:
        msg = f"✅ {found_plate} - Kapı Açıldı"
    elif len(ocr_results) == 0:
        msg = "❌ Hiç plaka kutusu algılanamadı!"
    else:
        msg = "❌ Plaka okunamadı!"

    conn.close()
    return image, msg

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/ekle', methods=('GET', 'POST'))
def ekle():
    if request.method == 'POST':
        plaka = clean_plate(request.form['plaka'])
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO plakalar (plaka) VALUES (?)', (plaka,))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            pass
        return redirect(url_for('index'))
    return render_template('ekle.html')

@app.route('/log')
def log():
    try:
        with open('log.txt', 'r', encoding='utf-8') as f:
            loglar = f.readlines()
    except FileNotFoundError:
        loglar = []
    return render_template('log.html', loglar=loglar)

if __name__ == '__main__':
    print("Flask başlatılıyor...")
    app.run(debug=True, host='0.0.0.0', port=5000)
