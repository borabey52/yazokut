import streamlit as st
import pandas as pd
import io

# Sayfa Ayarları (En başta olmalı)
st.set_page_config(page_title="Analiz Raporu", layout="wide")

# ==========================================
# 1. YAZICI DOSTU TASARIM (CSS)
# ==========================================
# Bu kod, Ctrl+P yapıldığında menüleri gizler, sadece raporu çıkarır.
st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"] { display: none !important; }
        header { display: none !important; }
        footer { display: none !important; }
        .stButton, button, [data-testid="stDownloadButton"] { display: none !important; }
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
        .stApp { background-color: white !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sınıf Analizi ve Rapor")

# ==========================================
# 2. HAFIZA KONTROLÜ
# ==========================================
if 'sinif_verileri' not in st.session_state:
    st.session_state.sinif_verileri = []

if len(st.session_state.sinif_verileri) == 0:
    st.info("Henüz veri yok. Lütfen Ana Sayfa'dan kağıt okutun.")
    st.stop()

# ==========================================
# 3. VERİYİ HAZIRLA
# ==========================================
df = pd.DataFrame(st.session_state.sinif_verileri)
# Detaylar sütununu görsel tablodan çıkar (varsa)
gosterilecek_df = df.drop(columns=["Detaylar"], errors="ignore")

# ==========================================
# 4. İSTATİSTİKLER PANELI
# ==========================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Öğrenci Sayısı", len(df))

if 'Toplam Puan' in df.columns:
    # Sayıları yuvarlayarak gösterelim
    ort = df['Toplam Puan'].mean()
    en_yuksek = df['Toplam Puan'].max()
    en_dusuk = df['Toplam Puan'].min()
    
    c2.metric("Sınıf Ortalaması", f"{ort:.1f}")
    c3.metric("En Yüksek Not", f"{en_yuksek:.0f}")
    c4.metric("En Düşük Not", f"{en_dusuk:.0f}")

st.markdown("---")

# ==========================================
# 5. SORU ANALİZİ GRAFİĞİ 📈
# ==========================================
st.subheader("📈 Soru Başarı Analizi")

try:
    # "Soru" kelimesi geçen sütunları bul
    soru_sutunlari = [col for col in df.columns if "Soru" in col]
    
    if soru_sutunlari:
        # Ortalamaları al
        analiz = df[soru_sutunlari].mean()
        # Grafiği çiz
        st.bar_chart(analiz, color="#4CAF50") 
        st.caption("Grafik: Soruların sınıf genelindeki ortalama puanları.")
    else:
        st.warning("Grafik için soru verisi bulunamadı.")
except Exception as e:
    st.error("Grafik oluşturulamadı.")

st.markdown("---")

# ==========================================
# 6. DETAYLI LİSTE
# ==========================================
st.subheader("📋 Öğrenci Not Listesi")
st.dataframe(gosterilecek_df, use_container_width=True)

st.markdown("---")

# ==========================================
# 7. RAPORLAMA BUTONLARI
# ==========================================
col1, col2 = st.columns(2)

with col1:
    # Yazdırma Bilgilendirmesi (Buton yerine kutu, çünkü butonlar bazen çalışmaz)
    st.success("🖨️ **YAZDIRMAK İÇİN:** Klavyeden **Ctrl + P** (Mac: Cmd+P) tuşuna basınız.")
    st.caption("Otomatik olarak menüler gizlenecek ve temiz bir rapor çıkacaktır.")

with col2:
    # Excel İndirme (Openpyxl)
    try:
        def convert_df(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Sonuclar')
                # Sütun genişlik ayarı
                worksheet = writer.sheets['Sonuclar']
                for idx, col in enumerate(df.columns):
                    worksheet.column_dimensions[chr(65 + idx) if idx < 26 else 'Z'].width = 15
            return output.getvalue()

        excel_data = convert_df(gosterilecek_df)
        
        st.download_button(
            label="📥 Excel Olarak İndir",
            data=excel_data,
            file_name='Sinav_Listesi.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary",
            use_container_width=True
        )
    except Exception as e:
        st.error("Excel oluşturulurken hata oluştu. Lütfen requirements.txt dosyasında 'openpyxl' olduğundan emin olun.")
