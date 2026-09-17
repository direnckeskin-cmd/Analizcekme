import streamlit as st
import numpy as np
import pandas as pd
import time
import os

# --- STREAMLIT SAYFA AYARLARI ---
st.set_page_config(page_title="Derin Bülten Taraması", layout="wide")

# --- 1. TAKIM İSMİNİ BULMA FONKSİYONU ---
def takim_ismini_bul(row, index, is_home=True):
    olasi_sutunlar = (
        ['EV_TAKIM', 'Ev_Takim', 'Ev Sahibi', 'Home', 'Ev', 'EV', 'Takim_1']
        if is_home else
        ['DEP_TAKIM', 'Dep_Takim', 'Deplasman', 'Away', 'Dep', 'DEP', 'Takim_2']
    )
    for sutun in olasi_sutunlar:
        if sutun in row and pd.notna(row[sutun]) and str(row[sutun]).strip() != '':
            return str(row[sutun]).strip()
            
    return f"Ev_{index}" if is_home else f"Dep_{index}"


# --- STREAMLIT ARAYÜZÜ ---
st.title("🎯 Derin AI Bülten Analiz & Oran Taraması")

# Tolerans Slider'ı
tolerans = st.slider("Tolerans Aralığı (±)", min_value=0.01, max_value=0.10, value=0.03, step=0.01)

# Dosya Yükleyiciler (Klasörde hazır varsa otomatik de okur)
col1, col2 = st.columns(2)
with col1:
    bulten_file = st.file_uploader("📋 Bülten Dosyası (Excel/CSV)", type=["xlsx", "csv"])
with col2:
    gecmis_file = st.file_uploader("📚 Geçmiş Veri Dosyası (Excel/CSV)", type=["xlsx", "csv"])

# Taramayı Başlat Butonu
baslat_butonu = st.button(f"🚀 DERİN BÜLTEN TARAMASINI BAŞLAT", use_container_width=True, type="primary")

