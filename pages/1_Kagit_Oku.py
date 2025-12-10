import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- AYARLAR ---
st.set_page_config(page_title="Kağıt Oku", layout="wide")

# API Anahtarı
if "GOOGLE_API_KEY" in st.secrets:
    SABIT_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("API Anahtarı bulunamadı (Secrets).")
    st.stop()

# Hafıza
if 'yuklenen_resimler_v3' not in st.session_state: st.session_state.yuklenen_resimler_v3 = []
if 'sinif_verileri' not in st.session_state: st.session_state.sinif_verileri = []
if 'file_key' not in st.session_state: st.session_state.file_key = 0

def reset_file(): st.session_state.file_key += 1
def listeyi_temizle():
    st.session_state.yuklenen_resimler_v3 = []
    reset_file()
    st.rerun()

def extract_json(text):
    text = text.strip()
    if "```json" in text: text = text.split("```json")[1].split("```")[0]
    elif "```" in text: text = text.split("```")[1].split("```")[0]
    return text

# --- ARAYÜZ ---
st.title("📝 Kağıt Okuma Modülü")
col1, col2 = st.columns(2)

with col1:
    ogretmen_notu = st.text_area("Öğretmen Notu / Cevap Anahtarı:", height=100)

with col2:
    uploaded = st.file_uploader("Kağıt Yükle", type=["jpg","png","jpeg"], key=f"up_{st.session_state.file_key}")
    if uploaded:
        img = Image.open(uploaded)
        st.session_state.yuklenen_resimler_v3.append(img)
        reset_file()
        st.rerun()

    if st.session_state.yuklenen_resimler_v3:
        st.info(f"{len(st.session_state.yuklenen_resimler_v3)} sayfa yüklendi.")
        if st.button("Temizle"): listeyi_temizle()

st.markdown("---")

if st.button("✅ KAĞIDI OKU", type="primary", use_container_width=True):
    if not st.session_state.yuklenen_resimler_v3:
        st.warning("Önce kağıt yükleyin.")
    else:
        with st.spinner("Okunuyor..."):
            try:
                genai.configure(api_key=SABIT_API_KEY)
                # Model Tanımı
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = ["Bu kağıdı oku. Çıktıyı JSON ver.", ogretmen_notu]
                prompt.extend(st.session_state.yuklenen_resimler_v3)
                
                response = model.generate_content(prompt)
                st.success("İşlem Başarılı!")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Hata: {e}")
