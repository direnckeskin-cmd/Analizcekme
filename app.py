import os
import re
import streamlit as st
import pandas as pd
import numpy as np

# Sayfa Ayarları (Telefona Tam Uyumlu)
st.set_page_config(page_title="Oran Analiz Pro AI", page_icon="⚽", layout="centered")

# CSS Tasarımı (Optimum Font ve Okunabilir Kontrastlı Uyarı Bandı)
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .stat-card { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 8px 10px; margin-bottom: 6px; font-family: sans-serif; font-size: 11px; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    .neon-alert-danger {
        background: linear-gradient(135deg, #500 0%, #200 100%);
        color: #ffdd57;
        padding: 9px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        margin-top: 6px;
        border: 2px solid #ff3333;
        box-shadow: 0 0 10px rgba(255, 51, 51, 0.5);
    }
    .neon-alert-success {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        color: #34d399;
        padding: 9px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
        text-align: center;
        margin-top: 6px;
        border: 2px solid #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "ORAN ANALİZ TABLOSU.xlsb")


def find_odd_column(columns, patterns):
    """Sütun adlarını normalize edip verilen desenlere uyan ilk sütunu döndürür."""
    for col in columns:
        norm = re.sub(r'[^A-Z0-9]', '', str(col).upper().replace('İ', 'I'))
        for pat in patterns:
            if pat in norm:
                return col
    return None


@st.cache_data(show_spinner=False)
def load_data():
    try:
        try:
            df = pd.read_excel(EXCEL_PATH, engine='pyxlsb', header=1)
        except Exception:
            df = pd.read_excel(EXCEL_PATH, header=1)
        return df
    except Exception:
        return None


st.markdown("<h2 style='text-align: center; color: #38bdf8; font-size: 18px; margin-bottom: 8px;'>⚽ ORAN ANALİZ VE AKILLI PATTERN MOTORU</h2>", unsafe_allow_html=True)

with st.spinner("📊 Tüm veritabanı (geçmiş sezonlar dahil) yükleniyor..."):
    df_all = load_data()

if df_all is None:
    st.error("❌ Excel verisi yüklenemedi! Lütfen dosya yolunu kontrol edin.")
    st.stop()

# Analiz motoru için sayısal kopya
df_calc_base = df_all.copy()
df_calc_base['MS1'] = pd.to_numeric(df_calc_base['MS1'], errors='coerce')
df_calc_base['MSX'] = pd.to_numeric(df_calc_base['MSX'], errors='coerce')
df_calc_base['MS2'] = pd.to_numeric(df_calc_base['MS2'], errors='coerce')

# Excel'deki İY oran sütun adlarını otomatik bulma
iy1_col = find_odd_column(df_calc_base.columns, ['IY1'])
iyx_col = find_odd_column(df_calc_base.columns, ['IYX'])
iy2_col = find_odd_column(df_calc_base.columns, ['IY2'])

# Excel'deki 2. Yarı (2Y) oran sütun adlarını otomatik bulma
y2_1_col = find_odd_column(df_calc_base.columns, ['2Y1', '2IY1', 'IY21'])
y2_x_col = find_odd_column(df_calc_base.columns, ['2YX', '2IYX', 'IY2X'])
y2_2_col = find_odd_column(df_calc_base.columns, ['2Y2', '2IY2', 'IY22'])

for c in [iy1_col, iyx_col, iy2_col, y2_1_col, y2_x_col, y2_2_col]:
    if c:
        df_calc_base[c] = pd.to_numeric(df_calc_base[c], errors='coerce')

df_clean = df_calc_base.dropna(subset=['MS1', 'MSX', 'MS2', 'İY SKOR', 'MS SKOR']).copy()

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
        df_analysis = df_clean[df_clean[lig_kolonu].isin(secilen_ligler)]
    else:
        df_analysis = df_clean
else:
    df_analysis = df_clean

st.markdown("---")

# MAÇ ADI / KÜNYE GİRİŞİ (Ekran Görüntüsü İçin)
st.markdown("<p style='font-size: 12px; font-weight: bold; color: #38bdf8; margin-bottom: 4px;'>📌 ANALİZ EDİLEN MAÇ (Ekran Görüntüsü Başlığı)</p>", unsafe_allow_html=True)
mac_adi_input = st.text_input("Maç Adını Yazın (Örn: Iğdır FK - Ümraniyespor)", value="", placeholder="Maç adını buraya yazabilirsiniz...")

# ORAN GİRİŞLERİ (Boş bırakılanlar otomatik es geçilir)
st.markdown("<p style='font-size: 12px; font-weight: bold; color: #38bdf8; margin-bottom: 4px;'>🎯 MAÇ SONUCU (MS) ORANLARI</p>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    ms1_input = st.text_input("MS 1", value="1.67")
with col2:
    msx_input = st.text_input("MS X", value="3.03")
with col3:
    ms2_input = st.text_input("MS 2", value="3.91")

st.markdown("<p style='font-size: 12px; font-weight: bold; color: #38bdf8; margin: 6px 0 4px 0;'>⚡ İLK YARI (İY) ORANLARI (Boş bırakılabilir)</p>", unsafe_allow_html=True)
col4, col5, col6 = st.columns(3)
with col4:
    iy1_input = st.text_input("İY 1", value="2.28")
with col5:
    iyx_input = st.text_input("İY X", value="1.88")
with col6:
    iy2_input = st.text_input("İY 2", value="")

st.markdown("<p style='font-size: 12px; font-weight: bold; color: #38bdf8; margin: 6px 0 4px 0;'>🔥 İKİNCİ YARI (2Y) ORANLARI (Boş bırakılabilir)</p>", unsafe_allow_html=True)
col7, col8, col9 = st.columns(3)
with col7:
    y2_1_input = st.text_input("2Y 1", value="")
with col8:
    y2_x_input = st.text_input("2Y X", value="")
with col9:
    y2_2_input = st.text_input("2Y 2", value="")

otomatik_mod = st.checkbox("🤖 Akıllı Tolerans (AI)", value=True)
tumunu_goster = st.checkbox("📋 Bulunan tüm maçları listede göster (Sınır olmasın)", value=True)
btn_analiz = st.button("ANALİZ ET 🚀", use_container_width=True, type="primary")

if btn_analiz:
    try:
        ms1_v = float(ms1_input.strip().replace(',', '.')) if ms1_input.strip() else 0.0
        msx_v = float(msx_input.strip().replace(',', '.')) if msx_input.strip() else 0.0
        ms2_v = float(ms2_input.strip().replace(',', '.')) if ms2_input.strip() else 0.0
        iy1_v = float(iy1_input.strip().replace(',', '.')) if iy1_input.strip() else 0.0
        iyx_v = float(iyx_input.strip().replace(',', '.')) if iyx_input.strip() else 0.0
        iy2_v = float(iy2_input.strip().replace(',', '.')) if iy2_input.strip() else 0.0
        y2_1_v = float(y2_1_input.strip().replace(',', '.')) if y2_1_input.strip() else 0.0
        y2_x_v = float(y2_x_input.strip().replace(',', '.')) if y2_x_input.strip() else 0.0
        y2_2_v = float(y2_2_input.strip().replace(',', '.')) if y2_2_input.strip() else 0.0
    except ValueError:
        st.error("Lütfen tüm değerleri geçerli sayı olarak girin!")
        st.stop()

    df_calc = df_analysis.copy()

    # Mesafe Hesaplama (Sadece dolu girilen oranlar hesaba katılır, boşlar atlanır)
    fark_ms1 = (df_calc['MS1'] - ms1_v) ** 2 if ms1_v > 0 else 0
    fark_msx = (df_calc['MSX'] - msx_v) ** 2 if msx_v > 0 else 0
    fark_ms2 = (df_calc['MS2'] - ms2_v) ** 2 if ms2_v > 0 else 0

    fark_iy1 = (df_calc[iy1_col] - iy1_v) ** 2 if (iy1_col and iy1_v > 0) else 0
    fark_iyx = (df_calc[iyx_col] - iyx_v) ** 2 if (iyx_col and iyx_v > 0) else 0
    fark_iy2 = (df_calc[iy2_col] - iy2_v) ** 2 if (iy2_col and iy2_v > 0) else 0

    fark_2y1 = (df_calc[y2_1_col] - y2_1_v) ** 2 if (y2_1_col and y2_1_v > 0) else 0
    fark_2yx = (df_calc[y2_x_col] - y2_x_v) ** 2 if (y2_x_col and y2_x_v > 0) else 0
    fark_2y2 = (df_calc[y2_2_col] - y2_2_v) ** 2 if (y2_2_col and y2_2_v > 0) else 0

    df_calc['Mesafe'] = np.sqrt(
        fark_ms1 + fark_msx + fark_ms2 +
        fark_iy1 + fark_iyx + fark_iy2 +
        fark_2y1 + fark_2yx + fark_2y2
    )

    # AKILLI TOLERANS ALGORİTMASI (AI MODU - Sadece dolu kutuları filtreler)
    if otomatik_mod:
        secilen_tol = 0.02
        filtre = pd.Series(True, index=df_calc.index)

        for t in [0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20]:
            temp_filtre = pd.Series(True, index=df_calc.index)
            if ms1_v > 0:
                temp_filtre &= (df_calc['MS1'] >= ms1_v - t) & (df_calc['MS1'] <= ms1_v + t)
            if msx_v > 0:
                temp_filtre &= (df_calc['MSX'] >= msx_v - t) & (df_calc['MSX'] <= msx_v + t)
            if ms2_v > 0:
                temp_filtre &= (df_calc['MS2'] >= ms2_v - t) & (df_calc['MS2'] <= ms2_v + t)
            if iy1_col and iy1_v > 0:
                temp_filtre &= (df_calc[iy1_col] >= iy1_v - t) & (df_calc[iy1_col] <= iy1_v + t)
            if iyx_col and iyx_v > 0:
                temp_filtre &= (df_calc[iyx_col] >= iyx_v - t) & (df_calc[iyx_col] <= iyx_v + t)
            if iy2_col and iy2_v > 0:
                temp_filtre &= (df_calc[iy2_col] >= iy2_v - t) & (df_calc[iy2_col] <= iy2_v + t)
            if y2_1_col and y2_1_v > 0:
                temp_filtre &= (df_calc[y2_1_col] >= y2_1_v - t) & (df_calc[y2_1_col] <= y2_1_v + t)
            if y2_x_col and y2_x_v > 0:
                temp_filtre &= (df_calc[y2_x_col] >= y2_x_v - t) & (df_calc[y2_x_col] <= y2_x_v + t)
            if y2_2_col and y2_2_v > 0:
                temp_filtre &= (df_calc[y2_2_col] >= y2_2_v - t) & (df_calc[y2_2_col] <= y2_2_v + t)

            secilen_tol = t
            if temp_filtre.sum() >= 20 or t == 0.20:
                filtre = temp_filtre
                break

        df_tolerans = df_calc[filtre].copy()

        def skor_ayir_temp(s):
            try:
                p = str(s).strip().split('-')
                return int(p[0]), int(p[1])
            except Exception:
                return 0, 0

        if not df_tolerans.empty:
            def check_surpriz_row(row):
                e_iy, d_iy = skor_ayir_temp(row['İY SKOR'])
                e_ms, d_ms = skor_ayir_temp(row['MS SKOR'])
                h = '1' if e_iy > d_iy else ('2' if d_iy > e_iy else 'X')
                f = '1' if e_ms > d_ms else ('2' if d_ms > e_ms else 'X')
                return 1 if f"{h}/{f}" in ['1/2', '2/1'] else 0

            df_tolerans['surpriz_flag'] = df_tolerans.apply(check_surpriz_row, axis=1)
            df_tolerans = df_tolerans.sort_values(by=['surpriz_flag', 'Mesafe'], ascending=[False, True]).copy()

        if not df_tolerans.empty:
            toplam_bulunan = len(df_tolerans)
            if tumunu_goster:
                benzerler = df_tolerans.copy()
                st.info(f"🤖 AI Modu: ±{secilen_tol} toleransla {toplam_bulunan} maç bulundu (Sürprizler öncelikli). Hepsi listeleniyor.")
            else:
                benzerler = df_tolerans.head(20).copy()
                st.info(f"🤖 AI Modu: ±{secilen_tol} toleransla {toplam_bulunan} maç bulundu (Sürprizler öncelikli). En yakın 20 tanesi listeleniyor.")
        else:
            st.warning("⚠️ Bu aralıkta tam eşleşme bulunamadı, en yakın maçlar listeleniyor.")
            benzerler = df_calc.sort_values('Mesafe').head(20).copy()

    else:
        st.info("🎯 Standart Mod: Sıfır tolerans (doğrudan en yakın mesafe) ile en yakın 20 maç listeleniyor.")
        benzerler = df_calc.sort_values('Mesafe').head(20).copy()


def skor_ayir(s):
    try:
        p = str(s).strip().split('-')
        return int(p[0]), int(p[1])
    except Exception:
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

    # 1. ÜST İSTATİSTİK KARTI
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

    # 2. İY VE MS SKOR TRENDLERİ
    st.markdown("<p style='font-size: 11px; font-weight: bold; color: #38bdf8; margin: 0 0 2px 0;'>📊 SKOR TRENDLERİ (ÖZET - STANDART/AI MODU)</p>", unsafe_allow_html=True)

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

    # EĞER MAÇ ADI YAZILDIYSA TABLONUN ÜSTÜNE ŞIK BİR BAŞLIK BASALIM
    if mac_adi_input.strip():
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0369a1 0%, #0f172a 100%); color: #38bdf8; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; text-align: center; margin-bottom: 6px; border: 1px solid #38bdf8; box-shadow: 0 0 8px rgba(56, 189, 248, 0.4);">
            📌 ANALİZ EDİLEN MAÇ : {mac_adi_input.strip().upper()}
        </div>
        """, unsafe_allow_html=True)

    # 3. TERMINAL TABLO
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
    <div style="background-color: #000000; padding: 8px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 10.5px; line-height: 1.35; white-space: pre; overflow-x: auto; border: 1px solid #333;">
    {"<br>".join(lines)}
    </div>
    """
    st.markdown(terminal_box, unsafe_allow_html=True)

    donus_orani = round((donus_sayisi / toplam_mac) * 100) if toplam_mac > 0 else 0
    if donus_orani >= 8 or donus_sayisi >= 2:
        uyari_mesaji = f"🚨 KRİTİK ALARM : Bu Oran Havuzu %{donus_orani} Oranında ({donus_sayisi} Maç) Maç İçi Ters Köşe (1/2 veya 2/1) Potansiyeli Taşıyor!"
        st.markdown(f'<div class="neon-alert-danger">{uyari_mesaji}</div>', unsafe_allow_html=True)
    else:
        uyari_mesaji = f"✅ PİYASA DENGELİ : Oran Havuzu İstikrarlı Seyrediyor (Ters köşe riski düşük)."
        st.markdown(f'<div class="neon-alert-success">{uyari_mesaji}</div>', unsafe_allow_html=True)

else:
    if btn_analiz:
        st.warning("Lütfen analiz için geçerli oranlar girin.")

# --- İKİ TAKIMLI AKILLI GEÇMİŞ MAÇ ARAMA MOTORU ---
st.markdown("---")
st.markdown("<h3 style='color: #38bdf8; font-size: 16px;'>🔍 İki Takım Arasındaki Geçmiş Maçları Listele</h3>", unsafe_allow_html=True)
st.caption("Aramak istediğin iki takımın adını yaz ve aşağıdaki butona bas, geçmişteki TÜM sezonlarındaki maçlarını orijinal oranları ve skorlarıyla listelesin.")

col_srch1, col_srch2 = st.columns(2)
with col_srch1:
    takim_a = st.text_input("1. Takım", value="").strip().upper()
with col_srch2:
    takim_b = st.text_input("2. Takım", value="").strip().upper()

btn_takim_ara = st.button("🔍 GEÇMİŞ MAÇLARI LİSTELE", use_container_width=True)

if btn_takim_ara:
    if not takim_a or not takim_b:
        st.warning("⚠️ Lütfen her iki takımın adını da eksiksiz girin.")
    else:
        kosul_gecmis = (
            (df_all['EV SAHİBİ'].astype(str).str.upper().str.contains(takim_a, na=False) & df_all['DEPLASMAN'].astype(str).str.upper().str.contains(takim_b, na=False)) |
            (df_all['EV SAHİBİ'].astype(str).str.upper().str.contains(takim_b, na=False) & df_all['DEPLASMAN'].astype(str).str.upper().str.contains(takim_a, na=False))
        )
        bulunan_gecmis = df_all[kosul_gecmis]

        if not bulunan_gecmis.empty:
            st.success(f"🎉 Aralarındaki toplam {len(bulunan_gecmis)} adet geçmiş maç bulundu (Tüm Sezonlar):")
            for _, m in bulunan_gecmis.iterrows():
                sezon_bilgi = str(m.get('SEZON', ''))
                lig_kolonu_bul = None
                for col in ['ÜLKE / LİG', 'ÜLKE/LİG', 'LİG', 'LIG', 'Lig', 'Lig Adı']:
                    if col in df_all.columns:
                        lig_kolonu_bul = col
                        break
                lig_bilgi = str(m.get(lig_kolonu_bul, '')) if lig_kolonu_bul else ''

                ev_sahibi = str(m['EV SAHİBİ'])
                deplasman = str(m['DEPLASMAN'])

                ms1_oran = m.get('MS1', '-')
                msx_oran = m.get('MSX', '-')
                ms2_oran = m.get('MS2', '-')
                if pd.isna(ms1_oran) or str(ms1_oran).strip() == '':
                    ms1_oran = "-"
                if pd.isna(msx_oran) or str(msx_oran).strip() == '':
                    msx_oran = "-"
                if pd.isna(ms2_oran) or str(ms2_oran).strip() == '':
                    ms2_oran = "-"

                iy_skor_str = str(m.get('İY SKOR', '-'))
                ms_skor_str = str(m.get('MS SKOR', '-'))
                if iy_skor_str == 'nan' or not iy_skor_str.strip():
                    iy_skor_str = "0-0"
                if ms_skor_str == 'nan' or not ms_skor_str.strip():
                    ms_skor_str = "0-0"

                try:
                    iy_p = iy_skor_str.strip().split('-')
                    ms_p = ms_skor_str.strip().split('-')
                    iy_e, iy_d = int(iy_p[0]), int(iy_p[1])
                    ms_e, ms_d = int(ms_p[0]), int(ms_p[1])
                except Exception:
                    iy_e, iy_d, ms_e, ms_d = 0, 0, 0, 0

                ht_val = '1' if iy_e > iy_d else ('2' if iy_d > iy_e else 'X')
                ft_val = '1' if ms_e > ms_d else ('2' if ms_d > ms_e else 'X')
                ht_ft_str = f"{ht_val}/{ft_val}"
                ms_toplam_gol = ms_e + ms_d

                is_alev = False
                alev_etiketleri = []

                if ht_ft_str in ['1/2', '2/1']:
                    is_alev = True
                    alev_etiketleri.append(f"Ters Köşe ({ht_ft_str})")
                elif ht_ft_str == '1/X':
                    is_alev = True
                    alev_etiketleri.append("1/X Sürpriz")
                elif ht_ft_str == '2/X':
                    is_alev = True
                    alev_etiketleri.append("2/X Sürpriz")

                if ms_toplam_gol >= 6:
                    is_alev = True
                    alev_etiketleri.append(f"{ms_toplam_gol} Gol (6+)")

                alev_icon = " 🔥" if is_alev else ""
                etiket_yazi = f" — <span style='color:#f59e0b; font-weight:bold;'>{' | '.join(alev_etiketleri)}</span>" if is_alev else ""

                st.markdown(f"""
                <div style="background-color: #111827; border: 2px solid {'#f59e0b' if is_alev else '#1f2937'}; padding: 12px; border-radius: 8px; margin-bottom: 10px; font-size: 13px;">
                    <b style="color: #38bdf8; font-size: 13px;">🏆 Lig/Sezon: {lig_bilgi}</b> | <span style="color:#9ca3af;">{sezon_bilgi}</span><br>
                    <span style="color:#34d399; font-weight:bold; font-size:15px;">⚽ {ev_sahibi} vs {deplasman}</span>{alev_icon}{etiket_yazi}<br>
                    <span style="color:#f43f5e; font-weight:bold; font-size:12px;">Oranlar ➔ MS1: {ms1_oran} | MSX: {msx_oran} | MS2: {ms2_oran}</span><br>
                    <span style="color:#e2e8f0; font-weight:bold; font-size:12px;">Skorlar ➔ İlk Yarı (İY): {iy_skor_str} | Maç Sonu (MS): {ms_skor_str} (Toplam: {ms_toplam_gol} Gol)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Bu iki takım arasında veritabanında eşleşen geçmiş maç bulunamadı. (Takım isimlerinin tam yazılışını kontrol edebilirsin)")
