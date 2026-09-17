import os
import numpy as np
import pandas as pd
import streamlit as st

# Sayfa Yapısı (Geniş Ekran - Telefonda ve PC'de Mükemmel Görünüm)
st.set_page_config(
    page_title="TİTAN BULDOZER — Derin Bülten Tarayıcı",
    page_icon="⚽",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "ORAN ANALİZ TABLOSU.xlsb")
CACHE_PATH = os.path.join(BASE_DIR, "cache_data.pkl")


# Geçmiş Veritabanını Işık Hızında Önbellekle Yükleme
@st.cache_data(show_spinner=False)
def load_historical_data():
  if os.path.exists(CACHE_PATH):
    try:
      return pd.read_pickle(CACHE_PATH)
    except Exception:
      pass
  try:
    try:
      df = pd.read_excel(EXCEL_PATH, engine="pyxlsb", header=1)
    except Exception:
      df = pd.read_excel(EXCEL_PATH, header=1)

    df["MS1"] = pd.to_numeric(df["MS1"], errors="coerce")
    df["MSX"] = pd.to_numeric(df["MSX"], errors="coerce")
    df["MS2"] = pd.to_numeric(df["MS2"], errors="coerce")
    df_clean = df.dropna(
        subset=["MS1", "MSX", "MS2", "İY SKOR", "MS SKOR"]
    ).copy()
    df_clean.to_pickle(CACHE_PATH)
    return df_clean
  except Exception as e:
    return None


# Başlık Tasarımı
st.markdown(
    "<h2 style='text-align: center; color: #00FF7F;'>⚽ TİTAN BULDOZER —"
    " DERİN BÜLTEN TARAMA MOTORU</h2>",
    unsafe_allow_html=True,
)

# Güncel Bülten Yükleme Alanı (Telefondan veya Masaüstünden Dosya Atma)
uploaded_file = st.file_uploader(
    "📁 Güncel Bülten Dosyasını Seç (Örn: Guncel_Bulten.xlsx)",
    type=["xlsx", "xls"],
)

df_hist = load_historical_data()

if df_hist is None:
  st.error(
      "❌ Geçmiş oran analizi veritabanı (ORAN ANALİZ TABLOSU.xlsb)"
      " bulunamadı! Lütfen dosya yolunu kontrol edin."
  )
  st.stop()

st.success(
    f"✅ Arşiv Hafızada: **{len(df_hist):,}** maçlık pattern veritabanı aktif ve"
    " hazır."
)

