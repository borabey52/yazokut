import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sınıf Analizi", layout="wide")

st.title("📊 Sınıf Analizi ve Excel")

# 1. HAFIZA KONTROLÜ
if 'sinif_verileri' not in st.session_state or len(st.session_state.sinif_verileri) == 0:
    st.warning("Henüz okunmuş kağıt yok. Lütfen 'Kağıt Oku' sayfasına gidip sınav okutun.")
    st.stop()

# 2. TABLOYU OLUŞTUR (Pandas)
# Hafızadaki veriyi Excel benzeri yapıya çeviriyoruz
df = pd.DataFrame(st.session_state.sinif_verileri)

# Detaylar sütununu tabloda göstermeye gerek yok, arkada kalsın
gosterilecek_df = df.drop(columns=["Detaylar"], errors="ignore")

# 3. İSTATİSTİKLER
col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Öğrenci", len(df))
col2.metric("Sınıf Ortalaması", f"{df['Toplam Puan'].mean():.1f}")
col3.metric("En Yüksek Puan", df['Toplam Puan'].max())
col4.metric("En Düşük Puan", df['Toplam Puan'].min())

st.markdown("---")

# 4. TABLOYU GÖSTER
st.subheader("📋 Not Listesi")
st.dataframe(gosterilecek_df, use_container_width=True)

# 5. GRAFİK: SORU BAŞARI ORANLARI
st.subheader("📈 Soru Bazlı Başarı Analizi")
try:
    # Sadece "Soru X" ile başlayan sütunları al
    soru_sutunlari = [col for col in df.columns if "Soru" in col]
    if soru_sutunlari:
        soru_analizi = df[soru_sutunlari].mean()
        st.bar_chart(soru_analizi)
        st.caption("Bu grafik, sınıfta hangi sorunun ortalama kaç puan aldığını gösterir.")
except:
    st.info("Grafik oluşturulacak yeterli veri yok.")

# 6. EXCEL İNDİRME BUTONU
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig') # Türkçe karakter için sig

csv = convert_df(gosterilecek_df)

st.download_button(
    label="📥 Excel (CSV) Olarak İndir",
    data=csv,
    file_name='Sinif_Analiz_Listesi.csv',
    mime='text/csv',
    type="primary"
)