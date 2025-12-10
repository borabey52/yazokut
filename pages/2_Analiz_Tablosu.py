import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import io

st.set_page_config(page_title="Sınıf Analizi", layout="wide")

# ==========================================
# 1. YAZICI İÇİN SİHİRLİ CSS (TASARIM)
# ==========================================
# Bu kod, yazdırma ekranında (Ctrl+P) yan menüyü ve butonları gizler.
st.markdown("""
    <style>
    @media print {
        /* Yan menüyü ve üst şeridi yok et */
        [data-testid="stSidebar"], header, footer { display: none !important; }
        
        /* Tüm butonları gizle (Yazdır ve İndir butonları kağıtta çıkmasın) */
        .stButton, button, [data-testid="stDownloadButton"] { display: none !important; }
        
        /* İçerik kenar boşluklarını sıfırla */
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        
        /* Arka planı bembeyaz yap */
        .stApp { background-color: white !important; }
        
        /* Grafikleri ve tabloyu kağıda sığdır */
        div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sınıf Analizi ve Raporlama")

# 2. HAFIZA KONTROLÜ
if 'sinif_verileri' not in st.session_state or len(st.session_state.sinif_verileri) == 0:
    st.info("Henüz veri yok. Lütfen Ana Sayfa'dan kağıt okutun.")
    st.stop()

# 3. VERİYİ HAZIRLA
df = pd.DataFrame(st.session_state.sinif_verileri)
# Tabloda 'Detaylar' sütunu varsa onu göstermelik tablodan çıkaralım (analiz için kalsın)
gosterilecek_df = df.drop(columns=["Detaylar"], errors="ignore")

# 4. İSTATİSTİKLER (EN ÜSTTE)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Öğrenci Sayısı", len(df))
if 'Toplam Puan' in df.columns:
    c2.metric("Sınıf Ortalaması", f"{df['Toplam Puan'].mean():.1f}")
    c3.metric("En Yüksek Not", df['Toplam Puan'].max())
    c4.metric("En Düşük Not", df['Toplam Puan'].min())

st.markdown("---")

# 5. GERİ GETİRİLEN BÖLÜM: SORU ANALİZİ GRAFİĞİ 📈
st.subheader("📈 Soru Bazlı Başarı Analizi")
try:
    # İçinde "Soru" kelimesi geçen sütunları bul (Soru 1, Soru 2...)
    soru_sutunlari = [col for col in df.columns if "Soru" in col]
    
    if soru_sutunlari:
        # Sadece bu sütunların ortalamasını al
