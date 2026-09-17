import numpy as np
import pandas as pd
import time

# --- 1. TAKIM İSİMLERİNİ OTOMATİK DÜZELTME FONKSİYONU ---
def takim_ismini_bul(row, index, is_home=True):
    """
    Excel/DataFrame sütun adı ne olursa olsun gerçek takım adını yakalar.
    Sütun bulunamazsa veya boşsa varsayılan ID üretir.
    """
    olasi_sutunlar = (
        ['EV_TAKIM', 'Ev_Takim', 'Ev Sahibi', 'Home', 'Ev', 'EV', 'Takim_1']
        if is_home else
        ['DEP_TAKIM', 'Dep_Takim', 'Deplasman', 'Away', 'Dep', 'DEP', 'Takim_2']
    )
    
    for sutun in olasi_sutunlar:
        if sutun in row and pd.notna(row[sutun]) and str(row[sutun]).strip() != '':
            return str(row[sutun]).strip()
            
    return f"Ev_{index}" if is_home else f"Dep_{index}"


# --- 2. HIZLANDIRILMIŞ VEKTÖREL BÜLTEN TARAMA MOTORU ---
def hizli_bulten_taramasi(bulten_df, gecmis_df, tolerans=0.03):
    start_time = time.time()
    
    # Oran sütun adlarını tespit et
    oran_sutunlari = []
    for aday in [['MS1', 'MSX', 'MS2'], ['MS_1', 'MS_X', 'MS_2'], ['1', 'X', '2']]:
        if all(col in bulten_df.columns for col in aday) and all(col in gecmis_df.columns for col in aday):
            oran_sutunlari = aday
            break
            
    if not oran_sutunlari:
        raise ValueError("❌ Oran sütunları (MS1, MSX, MS2) DataFrame içinde bulunamadı!")

    # NumPy Matrislerine Dönüştür (Tarama Hızını 10-20 Kat Artıran Kısım)
    bulten_oranlar = bulten_df[oran_sutunlari].to_numpy(dtype=float) # (1107, 3)
    gecmis_oranlar = gecmis_df[oran_sutunlari].to_numpy(dtype=float) # (N, 3)

    grup_1_sonuclar = [] # 1/2 ve 2/1 Sürpriz
    grup_3_sonuclar = [] # 6+ Gol
    grup_5_sonuclar = [] # 2.5+ Üst & KG Var

    toplam_bulten = len(bulten_df)

    for i in range(toplam_bulten):
        b_row = bulten_df.iloc[i]
        b_oran = bulten_oranlar[i]

        # 🚀 TEK MATRİS ÇIKARMASI İLE TÜM GEÇMİŞİ MİLİSANİYELERDE TARAR
        farklar = np.abs(gecmis_oranlar - b_oran)
        eslesen_maske = np.all(farklar <= tolerans, axis=1)
        eslesen_maclar = gecmis_df[eslesen_maske]

        toplam_eslesme = len(eslesen_maclar)
        if toplam_eslesme < 5: # 5 maçtan az eşleşme varsa atla
            continue

        # Takım İsimlerini Düzelt
        ev_adi = takim_ismini_bul(b_row, i, is_home=True)
        dep_adi = takim_ismini_bul(b_row, i, is_home=False)
        tarih = b_row.get('Tarih', b_row.get('TARİH', '20.09.2026'))

        # İstatistik Hesaplamaları
        # 1/2 ve 2/1 Dönüş Sayısı
        if 'IY_MS' in eslesen_maclar.columns:
            donus_sayisi = eslesen_maclar['IY_MS'].isin(['1/2', '2/1']).sum()
            donus_yuzde = int(round((donus_sayisi / toplam_eslesme) * 100))
        else:
            donus_yuzde, donus_sayisi = 0, 0

        # Gol İstatistikleri
        toplam_gol = eslesen_maclar.get('TOPLAM_GOL', eslesen_maclar.get('TG', pd.Series(dtype=float)))
        
        gol_6_yuzde = int(round(((toplam_gol >= 6).sum() / toplam_eslesme) * 100)) if len(toplam_gol) > 0 else 0
        ust_45_yuzde = int(round(((toplam_gol > 4.5).sum() / toplam_eslesme) * 100)) if len(toplam_gol) > 0 else 0
        ust_25_yuzde = int(round(((toplam_gol > 2.5).sum() / toplam_eslesme) * 100)) if len(toplam_gol) > 0 else 0
        
        kg_var = eslesen_maclar.get('KG', eslesen_maclar.get('KG_DURUM', pd.Series(dtype=str)))
        kg_var_yuzde = int(round(((kg_var == 'KG VAR').sum() / toplam_eslesme) * 100)) if len(kg_var) > 0 else 0

        oran_str = f"{b_oran[0]:.2f}-{b_oran[1]:.2f}-{b_oran[2]:.2f}"
        mac_etiketi = f"{tarih} | {ev_adi:<15} - {dep_adi:<15} | {oran_str}"

        # Gruplara Ayırma
        if donus_yuzde >= 14:
            grup_1_sonuclar.append(f"{mac_etiketi} | 🚨 1/2-2/1: %{donus_yuzde} ({donus_sayisi}/{toplam_eslesme})")

        if gol_6_yuzde >= 20:
            grup_3_sonuclar.append(f"{mac_etiketi} | ⚽ 6+ Gol: %{gol_6_yuzde} | ⚽ 4.5+ Üst: %{ust_45_yuzde}")

        if ust_25_yuzde >= 80:
            grup_5_sonuclar.append(f"{mac_etiketi} | ⚽ 2.5+ Üst: %{ust_25_yuzde} | 💖 KG Var: %{kg_var_yuzde}")

    gecen_sure = round(time.time() - start_time, 2)

    # --- EKRAN ÇIKTI FORMATI ---
    print(f"\n⚡ GRUP 1: 1/2 VE 2/1 SÜRPRİZ DÖNÜŞ BOMBALARI")
    print("-" * 85)
    for res in grup_1_sonuclar: print(res)

    print(f"\n🔥 GRUP 3: 6+ GOL YAĞMURU SİNYALLERİ")
    print("-" * 85)
    for res in grup_3_sonuclar: print(res)

    print(f"\n🎯 GRUP 5: 2.5+ ÜST & KG VAR YÜKSEK İHTİMAL MAÇLAR")
    print("-" * 85)
    for res in grup_5_sonuclar: print(res)

    print(f"\n⚡ {toplam_bulten} Maçlık Derin AI Bülten Taraması {gecen_sure} Saniyede Başarıyla Tamamlandı!")


# --- ÇALIŞTIRMA ÖRNEĞİ ---
# bulten_df ve gecmis_df verilerini yükledikten sonra çağırın:
# hizli_bulten_taramasi(bulten_df, gecmis_df, tolerans=0.03)