if uploaded_file is not None:
  try:
    df_bulten = pd.read_excel(uploaded_file)
  except Exception as e:
    st.error(f"Bülten okunurken hata oluştu: {e}")
    st.stop()

  st.info(
      f"📂 Güncel bülten yüklendi. Toplam **{len(df_bulten)}** maç sistemde"
      " taranmayı bekliyor."
  )

  # Tolerans ayarı
  tol_input = st.slider(
      "Tolerans Aralığı (±)",
      min_value=0.01,
      max_value=0.10,
      value=0.03,
      step=0.01,
  )

  if st.button(
      "🚀 50 MAÇLIK DERİN BÜLTEN TARAMASINI BAŞLAT",
      use_container_width=True,
      type="primary",
  ):
    with st.spinner(
        "⚡ Magnezyum motorlar ateşlendi, bülten taranıyor ve simülasyonlar"
        " yapılıyor..."
    ):

      def skor_ayir(s):
        try:
          p = str(s).strip().split("-")
          return int(p[0]), int(p[1])
        except:
          return 0, 0

      # Geçmiş veriye önceden hesaplanmış skor sütunlarını ekleyelim (Hız için)
      if "iy_toplam" not in df_hist.columns:
        temp_iy = df_hist["İY SKOR"].apply(lambda x: pd.Series(skor_ayir(x)))
        temp_ms = df_hist["MS SKOR"].apply(lambda x: pd.Series(skor_ayir(x)))
        df_hist["iy_toplam"] = temp_iy[0] + temp_iy[1]
        df_hist["ms_toplam"] = temp_ms[0] + temp_ms[1]
        df_hist["kg_var"] = (temp_ms[0] > 0) & (temp_ms[1] > 0)
        df_hist["is_donus"] = df_hist.apply(
            lambda r: (
                (temp_iy.loc[r.name, 0] > temp_iy.loc[r.name, 1])
                and (temp_ms.loc[r.name, 0] < temp_ms.loc[r.name, 1])
            )
            or (
                (temp_iy.loc[r.name, 0] < temp_iy.loc[r.name, 1])
                and (temp_ms.loc[r.name, 0] > temp_ms.loc[r.name, 1])
            ),
            axis=1,
        )

      # Bülten sütunlarını esnek yakalama
      def find_col(keywords):
        for kw in keywords:
          for c in df_bulten.columns:
            if kw in str(c).upper():
              return c
        return None


      c_saat = find_col(["SAAT", "TARİH", "TIME"])
      c_ev = find_col(["EV", "HOME", "TAKIM1"])
      c_dep = find_col(["DEPL", "AWAY", "TAKIM2"])
      c_ms1 = find_col(["MS1", "MS 1", "1"])
      c_msx = find_col(["MSX", "MS X", "X", "MS0"])
      c_ms2 = find_col(["MS2", "MS 2", "2"])

      simulasyon_sonuclari = []

      for idx, row in df_bulten.iterrows():
        try:
          m_saat = (
              str(row[c_saat]) if c_saat and pd.notna(row[c_saat]) else "18:00"
          )
          m_ev = str(row[c_ev]) if c_ev and pd.notna(row[c_ev]) else f"Ev_{idx}"
          m_dep = (
              str(row[c_dep]) if c_dep and pd.notna(row[c_dep]) else f"Dep_{idx}"
          )
          ms1_v = float(
              str(row[c_ms1]).replace(",", ".") if c_ms1 else row.iloc[3]
          )
          msx_v = float(
              str(row[c_msx]).replace(",", ".") if c_msx else row.iloc[4]
          )
          ms2_v = float(
              str(row[c_ms2]).replace(",", ".") if c_ms2 else row.iloc[5]
          )
        except:
          continue

        # Öklid mesafesi ile en yakın 50 maçı bulma
        df_calc = df_hist.copy()
        df_calc["Mesafe"] = np.sqrt(
            (df_calc["MS1"] - ms1_v) ** 2
            + (df_calc["MSX"] - msx_v) ** 2
            + (df_calc["MS2"] - ms2_v) ** 2
        )
        benzerler = df_calc.sort_values("Mesafe").head(50)

        if len(benzerler) > 0:
          oran_str = f"{ms1_v:.2f}-{msx_v:.2f}-{ms2_v:.2f}"
          mac_adi_str = f"{m_ev} - {m_dep}"[:22]

          donus_pct = round((benzerler["is_donus"].sum() / len(benzerler)) * 100)
          gol6_pct = round(
              ((benzerler["ms_toplam"] >= 6).sum() / len(benzerler)) * 100
          )
          ust45_pct = round(
              ((benzerler["ms_toplam"] >= 5).sum() / len(benzerler)) * 100
          )
          ust25_pct = round(
              ((benzerler["ms_toplam"] >= 3).sum() / len(benzerler)) * 100
          )
          kg_pct = round((benzerler["kg_var"].sum() / len(benzerler)) * 100)

          simulasyon_sonuclari.append({
              "saat": m_saat[:11],
              "mac": mac_adi_str,
              "oranlar": oran_str,
              "donus": donus_pct,
              "gol6": gol6_pct,
              "ust45": ust45_pct,
              "ust25": ust25_pct,
              "kg": kg_pct,
          })

      df_res = pd.DataFrame(simulasyon_sonuclari)

      if not df_res.empty:
        grup1 = df_res.sort_values(by="donus", ascending=False).head(15)
        grup3 = df_res.sort_values(by="gol6", ascending=False).head(15)
        grup5 = df_res.sort_values(by="ust25", ascending=False).head(10)

        # Terminal Görünümü İçin Satırları Oluşturma
        terminal_lines = []

        # Grup 1 Başlık ve Maçları
        terminal_lines.append(
            "<span style='color:#FF8C00; font-weight:bold;'>⚡ GRUP 1: 1/2 VE"
            " 2/1 SÜRPRİZ DÖNÜŞ BOMBALARI</span>"
        )
        terminal_lines.append(
            "<span style='color:#00FF66;'>" + "-" * 75 + "</span>"
        )
        for _, r in grup1.iterrows():
          line = f"{r['saat']:<11} | {r['mac']:<22} | {r['oranlar']:<15} | 🎴 1/2-2/1: %{r['donus']} ({int(r['donus']*50/100)}/50)"
          terminal_lines.append(f"<span style='color:#00FF66;'>{line}</span>")

        terminal_lines.append("")
        # Grup 3 Başlık ve Maçları
        terminal_lines.append(
            "<span style='color:#FF8C00; font-weight:bold;'>🔥 GRUP 3: 6+ GOL"
            " YAĞMURU SİNYALLERİ</span>"
        )
        terminal_lines.append(
            "<span style='color:#00FF66;'>" + "-" * 75 + "</span>"
        )
        for _, r in grup3.iterrows():
          line = f"{r['saat']:<11} | {r['mac']:<22} | {r['oranlar']:<15} | ⚽ 6+ Gol: %{r['gol6']} | ⚽ 4.5+ Üst: %{r['ust45']}"
          terminal_lines.append(f"<span style='color:#00E5FF;'>{line}</span>")

        terminal_lines.append("")
        # Grup 5 Başlık ve Maçları
        terminal_lines.append(
            "<span style='color:#FF8C00; font-weight:bold;'>🎯 GRUP 5: 2.5+"
            " ÜST & KG VAR YÜKSEK İHTİMAL MAÇLAR</span>"
        )
        terminal_lines.append(
            "<span style='color:#00FF66;'>" + "-" * 75 + "</span>"
        )
        for _, r in grup5.iterrows():
          line = f"{r['saat']:<11} | {r['mac']:<22} | {r['oranlar']:<15} | ⚽ 2.5+ Üst: %{r['ust25']} | 💖 KG Var: %{r['kg']}"
          terminal_lines.append(f"<span style='color:#00FF66;'>{line}</span>")

        content_html = "<br>".join(terminal_lines)

        # Siyah Terminal Kutusu Tasarımı
        terminal_box = []
        terminal_box.append("""
                <div style="
                    background-color: #000000;
                    padding: 15px;
                    border-radius: 8px;
                    font-family: 'Courier New', Consolas, monospace;
                    font-size: 13px;
                    line-height: 1.5;
                    white-space: pre;
                    overflow-x: auto;
                    border: 1px solid #222;
                ">
                """)
        terminal_box.append(content_html)
        terminal_box.append("</div>")

        st.markdown("".join(terminal_box), unsafe_allow_html=True)
        st.success(
            f"⚡ {len(df_res)} Maçlık Derin AI Bülten Taraması Başarıyla"
            " Tamamlandı!"
        )
      else:
        st.warning(
            "⚠️ Bülten içerisindeki oran sütunları eşleştirilemedi. Lütfen"
            " bülten formatını kontrol edin."
        )
else:
  st.info(
      "💡 Cebinden dilediğin gibi tarama yapmak için yukarıdan güncel bülten"
      " Excel dosyanı yükle kanka."
  )
