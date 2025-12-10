import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Sınıf Analizi", layout="wide")

# ==========================================
# 1. YAZICI İÇİN ÖZEL CSS (SİHİRLİ KISIM)
# ==========================================
# Bu kod, yazdır dediğinde butonları ve menüyü gizler, sadece tabloyu bırakır.
st.markdown("""
    <style>
    @media print {
        /* Yan menüyü gizle */
        [data-testid="stSidebar"] { display: none !important; }
        /* Üstteki renkli şeridi ve ayarları gizle */
        header { display: none !important; }
        /* Butonların hepsini gizle (Yazdır butonunun kendisi dahil) */
        .stButton, button, [data-testid="stDownloadButton"] { display: none !important; }
        /* Sayfa kenar boşluklarını ayarla */
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        /* Arka planı beyaz yap */
        .stApp { background-color: white !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sınıf Analizi ve Rapor")

# 2. HAFIZA KONTROLÜ
if 'sinif_verileri' not in st.session_state or len(st.session_state.sinif_verileri) == 0:
    st.info("Henüz veri yok. Lütfen Ana Sayfa'dan kağıt okutun.")
    st.stop()

# 3. VERİYİ HAZIRLA
df = pd.DataFrame(st.session_state.sinif_verileri)
gosterilecek_df = df.drop(columns=["Detaylar"], errors="ignore")

# 4. İSTATİSTİKLER PANELI
col1, col2, col3, col4 = st.columns(4)
col1.metric("Öğrenci Sayısı", len(df))
if 'Toplam Puan' in df.columns:
    col2.metric("Ortalama", f"{df['Toplam Puan'].mean():.1f}")
    col3.metric("En Yüksek", df['Toplam Puan'].max())
    col4.metric("En Düşük", df['Toplam Puan'].min())

st.markdown("---")

# 5. WEB TABLOSU
st.subheader("📋 Detaylı Liste")
# Tabloyu ekrana tam yayalım
st.dataframe(gosterilecek_df, use_container_width=True)

st.markdown("---")

# ==========================================
# 6. YAZDIRMA VE EXCEL BUTONLARI
# ==========================================
c1, c2 = st.columns([1, 1])

with c1:
    # JavaScript ile Yazdırma Butonu
    # Bu butona basınca tarayıcının Yazdır penceresi açılır
    st.markdown(
        """
        <button onclick="window.print()" style="
            background-color: #4CAF50; 
            border: none;
            color: white;
            padding: 15px 32px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 8px;
            width: 100%;">
            🖨️ BU SAYFAYI YAZDIR (PDF)
        </button>
        """,
        unsafe_allow_html=True
    )
    st.caption("Not: Yazdırma ekranında 'Hedef' kısmından 'PDF Olarak Kaydet'i seçebilir veya doğrudan yazıcıya gönderebilirsiniz.")

with c2:
    # Excel İndirme (Eski özellik de dursun)
    import io
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sonuclar')
        return output.getvalue()
    
    excel_data = to_excel(gosterilecek_df)
    st.download_button(
        label="📥 Excel Olarak İndir",
        data=excel_data,
        file_name='Sinav_Listesi.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        type="secondary",
        use_container_width=True
    )