if baslat_butonu:
    # 1. Veri Yükleme Kontrolü
    bulten_df, gecmis_df = None, None

    # Kullanıcı dosya yüklediyse onu al, yoksa klasördeki varsayılan dosyaları ara
    if bulten_file:
        bulten_df = pd.read_excel(bulten_file) if bulten_file.name.endswith('.xlsx') else pd.read_csv(bulten_file)
    elif os.path.exists("bulten.xlsx"):
        bulten_df = pd.read_excel("bulten.xlsx")

    if gecmis_file:
        gecmis_df = pd.read_excel(gecmis_file) if gecmis_file.name.endswith('.xlsx') else pd.read_csv(gecmis_file)
    elif os.path.exists("gecmis.xlsx"):
        gecmis_df = pd.read_excel("gecmis.xlsx")

    if bulten_df is None or gecmis_df is None:
        st.error("❌ Lütfen Bülten ve Geçmiş Veri dosyalarını yükleyin veya GitHub ana dizinine 'bulten.xlsx' ve 'gecmis.xlsx' olarak ekleyin!")
    else:
        # 2. Hızlı Vektörel Tarama Motoru
        start_time = time.time()
        
        oran_sutunlari = []
        for aday in [['MS1', 'MSX', 'MS2'], ['MS_1', 'MS_X', 'MS_2'], ['1', 'X', '2']]:
            if all(col in bulten_df.columns for col in aday) and all(col in gecmis_df.columns for col in aday):
                oran_sutunlari = aday
                break

        if not oran_sutunlari:
            st.error("❌ Oran sütunları (MS1, MSX, MS2) dosyalarda bulunamadı!")
        else:
            bulten_oranlar = bulten_df[oran_sutunlari].to_numpy(dtype=float)
            gecmis_oranlar = gecmis_df[oran_sutunlari].to_numpy(dtype=float)

            grup1, grup3, grup5 = [], [], []
            toplam_bulten = len(bulten_df)

            for i in range(toplam_bulten):
                b_row = bulten_df.iloc[i]
                b_oran = bulten_oranlar[i]

                # Vektörel Hızlı Hesaplama
                farklar = np.abs(gecmis_oranlar - b_oran)
                eslesen_maske = np.all(farklar <= tolerans, axis=1)
                eslesen_maclar = gecmis_df[eslesen_maske]

                toplam_eslesme = len(eslesen_maclar)
                if toplam_eslesme < 5:
                    continue

                ev_adi = takim_ismini_bul(b_row, i, is_home=True)
                dep_adi = takim_ismini_bul(b_row, i, is_home=False)
                tarih = str(b_row.get('Tarih', b_row.get('TARİH', '20.09.2026')))

                # İstatistikler
                if 'IY_MS' in eslesen_maclar.columns:
                    donus_sayisi = eslesen_maclar['IY_MS'].isin(['1/2', '2/1']).sum()
                    donus_yuzde = int(round((donus_sayisi / toplam_eslesme) * 100))
                else:
                    donus_yuzde, donus_sayisi = 0, 0

                toplam_gol = eslesen_maclar.get('TOPLAM_GOL', eslesen_maclar.get('TG', pd.Series(dtype=float)))
                gol_6_yuzde = int(round(((toplam_gol >= 6).sum() / toplam_eslesme) * 100)) if len(toplam_gol) > 0 else 0
                ust_45_yuzde = int(round(((toplam_gol > 4.5).sum() / toplam_eslesme) * 100)) if len(toplam_gol) > 0 else 0
                ust_25_yuzde = int(round(((toplam_gol > 2.5).sum() / toplam_eslesme) * 100)) if len(toplam_gol) > 0 else 0

                kg_var = eslesen_maclar.get('KG', eslesen_maclar.get('KG_DURUM', pd.Series(dtype=str)))
                kg_var_yuzde = int(round(((kg_var == 'KG VAR').sum() / toplam_eslesme) * 100)) if len(kg_var) > 0 else 0

                oran_str = f"{b_oran[0]:.2f}-{b_oran[1]:.2f}-{b_oran[2]:.2f}"
                mac_etiketi = f"{tarih} | {ev_adi:<15} - {dep_adi:<15} | {oran_str}"

                if donus_yuzde >= 14:
                    grup1.append(f"{mac_etiketi} | 🚨 1/2-2/1: %{donus_yuzde} ({donus_sayisi}/{toplam_eslesme})")
                if gol_6_yuzde >= 20:
                    grup3.append(f"{mac_etiketi} | ⚽ 6+ Gol: %{gol_6_yuzde} | ⚽ 4.5+ Üst: %{ust_45_yuzde}")
                if ust_25_yuzde >= 80:
                    grup5.append(f"{mac_etiketi} | ⚽ 2.5+ Üst: %{ust_25_yuzde} | 💖 KG Var: %{kg_var_yuzde}")

            gecen_sure = round(time.time() - start_time, 2)

            # --- EKRANA BASMA (STREAMLIT YAZDIRMA) ---
            st.subheader("⚡ GRUP 1: 1/2 VE 2/1 SÜRPRİZ DÖNÜŞ BOMBALARI")
            if grup1:
                st.code("\n".join(grup1), language="text")
            else:
                st.info("Bu kriterde maç bulunamadı.")

            st.subheader("🔥 GRUP 3: 6+ GOL YAĞMURU SİNYALLERİ")
            if grup3:
                st.code("\n".join(grup3), language="text")
            else:
                st.info("Bu kriterde maç bulunamadı.")

            st.subheader("🎯 GRUP 5: 2.5+ ÜST & KG VAR YÜKSEK İHTİMAL MAÇLAR")
            if grup5:
                st.code("\n".join(grup5), language="text")
            else:
                st.info("Bu kriterde maç bulunamadı.")

            st.success(f"⚡ {toplam_bulten} Maçlık Derin AI Bülten Taraması {gecen_sure} Saniyede Başarıyla Tamamlandı!")
