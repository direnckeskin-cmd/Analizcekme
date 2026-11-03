import os
import streamlit as st
import pandas as pd
import numpy as np

# Sayfa Ayarları (Telefona Tam Uyumlu)
st.set_page_config(page_title="Oran Analiz Pro", page_icon="⚽", layout="centered")

# CSS Tasarımı (Tek Ekrana Sığması İçin Kompakt Boşluklar)
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stat-card { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; font-family: sans-serif; font-size: 11px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    </style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "ORAN ANALİZ TABLOSU.xlsb")
CACHE_PATH = os.path.join(BASE_DIR, "cache_data.pkl")

@st.cache_data(show_spinner=False)
def load_data():
    if os.path.exists(CACHE_PATH):
        try:
            return pd.read_pickle(CACHE_PATH)
        except Exception:
            pass
    
    try:
        try:
            df = pd.read_excel(EXCEL_PATH, engine='pyxlsb', header=1)
        except Exception:
            df = pd.read_excel(EXCEL_PATH, header=1)

        df['MS1'] = pd.to_numeric(df['MS1'], errors='coerce')
        df['MSX'] = pd.to_numeric(df['MSX'], errors='coerce')
        df['MS2'] = pd.to_numeric(df['MS2'], errors='coerce')
        df_clean = df.dropna(subset=['MS1', 'MSX', 'MS2', 'İY SKOR', 'MS SKOR']).copy()
        df_clean.to_pickle(CACHE_PATH)
        return df_clean
    except Exception as e:
        return None

st.markdown("<h2 style='text-align: center; color: #38bdf8; font-size: 18px; margin-bottom: 8px;'>⚽ ORAN ANALİZ VE PATTERN MOTORU</h2>", unsafe_allow_html=True)

with st.spinner("📊 Veriler yükleniyor..."):
    df_clean = load_data()

if df_clean is None:
    st.error("❌ Excel verisi yüklenemedi! Lütfen dosya yolunu kontrol edin.")
    st.stop()

# Lig Filtreleme
lig_kolonu = None
for col in ['ÜLKE / LİG', 'ÜLKE/LİG', 'LİG', 'LIG', 'Lig', 'Lig Adı']:
    if col in df_clean.columns:
        lig_kolonu = col
        break

if lig_kolonu:
    df_clean[lig_kolonu] = df_clean[lig_kolonu].astype(str).str.strip()
    tum_ligler = sorted(df_clean[lig_kolonu].dropna().unique().tolist())
    
    st.markdown("### 🏆 Lig Filtreleme")
    secilen_ligler = st.multiselect(
        "Analize dahil etmek istediğin ligleri seç (Boş bırakırsan hepsi taranır):",
        options=tum_ligler,
        default=tum_ligler
    )
    
    if secilen_ligler:
        df_clean = df_clean[df_clean[lig_kolonu].isin(secilen_ligler)]

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    ms1_input = st.text_input("MS 1", value="0")
with col2:
    msx_input = st.text_input("MS X", value="7.29")
with col3:
    ms2_input = st.text_input("MS 2", value="13.30")
with col4:
    tolerans_input = st.text_input("Tolerans", value="0.04")

tumunu_goster = st.checkbox("📋 Bulunan tüm maçları listede göster (20 sınırı olmasın)", value=False)
btn_analiz = st.button("ANALİZ ET 🚀", use_container_width=True, type="primary")

if btn_analiz:
    try:
        ms1_v = float(ms1_input.strip().replace(',', '.'))
        msx_v = float(msx_input.strip().replace(',', '.'))
        ms2_v = float(ms2_input.strip().replace(',', '.'))
        tol_v = float(tolerans_input.strip().replace(',', '.'))
    except ValueError:
        st.error("Lütfen tüm değerleri geçerli sayı olarak girin! (Kapalılar için 0 yazın)")
        st.stop()

    df_calc = df_clean.copy()
    
    fark_ms1 = (df_calc['MS1'] - ms1_v)**2 if ms1_v > 0 else 0
    fark_msx = (df_calc['MSX'] - msx_v)**2 if msx_v > 0 else 0
    fark_ms2 = (df_calc['MS2'] - ms2_v)**2 if ms2_v > 0 else 0
    
    df_calc['Mesafe'] = np.sqrt(fark_ms1 + fark_msx + fark_ms2)

    filtre = pd.Series(True, index=df_calc.index)
    if ms1_v > 0:
        filtre &= (df_calc['MS1'] >= ms1_v - tol_v) & (df_calc['MS1'] <= ms1_v + tol_v)
    if msx_v > 0:
        filtre &= (df_calc['MSX'] >= msx_v - tol_v) & (df_calc['MSX'] <= msx_v + tol_v)
    if ms2_v > 0:
        filtre &= (df_calc['MS2'] >= ms2_v - tol_v) & (df_calc['MS2'] <= ms2_v + tol_v)

    df_tolerans = df_calc[filtre].sort_values('Mesafe').copy()

    if not df_tolerans.empty:
        toplam_bulunan = len(df_tolerans)
        if tumunu_goster:
            benzerler = df_tolerans.copy()
            st.info(f"🔍 ±{tol_v} aralığında {toplam_bulunan} maç bulundu. Hepsi listeleniyor.")
        else:
            benzerler = df_tolerans.head(20).copy()
            st.info(f"🔍 ±{tol_v} aralığında {toplam_bulunan} maç bulundu. En yakın 20 tanesi listeleniyor.")
    else:
        st.warning(f"⚠️ Tam eşleşme bulunamadı. En yakın maçlar listeleniyor.")
        benzerler = df_calc.sort_values('Mesafe').head(20).copy()

