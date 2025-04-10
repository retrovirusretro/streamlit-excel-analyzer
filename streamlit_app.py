
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
from datetime import datetime
import math

st.set_page_config(page_title="Transfer Öneri Uygulaması", layout="wide")
st.title("📦 Google Sheets Tabanlı Transfer Önerisi")

# Gerekli girişler
sheet_url = st.text_input("🔗 Google Sheets bağlantısını buraya yapıştırın:")
json_file = st.file_uploader("🔐 Google Service Account JSON dosyasını yükleyin", type=["json"])

if sheet_url and json_file:
    try:
        # Yetkilendirme ve bağlantı
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(json_file.name, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(sheet_url)

        # Sayfaları oku
        df_data = pd.DataFrame(spreadsheet.worksheet("Veri").get_all_records())
        df_regions = pd.DataFrame(spreadsheet.worksheet("Bölgeler").get_all_records())

        # Kolon isimlerini normalize et
        df_data.rename(columns={
            "Ürün Hiyerarşisi - LotKodu": "LotKodu",
            "Ürün Hiyerarşisi - LotAdi": "LotAdi",
            "Ürün Hiyerarşisi - AileAdı": "Aile Adı",
            "Ürün Hiyerarşisi - KategoriAdı": "Kategori Adı",
            "Ürün Hiyerarşisi - AltKategoriAdı": "Alt Kategori Adı"
        }, inplace=True)

        # Mağaza bilgilerini ana veriye ekle
        df = pd.merge(df_data, df_regions, on="DepoAdı", how="left")

        # Eksik stok düzeltme: stok negatif ve satış varsa stok = abs(stok)
        df.loc[(df["Mgz Stok Ad."] < 0) & (df["Satış Ad."] > 0), "Mgz Stok Ad."] = df["Mgz Stok Ad."].abs()

        # Satış kolonunu tamamlama
        df["Satış Ad."] = df["Satış Ad."].fillna(0)
        df["Tahmini Satış"] = df["Satış Ad."]
        df.loc[df["Tahmini Satış"] <= 0, "Tahmini Satış"] = df["Önceki Hafta Satış Miktar"]
        df.loc[df["Tahmini Satış"].isna() | (df["Tahmini Satış"] <= 0), "Tahmini Satış"] = df["Önceki Ay Satış Miktar"] / 4
        df["Tahmini Satış"] = df["Tahmini Satış"].fillna(0)

        # Yeni Cover hesapla
        df["Mag. S/S"] = df["Mgz Stok Ad."] / (df["Tahmini Satış"] + 1)

        # Analiz Tarihi
        today = datetime.today().strftime('%Y-%m-%d')
        transfer_list = []

        for lot_kodu, group in df.groupby("LotKodu"):
            for il in group["İl"].unique():
                il_group = group[group["İl"] == il]
                avg_cover = il_group["Mag. S/S"].mean()
                donors = il_group[(il_group["Mag. S/S"] > avg_cover) & (il_group["Mag. S/S"] > 10) & (il_group["Mgz Stok Ad."] >= 10)].copy()
                receivers = il_group[(il_group["Mag. S/S"] < avg_cover) & (il_group["Mag. S/S"] < 5) & (il_group["Stok Rezerve Ad."] == 0)].copy()

                donor_stok = donors.set_index("DepoAdı")["Mgz Stok Ad."].to_dict()
                receiver_stok = receivers.set_index("DepoAdı")["Mgz Stok Ad."].to_dict()

                for _, donor in donors.iterrows():
                    donor_name = donor["DepoAdı"]
                    for _, receiver in receivers.iterrows():
                        receiver_name = receiver["DepoAdı"]
                        if donor_name == receiver_name:
                            continue

                        donor_current_stock = donor_stok.get(donor_name, 0)
                        receiver_current_stock = receiver_stok.get(receiver_name, 0)

                        max_transfer = int(receiver["Tahmini Satış"] * 2)
                        proposed_qty = math.floor(donor_current_stock / 2)
                        transfer_qty = min(proposed_qty, max_transfer)

                        if transfer_qty <= 0 or (donor_current_stock - transfer_qty) < 10:
                            continue

                        new_donor_stock = donor_current_stock - transfer_qty
                        new_receiver_stock = receiver_current_stock + transfer_qty

                        donor_final_cover = new_donor_stock / (donor["Tahmini Satış"] + 1)
                        receiver_final_cover = new_receiver_stock / (receiver["Tahmini Satış"] + 1)

                        transfer_list.append({
                            "Analiz Tarihi": today,
                            "İl": il,
                            "Ürün Kodu": lot_kodu,
                            "Ürün Adı": donor["LotAdi"],
                            "Aile Adı": donor["Aile Adı"],
                            "Kategori Adı": donor["Kategori Adı"],
                            "Alt Kategori Adı": donor["Alt Kategori Adı"],
                            "Transfer Adedi": transfer_qty,
                            "Gönderen Mağaza": donor_name,
                            "Gönderen Stok (önce)": donor_current_stock,
                            "Gönderen Cover (önce)": round(donor["Mag. S/S"], 2),
                            "Gönderen Final Cover": round(donor_final_cover, 2),
                            "Alan Mağaza": receiver_name,
                            "Alan Stok (önce)": receiver_current_stock,
                            "Alan Cover (önce)": round(receiver["Mag. S/S"], 2),
                            "Alan Final Cover": round(receiver_final_cover, 2),
                            "Transfer Yönü": f"{donor_name} → {receiver_name}"
                        })

                        donor_stok[donor_name] = new_donor_stock
                        receiver_stok[receiver_name] = new_receiver_stock

        transfer_df = pd.DataFrame(transfer_list)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            transfer_df.to_excel(writer, sheet_name="Transfer Önerileri", index=False)
        output.seek(0)

        st.success("Transfer önerileri başarıyla oluşturuldu!")
        st.download_button(
            label="📥 Excel Raporunu İndir",
            data=output,
            file_name="transfer_raporu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.dataframe(transfer_df.head(20))

    except Exception as e:
        st.error(f"Hata oluştu: {e}")
else:
    st.info("Google Sheets bağlantısını ve JSON dosyasını girerek başlayabilirsiniz.")
