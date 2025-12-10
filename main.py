import streamlit as st

st.set_page_config(page_title="Sınav Asistanı Ana Sayfa", layout="wide")

st.title("🏫 AI Sınav Okuma - Sinan S. V3.8")
st.info("Soldaki menüden işlem seçebilirsiniz.")

# --- TÜM SİSTEMİN HAFIZASI BURADA BAŞLAR ---
# Bu liste diğer sayfalarda da ortak kullanılacak.
if 'sinif_verileri' not in st.session_state:
    st.session_state.sinif_verileri = []

st.write(f"📂 Şu an hafızada **{len(st.session_state.sinif_verileri)}** adet okunmuş kağıt var.")

if len(st.session_state.sinif_verileri) > 0:
    if st.button("Tüm Hafızayı Temizle (Yeni Sınıf)"):
        st.session_state.sinif_verileri = []
        st.rerun()