def skor_ayir(s):
    try:
        p = str(s).strip().split('-')
        return int(p[0]), int(p[1])
    except:
        return 0, 0

if 'benzerler' in locals() and not benzerler.empty:
    benzerler[['iy_e', 'iy_d']] = benzerler['İY SKOR'].apply(lambda x: pd.Series(skor_ayir(x)))
    benzerler[['ms_e', 'ms_d']] = benzerler['MS SKOR'].apply(lambda x: pd.Series(skor_ayir(x)))

    benzerler['iy_toplam'] = benzerler['iy_e'] + benzerler['iy_d']
    benzerler['ms_toplam'] = benzerler['ms_e'] + benzerler['ms_d']
    benzerler['kg_var'] = (benzerler['ms_e'] > 0) & (benzerler['ms_d'] > 0)
    
    iy_kg_var = (benzerler['iy_e'] > 0) & (benzerler['iy_d'] > 0)
    ikinci_yari_e = benzerler['ms_e'] - benzerler['iy_e']
    ikinci_yari_d = benzerler['ms_d'] - benzerler['iy_d']
    ikinci_yari_kg_var = (ikinci_yari_e > 0) & (ikinci_yari_d > 0)
    
    benzerler['her_iki_yari_kg_var'] = iy_kg_var & ikinci_yari_kg_var

    def get_ht_ft(row):
        ht = '1' if row['iy_e'] > row['iy_d'] else ('2' if row['iy_d'] > row['iy_e'] else 'X')
        ft = '1' if row['ms_e'] > row['ms_d'] else ('2' if row['ms_d'] > row['ms_e'] else 'X')
        return f"{ht}/{ft}"

    benzerler['HT/FT'] = benzerler.apply(get_ht_ft, axis=1)

    toplam_mac = len(benzerler)
    iy_05 = round((benzerler['iy_toplam'] >= 1).mean() * 100)
    iy_15 = round((benzerler['iy_toplam'] >= 2).mean() * 100)
    ms_25 = round((benzerler['ms_toplam'] >= 3).mean() * 100)
    ms_35 = round((benzerler['ms_toplam'] >= 4).mean() * 100)
    ms_6plus_pct = round((benzerler['ms_toplam'] >= 6).mean() * 100)
    her_iki_yari_kg_pct = round(benzerler['her_iki_yari_kg_var'].mean() * 100)
    kg_v = round(benzerler['kg_var'].mean() * 100)

    # 1. ÜST İSTATİSTİK KARTI (2'Lİ YAN YANA - SIKIŞTIRILMIŞ)
    st.markdown(f"""
    <div style="display: flex; gap: 6px; margin-bottom: 4px;">
        <div class="stat-card" style="flex: 1; margin-bottom: 0;">
            <b>🟢 İY 0.5+</b> : %{iy_05} <span style="color:#9ca3af;">[60-90]</span><br>
            <b>🟢 İY 1.5+</b> : %{iy_15} <span style="color:#9ca3af;">[15-45]</span><br>
            <b>🔥 6+ GOL</b> : %{ms_6plus_pct} <span style="color:#f59e0b;">[SÜRPRİZ]</span><br>
            <b>🏆 KG VAR</b> : %{kg_v} <span style="color:#9ca3af;">[50-80]</span>
        </div>
        <div class="stat-card" style="flex: 1; margin-bottom: 0;">
            <b>🟢 MS 2.5+</b> : %{ms_25} <span style="color:#9ca3af;">[20-50]</span><br>
            <b>🟢 MS 3.5+</b> : %{ms_35} <span style="color:#9ca3af;">[5-35]</span><br>
            <b>⚡ İY/2Y KG</b> : %{her_iki_yari_kg_pct} <span style="color:#f59e0b;">[İKİ YARI]</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. İY VE MS SKOR TRENDLERİ (YAN YANA, 6'ŞAR SEÇENEK - SIKIŞTIRILMIŞ)
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #38bdf8; margin: 0 0 2px 0;'>📊 SKOR TRENDLERİ (ÖZET)</p>", unsafe_allow_html=True)
    
    iy_counts = benzerler['İY SKOR'].value_counts().head(6)
    ms_counts = benzerler['MS SKOR'].value_counts().head(6)
    
    iy_lines = [f"🟢 <b>{sk}:</b> {c} (%{int((c/toplam_mac)*100)})" for sk, c in iy_counts.items()]
    ms_lines = [f"🟢 <b>{sk}:</b> {c} (%{int((c/toplam_mac)*100)})" for sk, c in ms_counts.items()]

    st.markdown(f"""
    <div style="display: flex; gap: 6px; margin-bottom: 6px;">
        <div style="flex: 1; background-color: #111827; border: 1px solid #1f2c47; padding: 6px 8px; border-radius: 6px; font-size: 10px; font-family: sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <b style="color: #38bdf8;">⚽ İY SKOR</b><br>{"<br>".join(iy_lines)}
        </div>
        <div style="flex: 1; background-color: #111827; border: 1px solid #1f2c47; padding: 6px 8px; border-radius: 6px; font-size: 10px; font-family: sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <b style="color: #38bdf8;">⚽ MS SKOR</b><br>{"<br>".join(ms_lines)}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. KESİNLİKLE KAYMAYAN TERTEMİZ TERMINAL TABLO
    lines = []
    header_line = f"{'EV - DEPLASMAN':<22} | {'İY':<4} | {'MS':<4} | {'HT/FT'}"
    sep_line = "-" * 48

    lines.append(f"<span style='color:#00FF66;'><b>{header_line}</b></span>")
    lines.append(f"<span style='color:#00FF66;'>{sep_line}</span>")

    donus_sayisi = 0
    for _, row in benzerler.iterrows():
        ev = str(row.get('EV SAHİBİ', ''))[:10]
        dep = str(row.get('DEPLASMAN', ''))[:10]
        mac_adi = f"{ev}-{dep}".ljust(22)
        iy_s = str(row.get('İY SKOR', '')).ljust(4)
        ms_s = str(row.get('MS SKOR', '')).ljust(4)
        ht_ft = str(row.get('HT/FT', ''))
        ms_toplam = row['ms_toplam']

        is_donus = ht_ft in ['1/2', '2/1']
        is_6plus = ms_toplam >= 6
        is_1x = ht_ft == '1/X'
        is_2x = ht_ft == '2/X'

        if is_donus:
            donus_sayisi += 1
            ht_ft_disp = f"{ht_ft} 🔥"
        else:
            ht_ft_disp = ht_ft

        line_str = f"{mac_adi} | {iy_s} | {ms_s} | {ht_ft_disp}"
        
        renk = "#00FF66"
        font_weight = "normal"
        if is_6plus:
            renk = "#FF3333"
            font_weight = "bold"
        elif is_donus:
            renk = "#FF8C00"
            font_weight = "bold"
        elif is_1x:
            renk = "#FFD700"
            font_weight = "bold"
        elif is_2x:
            renk = "#00BFFF"
            font_weight = "bold"

        lines.append(f"<span style='color:{renk}; font-weight:{font_weight};'>{line_str}</span>")

    terminal_box = f"""
    <div style="background-color: #000000; padding: 8px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 10px; line-height: 1.3; white-space: pre; overflow-x: auto; border: 1px solid #222;">
    {"<br>".join(lines)}
    </div>
    """
    st.markdown(terminal_box, unsafe_allow_html=True)

    # Risk Bandı
    donus_orani = round((donus_sayisi / toplam_mac) * 100) if toplam_mac > 0 else 0
    if donus_orani >= 8 or donus_sayisi >= 2:
        uyari_mesaji = f"🚨 DİKKAT : Bu Oran Havuzu %{donus_orani} Oranında ({donus_sayisi} Maç) Maç İçi Ters Köşe (1/2 veya 2/1) Potansiyeli Taşıyor!"

        st.markdown(f"""
        <div style="background-color: #7f1d1d; color: #fca5a5; padding: 8px; border-radius: 6px; font-size: 11px; font-weight: bold; text-align: center; margin-top: 6px; border: 1px solid #991b1b;">
        {uyari_mesaji}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #064e3b; color: #6ee7b7; padding: 8px; border-radius: 6px; font-size: 11px; font-weight: bold; text-align: center; margin-top: 6px; border: 1px solid #065f46;">
        ✅ Oran Havuzu İstikrarlı Seyrediyor (Ters köşe riski düşük).
        </div>
        """, unsafe_allow_html=True)

else:
    if btn_analiz:
        st.warning("Lütfen analiz için geçerli oranlar girin.")
