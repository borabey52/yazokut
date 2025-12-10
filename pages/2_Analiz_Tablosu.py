import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Sınıf Analizi", layout="wide")

st.title("📊 Sınıf Analizi ve Excel")

# 1. HAFIZA KONTROLÜ
# Ana sayfadan gelen veriler burada tutulur
if 'sinif_verileri' not in st.session_state or len(st.session_state.sinif_verileri) == 0:
    st.info("Henüz okunmuş kağıt yok. Lütfen 'Ana Sayfa'dan kağıt okutun.")
    st.stop()

# 2. TABLOYU OLUŞTUR
df = pd.DataFrame(st.session_state.sinif_verileri)

# (İsteğe bağlı) Gereksiz detay sütunlarını temizle
# Eğer kodunda 'Detaylar' diye bir sütun oluşuyorsa onu atarız
gosterilecek_df = df.drop(columns=["Detaylar"], errors="ignore")

# 3. İSTATİSTİKLER (Üst Bilgi Paneli)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Öğrenci", len(df))
if 'Toplam Puan' in df.columns:
    col2.metric("Sınıf Ortalaması", f"{df['Toplam Puan'].mean():.1f}")
    col3.metric("En Yüksek", df['Toplam Puan'].max())
    col4.metric("En Düşük", df['Toplam Puan'].min())

st.markdown("---")

# 4. TABLOYU GÖSTER (Web Görünümü)
st.subheader("📋 Not Listesi")
st.dataframe(gosterilecek_df, use_container_width=True)

# 5. GRAFİK
st.subheader("📈 Başarı Analizi")
try:
    soru_sutunlari = [col for col in df.columns if "Soru" in col]
    if soru_sutunlari:
        soru_analizi = df[soru_sutunlari].mean()
        st.bar_chart(soru_analizi)
except:
    pass

# ==========================================
# 6. EXCEL (.XLSX) İNDİRME MOTORU
# ==========================================
st.markdown("---")

def to_excel(df):
    output = io.BytesIO()
    # openpyxl motorunu kullanarak gerçek bir Excel dosyası oluşturuyoruz
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sinav_Sonuclari')
        
        # Sütun Genişliklerini Otomatik Ayarlama (Gözüktüğü gibi olsun diye)
        worksheet = writer.sheets['Sinav_Sonuclari']
        for i, col in enumerate(df.columns):
            # En uzun hücreyi bulup ona göre genişlik veriyoruz
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(str(col))
            ) + 2
            # Excel sütun harfini bul (A, B, C...)
            col_letter = chr(65 + i) if i < 26 else 'Z' 
            worksheet.column_dimensions[col_letter].width = max_len
            
    return output.getvalue()

# Excel Verisini Hazırla
excel_data = to_excel(gosterilecek_df)

# İndirme Butonu
st.download_button(
    label="📥 Listeyi Excel (.xlsx) Olarak İndir",
    data=excel_data,
    file_name='Sinif_Not_Listesi.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    type="primary",
    use_container_width=True
)
