import streamlit as st
import pandas as pd
import numpy as np
import os

# Sayfa Ayarları (Telefona Tam Uyumlu)
st.set_page_config(page_title="Oran Analiz Pro", page_icon="⚽", layout="centered")

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

st.markdown("<h2 style='text-align: center; color: #00FF7F;'>⚽ ORAN ANALİZ VE PATTERN MOTORU</h2>", unsafe_allow_html=True)

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
    ms1_input = st.text_input("MS 1 Oranı", value="3.04")
with col2:
    msx_input = st.text_input("MS X Oranı", value="2.84")
with col3:
    ms2_input = st.text_input("MS 2 Oranı", value="2.02")
with col4:
    tolerans_input = st.text_input("Tolerans (±)", value="0.03")

tumunu_goster = st.checkbox("📋 Bulunan tüm maçları listede göster (20 sınırı olmasın)", value=False)
btn_analiz = st.button("ANALİZ ET 🚀", use_container_width=True, type="primary")

if btn_analiz:
    try:
        ms1_v = float(ms1_input.strip().replace(',', '.'))
        msx_v = float(msx_input.strip().replace(',', '.'))
        ms2_v = float(ms2_input.strip().replace(',', '.'))
        tol_v = float(tolerans_input.strip().replace(',', '.'))
    except ValueError:
        st.error("Lütfen tüm değerleri geçerli sayı olarak girin! (Örn: 1.85 / 0.03)")
        st.stop()

    df_calc = df_clean.copy()
    df_calc['Mesafe'] = np.sqrt(
        (df_calc['MS1'] - ms1_v)**2 + 
        (df_calc['MSX'] - msx_v)**2 + 
        (df_calc['MS2'] - ms2_v)**2
    )

    filtre = (
        (df_calc['MS1'] >= ms1_v - tol_v) & (df_calc['MS1'] <= ms1_v + tol_v) &
        (df_calc['MSX'] >= msx_v - tol_v) & (df_calc['MSX'] <= msx_v + tol_v) &
        (df_calc['MS2'] >= ms2_v - tol_v) & (df_calc['MS2'] <= ms2_v + tol_v)
    )
    df_tolerans = df_calc[filtre].sort_values('Mesafe').copy()

    if not df_tolerans.empty:
        toplam_bulunan = len(df_tolerans)
        if tumunu_goster:
            benzerler = df_tolerans.copy()
            st.info(f"🔍 ±{tol_v} tolerans aralığında {toplam_bulunan} maç bulundu. Tüm maçlar listeleniyor.")
        else:
            benzerler = df_tolerans.head(20).copy()
            st.info(f"🔍 ±{tol_v} tolerans aralığında {toplam_bulunan} maç bulundu. En yakın 20 tanesi listeleniyor.")
    else:
        st.warning(f"⚠️ ±{tol_v} tolerans aralığında tam eşleşme bulunamadı. En yakın maçlar listeleniyor.")
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
    kg_v = round(benzerler['kg_var'].mean() * 100)

    # X Biçimli Üst İstatistik Alanı
    istatistik_text = f"""
    🟢 İY 0.5+ : % {iy_05:<2}  [60-90]
    🟢 İY 1.5+ : % {iy_15:<2}  [15-45]
    🟢 MS 2.5+ : % {ms_25:<2}  [20-50]
    🟢 MS 3.5+ : % {ms_35:<2}  [5-35]
    🏆 KG VAR  : % {kg_v:<2}  [50-80]
    """
    st.markdown(f"""
    <div style="background-color: #000000; padding: 12px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 12px; color: #00FF66; border: 1px solid #222; overflow-x: auto;">
    <pre style="margin:0; background:none; color:#00FF66;">{istatistik_text}</pre>
    </div>
    """, unsafe_output_allow=True if hasattr(st, 'markdown') else None, unsafe_allow_html=True)

    # X Formatına Birebir Uyarlanmış Maç Tablosu
    st.markdown("---")
    lines = []
    header_line = f"{'TARİH':<10} | {'EV SAHİBİ':<16} | {'DEPLASMAN':<16} | {'İY':<4} | {'MS':<4} | {'HT/FT'}"
    sep_line = "-" * 72

    lines.append(f"<span style='color:#00FF66;'>{header_line}</span>")
    lines.append(f"<span style='color:#00FF66;'>{sep_line}</span>")

    donus_sayisi = 0
    for _, row in benzerler.iterrows():
        # Tarih kolonunu güvenli çekme
        tarih_val = str(row.get('SEZON', ''))
        tarih = tarih_val[:10] if len(tarih_val) >= 10 else f"{tarih_val:<10}"[:10]
        
        ev = str(row.get('EV SAHİBİ', ''))[:15].ljust(15)
        dep = str(row.get('DEPLASMAN', ''))[:15].ljust(15)
        iy_s = str(row.get('İY SKOR', ''))
        ms_s = str(row.get('MS SKOR', ''))
        ht_ft = str(row.get('HT/FT', ''))

        is_donus = ht_ft in ['1/2', '2/1']
        if is_donus:
            donus_sayisi += 1
            ht_ft_disp = f"{ht_ft} 🔥"
        else:
            ht_ft_disp = ht_ft

        line_str = f"{tarih:<10} | {ev} | {dep} | {iy_s:<4} | {ms_s:<4} | {ht_ft_disp:<7}"
        
        if is_donus:
            lines.append(f"<span style='color:#FF8C00; font-weight:bold;'>{line_str}</span>")
        else:
            lines.append(f"<span style='color:#00FF66;'>{line_str}</span>")

    terminal_box = f"""
    <div style="background-color: #000000; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 11px; line-height: 1.4; white-space: pre; overflow-x: auto; border: 1px solid #222;">
    {"<br>".join(lines)}
    </div>
    """
    st.markdown(terminal_box, unsafe_allow_html=True)

    # Skor Trendleri
    st.markdown("---")
    st.subheader("📊 Skor Trendleri")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("##### ⚽ İY SKOR TRENDİ")
        iy_counts = benzerler['İY SKOR'].value_counts().head(6)
        iy_trend_lines = []
        for skor, count in iy_counts.items():
            pct = (count / toplam_mac) * 100
            iy_trend_lines.append(f"🟢 {skor:<5} : {count} Maç (%{pct:.0f})")
        st.markdown(f"<div style='background:#0b0b0b; padding:10px; border-radius:6px; font-family:monospace; font-size:12px; color:#00FF66;'>{'<br>'.join(iy_trend_lines)}</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown("##### ⚽ MS SKOR TRENDİ (İLK 8)")
        ms_counts = benzerler['MS SKOR'].value_counts().head(8)
        ms_trend_lines = []
        for skor, count in ms_counts.items():
            pct = (count / toplam_mac) * 100
            ms_trend_lines.append(f"🟢 {skor:<5} : {count} Maç (%{pct:.0f})")
        st.markdown(f"<div style='background:#0b0b0b; padding:10px; border-radius:6px; font-family:monospace; font-size:12px; color:#00FF66;'>{'<br>'.join(ms_trend_lines)}</div>", unsafe_allow_html=True)

    # Risk Bandı
    donus_orani = round((donus_sayisi / toplam_mac) * 100) if toplam_mac > 0 else 0
    if donus_orani >= 15:
        uyari_mesaji = f"🚨 DİKKAT : Bu Oran Havuzu %{donus_orani} Oranında Maç İçi Ters Köşe (1/2 veya 2/X) Potansiyeli Taşıyor!"
        st.markdown(f"""
        <div style="background-color: #8B0000; color: #FFFFFF; padding: 10px 15px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 13px; font-weight: bold; text-align: center; margin-top: 15px;">
        {uyari_mesaji}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #004d1a; color: #00FF66; padding: 10px 15px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 13px; font-weight: bold; text-align: center; margin-top: 15px;">
        ✅ Oran Havuzu İstikrarlı Seyrediyor (Ters köşe riski düşük).
        </div>
        """, unsafe_allow_html=True)

else:
    if btn_analiz:
        st.warning("Lütfen analiz için geçerli oranlar girin.")
