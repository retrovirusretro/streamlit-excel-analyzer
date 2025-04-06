# streamlit-excel-analyzer
# 📊 Streamlit Excel Analiz Uygulaması

Bu uygulama, bir Excel dosyasını yükleyip temel analizler yapan ve sonuçları tekrar Excel çıktısı olarak sunan bir **Streamlit** projesidir.

## 🚀 Özellikler

- Excel dosyası yükleme (.xlsx)
- Yüklenen veriyi tablo olarak görüntüleme
- Her sütun için boş olmayan değer sayısını analiz etme
- İndirilebilir Excel çıktısı üretme

## 🛠 Gereksinimler

Aşağıdaki kütüphaneler gereklidir (requirements.txt dosyasında tanımlı):

- streamlit
- pandas
- openpyxl
- xlsxwriter

## ▶️ Uygulama Nasıl Çalıştırılır?

1. Bu repoyu klonlayın veya ZIP olarak indirin.
2. Ortamınızı kurun ve kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
