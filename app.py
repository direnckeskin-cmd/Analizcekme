import os
import streamlit as st
import pandas as pd
import numpy as np

# Sayfa Ayarları (Telefona Tam Uyumlu)
st.set_page_config(page_title="Oran Analiz Pro", page_icon="⚽", layout="centered")

# Mobil Dostu Şık CSS Tasarımı
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stat-card { background-color: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 15px; margin-bottom: 12px; font-family: sans-serif; font-size: 14px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .match-row { background-color: #0f172a; border-left: 4px solid #3b82f6; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 13px; font-family: sans-serif; }
    .match-row-signal { background-color: #1a150b; border-left: 4px solid #f59e0b; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px; font-size: 13px; font-family: sans-serif; }
    .trend-box { background-color: #111827; border: 1px solid #1f2c47; padding: 12px; border-radius: 8px; font-size: 13px; font-family: sans-serif; margin-bottom: 10px; }
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

st.markdown("<h2 style='text-align: center; color: #38bdf8; font-size: 22px; margin-bottom: 20px;'>⚽ ORAN ANALİZ VE PATTERN MOTORU</h2>", unsafe_allow_html=True)

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

    # ÜST İSTATİSTİKLER (Şık Kart Tasarımı)
    st.markdown(f"""
    <div class="stat-card">
        <b>🟢 İY 0.5+</b> &nbsp;:&nbsp; %{iy_05} &nbsp;&nbsp;<span style="color:#9ca3af;">[60-90]</span><br>
        <b>🟢 İY 1.5+</b> &nbsp;:&nbsp; %{iy_15} &nbsp;&nbsp;<span style="color:#9ca3af;">[15-45]</span><br>
        <b>🟢 MS 2.5+</b> &nbsp;:&nbsp; %{ms_25} &nbsp;&nbsp;<span style="color:#9ca3af;">[20-50]</span><br>
        <b>🟢 MS 3.5+</b> &nbsp;:&nbsp; %{ms_35} &nbsp;&nbsp;<span style="color:#9ca3af;">[5-35]</span><br>
        <b>🔥 6+ GOL</b> &nbsp;&nbsp;&nbsp;:&nbsp; %{ms_6plus_pct} &nbsp;&nbsp;<span style="color:#f59e0b;">[SÜRPRİZ]</span><br>
        <b>⚡ İY/2Y KG</b> &nbsp;:&nbsp; %{her_iki_yari_kg_pct} &nbsp;&nbsp;<span style="color:#f59e0b;">[HER İKİ YARI]</span><br>
        <b>🏆 KG VAR</b> &nbsp;&nbsp;&nbsp;:&nbsp; %{kg_v} &nbsp;&nbsp;<span style="color:#9ca3af;">[50-80]</span>
    </div>
    """, unsafe_allow_html=True)

    # Maç Listesi (Alt alta temiz kartlar şeklinde, sağa kaydırma derdi yok)
    st.markdown("---")
    st.markdown("### 📋 Benzer Maç Havuzu")

    donus_sayisi = 0
    for _, row in benzerler.iterrows():
        tarih = str(row.get('SEZON', ''))[:16]
        ev = str(row.get('EV SAHİBİ', ''))
        dep = str(row.get('DEPLASMAN', ''))
        iy_s = str(row.get('İY SKOR', ''))
        ms_s = str(row.get('MS SKOR', ''))
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

        # Renk ve stil ayarları
        row_class = "match-row-signal" if (is_donus or is_6plus) else "match-row"
        renk = "#34d399" # Yeşil varsayılan
        if is_6plus: renk = "#f87171" # Kırmızı
        elif is_donus: renk = "#fbbf24" # Turuncu
        elif is_1x: renk = "#facc15" # Sarı
        elif is_2x: renk = "#38bdf8" # Mavi

        match_card_html = f"""
        <div class="{row_class}">
            <div style="color: #94a3b8; font-size: 11px; margin-bottom: 2px;">{tarih}</div>
            <div style="font-weight: bold; color: #ffffff; font-size: 14px; margin-bottom: 4px;">{ev} vs {dep}</div>
            <div style="display: flex; justify-content: space-between; color: {renk}; font-weight: bold;">
                <span>İY: {iy_s} &nbsp;|&nbsp; MS: {ms_s}</span>
                <span>HT/FT: {ht_ft_disp}</span>
            </div>
        </div>
        """
        st.markdown(match_card_html, unsafe_allow_html=True)

    # Skor Trendleri
    st.markdown("---")
    st.subheader("📊 Skor Trendleri")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("##### ⚽ İY SKOR")
        iy_counts = benzerler['İY SKOR'].value_counts().head(6)
        iy_trend_lines = []
        for skor, count in iy_counts.items():
            pct = (count / toplam_mac) * 100
            iy_trend_lines.append(f"🟢 <b>{skor}</b> : {count} Maç (%{pct:.0f})")
        iy_html = "<br>".join(iy_trend_lines)
        st.markdown(f"<div class='trend-box'>{iy_html}</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown("##### ⚽ MS SKOR")
        ms_counts = benzerler['MS SKOR'].value_counts().head(8)
        ms_trend_lines = []
        for skor, count in ms_counts.items():
            pct = (count / toplam_mac) * 100
            ms_trend_lines.append(f"🟢 <b>{skor}</b> : {count} Maç (%{pct:.0f})")
        ms_html = "<br>".join(ms_trend_lines)
        st.markdown(f"<div class='trend-box'>{ms_html}</div>", unsafe_allow_html=True)

    # Risk Bandı
    donus_orani = round((donus_sayisi / toplam_mac) * 100) if toplam_mac > 0 else 0
    if donus_orani >= 8 or donus_sayisi >= 2:
        uyari_mesaji = f"🚨 DİKKAT : Bu Oran Havuzu %{donus_orani} Oranında ({donus_sayisi} Maç) Maç İçi Ters Köşe (1/2 veya 2/1) Potansiyeli Taşıyor!"

        st.markdown(f"""
        <div style="background-color: #7f1d1d; color: #fca5a5; padding: 12px; border-radius: 8px; font-size: 13px; font-weight: bold; text-align: center; margin-top: 15px; border: 1px solid #991b1b;">
        {uyari_mesaji}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #064e3b; color: #6ee7b7; padding: 12px; border-radius: 8px; font-size: 13px; font-weight: bold; text-align: center; margin-top: 15px; border: 1px solid #065f46;">
        ✅ Oran Havuzu İstikrarlı Seyrediyor (Ters köşe riski düşük).
        </div>
        """, unsafe_allow_html=True)

else:
    if btn_analiz:
        st.warning("Lütfen analiz için geçerli oranlar girin.")
