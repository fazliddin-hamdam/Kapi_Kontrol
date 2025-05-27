# KAPI KONTROL SİSTEMİ

Bu proje, görüntü işleme ve yapay zeka kullanarak araç plaka tespiti ve sınıflandırma (araba/kamyon/plaka) yapan bir kapı kontrol sistemidir.

## Özellikler

- Yüklenen resim üzerinden **araba, kamyon (truck), plaka** algılar ve kutu içine alır.
- Eğer bir **kamyon (truck)** algılanırsa, plakasını OCR ile okur ve **veritabanındaki plakalarla karşılaştırır**:
    - Kayıtlıysa: "Kapı açıldı" mesajı.
    - Kayıtlı değilse: "Buzzer çalıştı" uyarısı.
- Web arayüzü ile kullanıcı dostu **resim yükleme ve sonuç görüntüleme**.
- Plaka ve araç kayıt yönetimi.

## Kurulum

1. **Gerekli kütüphaneleri yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
2. **Tesseract kurulumu**  
    - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) bilgisayarınıza kurulu olmalı ve `app.py` içinde doğru yol tanımlanmalı.

3. **Uygulamayı başlatın:**
    ```bash
    python app.py
    ```

4. **Web tarayıcınızda** `http://localhost:5000` adresine gidin.

## Kullanım

- **Resim veya video yükleyerek** araç/plaka tespitini başlatın.
- Sistemde kayıtlı plakaları görüntüleyin, yeni plaka ekleyin.
- Her tespit işleminin sonucu anlık olarak ekranda gösterilir.

## Klasör Yapısı
![image](https://github.com/user-attachments/assets/b4de536e-41f4-46ce-9a56-8b87f80d6e4d)


## Notlar

- `model/`, `venv/` veya büyük dosyalar **.gitignore** ile hariç tutulmuştur.
- Kullanıcı ve plaka veritabanı `plakalar.db` içinde tutulur.
- Sadece temel kaynak kodları paylaşılmıştır; model dosyaları veya eğitim verisi repoya dahil değildir.

## Katkı ve Lisans

- Katkı sağlamak isterseniz, fork edip PR gönderebilirsiniz.
- [MIT Lisansı] ile lisanslanmıştır (lisans eklemediyseniz bu kısmı çıkarabilirsiniz).

---

**Geliştirici:**  
[FAZLIDDIN KHAMDAMOV](https://github.com/fazliddin-hamdam)



