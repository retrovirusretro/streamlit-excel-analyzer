
# Bu kod sadece Streamlit ortamında çalıştırılabilir.
# Lütfen streamlit yüklü bir ortamda çalıştırın (örneğin: local python environment, streamlit.io veya Codespaces).

try:
    import streamlit as st
    import pandas as pd
    from io import BytesIO

    st.set_page_config(page_title="Excel Veri Analizi", layout="centered")
    st.title("📊 Excel Dosyası Analiz Uygulaması")

    uploaded_file = st.file_uploader("Lütfen bir Excel dosyası yükleyin", type=[".xlsx"])

    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.subheader("Yüklenen Veri")
        st.dataframe(df)

        # Örnek analiz: her sütunun boş olmayan değer sayısı
        st.subheader("🔍 Örnek Analiz")
        analysis = df.count().reset_index()
        analysis.columns = ["Kolon", "Boş Olmayan Değer Sayısı"]
        st.dataframe(analysis)

        # Excel çıktısını hazırlama
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Orijinal Veri')
            analysis.to_excel(writer, index=False, sheet_name='Analiz')
        output.seek(0)

        st.download_button(
            label="📥 Excel Çıktısını İndir",
            data=output,
            file_name="analiz_sonuclari.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Başlamak için bir dosya yükleyin.")

except ModuleNotFoundError:
    print("HATA: Bu kod yalnızca Streamlit yüklü bir ortamda çalıştırılabilir. Lütfen 'pip install streamlit' komutuyla yüklemeyi deneyin.")
