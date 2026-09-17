import streamlit as st
import numpy as np
import pandas as pd
import time
import os

st.set_page_config(page_title="Derin Bülten Taraması", layout="wide")

# --- ORANLARI GÜVENLİ SAYIYA ÇEVİRME (VİRGÜL SAVAR) ---
def oranlari_temizle(df, sutunlar):
    for col in sutunlar:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    return df

# --- SÜTUN İSİMLERİNİ ESNEK YAKALAMA ---
def oran_sutunlarini_bul(df):
    sutun_haritası = {str(c).strip().upper(): c for c in df.columns}
    adaylar = [
        ['MS1', 'MSX', 'MS2'],
        ['MS_1', 'MS_X', 'MS_2'],
        ['1', 'X', '2'],
        ['MS 1', 'MS X', 'MS 2']
    ]
    for aday in adaylar:
        if all(c in sutun_haritası for c in aday):
            return [sutun_haritası[c] for c in aday]
    return None

def takim_ismini_bul(row, index, is_home=True):
    olasi_sutunlar = (
        ['EV_TAKIM', 'EV_TAKIM ', 'Ev_Takim', 'Ev Sahibi', 'Home', 'Ev', 'EV', 'Takim_1']
        if is_home else
        ['DEP_TAKIM', 'DEP_TAKIM ', 'Dep_Takim', 'Deplasman', 'Away', 'Dep', 'DEP', 'Takim_2']
    )
    for sutun in olasi_sutunlar:
        if sutun in row and pd.notna(row[sutun]) and str(row[sutun]).strip() != '':
            return str(row[sutun]).strip()
    return f"Ev_{index}" if is_home else f"Dep_{index}"

def dosya_oku(uploaded_file, default_name):
    if uploaded_file is not None:
        name = uploaded_file.name.lower()
        if name.endswith('.xlsb'):
            return pd.read_excel(uploaded_file, engine='pyxlsb')
        elif name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)
        else:
            return pd.read_csv(uploaded_file)
    elif os.path.exists(default_name):
        return pd.read_excel(default_name)
    return None

# --- STREAMLIT ARAYÜZÜ ---
st.title("🎯 Derin AI Bülten Analiz & Oran Taraması")

tolerans = st.slider("Tolerans Aralığı (±)", min_value=0.01, max_value=0.10, value=0.03, step=0.01)

col1, col2 = st.columns(2)
with col1:
    bulten_file = st.file_uploader("📋 Bülten Dosyası (Excel/CSV/XLSB)", type=["xlsx", "csv", "xlsb"])
with col2:
    gecmis_file = st.file_uploader("📚 Geçmiş Veri Dosyası (Excel/CSV/XLSB)", type=["xlsx", "csv", "xlsb"])

baslat_butonu = st.button("🚀 DERİN BÜLTEN TARAMASINI BAŞLAT", use_container_width=True, type="primary")

