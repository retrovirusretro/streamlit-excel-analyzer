import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import math

st.set_page_config(page_title="Transfer Öneri Uygulaması", layout="wide")
st.title("📦 Mağazalar Arası Transfer Önerisi")

uploaded_file = st.file_uploader("Excel dosyasını yükleyin", type=[".xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df_filtered = df[df["Mag. S/S"] > 0].copy()
    df_filtered = df_filtered[df_filtered["Mgz Stok Ad."] > 0]
    df_filtered["Stok Rezerve Ad."] = df_filtered["Stok Rezerve Ad."].fillna(0)

    today = datetime.today().strftime('%Y-%m-%d')
    transfer_list = []

    for lot_kodu, group in df_filtered.groupby("LotKodu"):
        avg_cover = group["Mag. S/S"].mean()
        donors = group[(group["Mag. S/S"] > avg_cover) & (group["Mgz Stok Ad."] >= 10)].copy()
        receivers = group[(group["Mag. S/S"] < avg_cover) & (group["Stok Rezerve Ad."] == 0)].copy()

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
                if donor_current_stock < 10:
                    continue
                max_transfer = int(receiver["Satış Ad."] * 2)
                proposed_qty = math.floor(donor_current_stock / 2)
                transfer_qty = min(proposed_qty, max_transfer)
                if transfer_qty <= 0:
                    continue
                new_donor_stock = donor_current_stock - transfer_qty
                new_receiver_stock = receiver_current_stock + transfer_qty
                donor_final_cover = new_donor_stock / (donor["Satış Ad."] + 1)
                receiver_final_cover = new_receiver_stock / (receiver["Satış Ad."] + 1)

                transfer_list.append({
                    "Analiz Tarihi": today,
                    "Ürün Kodu": lot_kodu,
                    "Ürün Adı": donor["LotAdi"],
                    "Transfer Adedi": transfer_qty,
                    "Gönderen Mağaza": donor_name,
                    "Gönderen Stok (önce)": donor_current_stock,
                    "Gönderen Cover (önce)": round(donor["Mag. S/S"], 2),
                    "Gönderen Final Cover": round(donor_final_cover, 2),
                    "Gönderen YTD Satış": donor["YTD Satış Ad."],
                    "Alan Mağaza": receiver_name,
                    "Alan Stok (önce)": receiver_current_stock,
                    "Alan Cover (önce)": round(receiver["Mag. S/S"], 2),
                    "Alan Final Cover": round(receiver_final_cover, 2),
                    "Alan YTD Satış": receiver["YTD Satış Ad."],
                    "Transfer Yönü": f"{donor_name} → {receiver_name}"
                })
                donor_stok[donor_name] = new_donor_stock
                receiver_stok[receiver_name] = new_receiver_stock

    transfer_df = pd.DataFrame(transfer_list)

    if not transfer_df.empty:
        summary_data = {
            "Analiz Tarihi": [today],
            "Toplam Ürün Sayısı": [transfer_df["Ürün Kodu"].nunique()],
            "Toplam Transfer Sayısı": [len(transfer_df)],
            "Toplam Transfer Adedi": [transfer_df["Transfer Adedi"].sum()],
            "Gönderen Mağaza Sayısı": [transfer_df["Gönderen Mağaza"].nunique()],
            "Alan Mağaza Sayısı": [transfer_df["Alan Mağaza"].nunique()]
        }
        summary_df = pd.DataFrame(summary_data)
        top_donors = transfer_df.groupby("Gönderen Mağaza")["Transfer Adedi"].sum().sort_values(ascending=False).head(5).reset_index()
        top_donors.columns = ["Mağaza", "Gönderilen Toplam Adet"]
        top_receivers = transfer_df.groupby("Alan Mağaza")["Transfer Adedi"].sum().sort_values(ascending=False).head(5).reset_index()
        top_receivers.columns = ["Mağaza", "Alınan Toplam Adet"]
        top_products = transfer_df.groupby(["Ürün Kodu", "Ürün Adı"])["Transfer Adedi"].sum().sort_values(ascending=False).head(5).reset_index()
        top_products.columns = ["Ürün Kodu", "Ürün Adı", "Toplam Transfer Adedi"]
    else:
        summary_df = pd.DataFrame()
        top_donors = pd.DataFrame()
        top_receivers = pd.DataFrame()
        top_products = pd.DataFrame()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        transfer_df.to_excel(writer, sheet_name="Transfer Önerileri", index=False)
        summary_df.to_excel(writer, sheet_name="Yönetici Özeti", index=False, startrow=0)
        top_donors.to_excel(writer, sheet_name="Yönetici Özeti", index=False, startrow=5)
        top_receivers.to_excel(writer, sheet_name="Yönetici Özeti", index=False, startrow=12)
        top_products.to_excel(writer, sheet_name="Yönetici Özeti", index=False, startrow=19)
    output.seek(0)

    st.success("Transfer önerileri başarıyla oluşturuldu!")
    st.download_button(
        label="📥 Excel Raporunu İndir",
        data=output,
        file_name="transfer_raporu_ve_ozet.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.subheader("📋 Örnek Transfer Tablosu")
    st.dataframe(transfer_df.head(20))
else:
    st.info("Başlamak için bir dosya yükleyin.")