if baslat_butonu:
    try:
        with st.spinner("⏳ 16.7 MB'lık geçmiş veri dosyası okunuyor ve matrisler hazırlanıyor... Lütfen bekleyin..."):
            bulten_df = dosya_oku(bulten_file, "bulten.xlsx")
            gecmis_df = dosya_oku(gecmis_file, "gecmis.xlsx")

        if bulten_df is None or gecmis_df is None:
            st.error("❌ Lütfen her iki dosyayı da yükleyin!")
        else:
            with st.spinner("⚡ Vektörel oran taraması yapılıyor..."):
                start_time = time.time()
                
                bulten_oran_cols = oran_sutunlarini_bul(bulten_df)
                gecmis_oran_cols = oran_sutunlarini_bul(gecmis_df)

                if not bulten_oran_cols or not gecmis_oran_cols:
                    st.error("❌ Oran sütunları (MS1, MSX, MS2) dosyalardan birinde tespit edilemedi!")
                else:
                    # Virgüllü oranları noktaya çevirip sayı yap
                    bulten_df = oranlari_temizle(bulten_df, bulten_oran_cols)
                    gecmis_df = oranlari_temizle(gecmis_df, gecmis_oran_cols)

                    bulten_oranlar = bulten_df[bulten_oran_cols].to_numpy(dtype=float)
                    gecmis_oranlar = gecmis_df[gecmis_oran_cols].to_numpy(dtype=float)

                    grup1, grup3, grup5 = [], [], []
                    toplam_bulten = len(bulten_df)

                    for i in range(toplam_bulten):
                        b_row = bulten_df.iloc[i]
                        b_oran = bulten_oranlar[i]

                        # NaN oran varsa atla
                        if np.isnan(b_oran).any():
                            continue

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
                        iy_ms_col = [c for c in eslesen_maclar.columns if str(c).strip().upper() in ['IY_MS', 'İY_MS', 'IY/MS']]
                        if iy_ms_col:
                            donus_sayisi = eslesen_maclar[iy_ms_col[0]].isin(['1/2', '2/1']).sum()
                            donus_yuzde = int(round((donus_sayisi / toplam_eslesme) * 100))
                        else:
                            donus_yuzde, donus_sayisi = 0, 0

                        gol_col = [c for c in eslesen_maclar.columns if str(c).strip().upper() in ['TOPLAM_GOL', 'TG', 'GOL']]
                        if gol_col:
                            toplam_gol = pd.to_numeric(eslesen_maclar[gol_col[0]], errors='coerce')
                            gol_6_yuzde = int(round(((toplam_gol >= 6).sum() / toplam_eslesme) * 100))
                            ust_45_yuzde = int(round(((toplam_gol > 4.5).sum() / toplam_eslesme) * 100))
                            ust_25_yuzde = int(round(((toplam_gol > 2.5).sum() / toplam_eslesme) * 100))
                        else:
                            gol_6_yuzde, ust_45_yuzde, ust_25_yuzde = 0, 0, 0

                        kg_col = [c for c in eslesen_maclar.columns if str(c).strip().upper() in ['KG', 'KG_DURUM', 'KG_VAR']]
                        if kg_col:
                            kg_var = eslesen_maclar[kg_col[0]].astype(str).str.upper()
                            kg_var_yuzde = int(round(((kg_var == 'KG VAR').sum() / toplam_eslesme) * 100))
                        else:
                            kg_var_yuzde = 0

                        oran_str = f"{b_oran[0]:.2f}-{b_oran[1]:.2f}-{b_oran[2]:.2f}"
                        mac_etiketi = f"{tarih} | {ev_adi:<15} - {dep_adi:<15} | {oran_str}"

                        if donus_yuzde >= 14:
                            grup1.append(f"{mac_etiketi} | 🚨 1/2-2/1: %{donus_yuzde} ({donus_sayisi}/{toplam_eslesme})")
                        if gol_6_yuzde >= 20:
                            grup3.append(f"{mac_etiketi} | ⚽ 6+ Gol: %{gol_6_yuzde} | ⚽ 4.5+ Üst: %{ust_45_yuzde}")
                        if ust_25_yuzde >= 80:
                            grup5.append(f"{mac_etiketi} | ⚽ 2.5+ Üst: %{ust_25_yuzde} | 💖 KG Var: %{kg_var_yuzde}")

                    gecen_sure = round(time.time() - start_time, 2)

                    st.subheader("⚡ GRUP 1: 1/2 VE 2/1 SÜRPRİZ DÖNÜŞ BOMBALARI")
                    st.code("\n".join(grup1) if grup1 else "Bu kriterde maç bulunamadı.", language="text")

                    st.subheader("🔥 GRUP 3: 6+ GOL YAĞMURU SİNYALLERİ")
                    st.code("\n".join(grup3) if grup3 else "Bu kriterde maç bulunamadı.", language="text")

                    st.subheader("🎯 GRUP 5: 2.5+ ÜST & KG VAR YÜKSEK İHTİMAL MAÇLAR")
                    st.code("\n".join(grup5) if grup5 else "Bu kriterde maç bulunamadı.", language="text")

                    st.success(f"⚡ {toplam_bulten} Maçlık Derin AI Bülten Taraması {gecen_sure} Saniyede Başarıyla Tamamlandı!")

    except Exception as e:
        st.error(f"❌ İşlem sırasında bir hata oluştu: {str(e)}")
