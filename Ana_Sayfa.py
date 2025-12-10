import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# ==========================================
# 1. AYARLAR & TASARIM (CSS)
# ==========================================
st.set_page_config(page_title="AI Sınav Okuma", layout="wide")

st.markdown("""
    <style>
    /* --- SOL MENÜ TASARIMI --- */
    [data-testid="stSidebarNav"] a {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-decoration: none !important;
        color: #31333F !important;
        font-weight: 700;
        display: block;
        text-align: center;
        border: 1px solid #dcdcdc;
        transition: all 0.3s;
    }
    [data-testid="stSidebarNav"] a:hover {
        background-color: #e6e9ef;
        transform: scale(1.02);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-color: #b0b0b0;
    }
    
    /* --- BAŞLIK BOYUTLARI --- */
    h1 { font-size: 3rem !important; font-weight: 800 !important; color: #1E3A8A; }
    h2 { font-size: 2rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# API Anahtarı
if "GOOGLE_API_KEY" in st.secrets:
    SABIT_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    SABIT_API_KEY = ""

# --- HAFIZA BAŞLATMA ---
if 'yuklenen_resimler_v3' not in st.session_state: st.session_state.yuklenen_resimler_v3 = []
if 'sinif_verileri' not in st.session_state: st.session_state.sinif_verileri = []
if 'cam_key' not in st.session_state: st.session_state.cam_key = 0
if 'file_key' not in st.session_state: st.session_state.file_key = 0

def reset_cam(): st.session_state.cam_key += 1
def reset_file(): st.session_state.file_key += 1

def listeyi_temizle():
    st.session_state.yuklenen_resimler_v3 = []
    reset_cam()
    reset_file()
    st.rerun()

def tam_hafiza_temizligi():
    st.session_state.sinif_verileri = []
    st.session_state.yuklenen_resimler_v3 = []
    st.toast("🧹 Tüm sınıf verileri ve hafıza temizlendi!", icon="🗑️")
    st.rerun()

def extract_json(text):
    text = text.strip()
    try:
        if "```json" in text: text = text.split("```json")[1].split("```")[0]
        elif "```" in text: text = text.split("```")[1].split("```")[0]
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0: return text[start:end]
        return text
    except:
        return text

# ==========================================
# 2. ARAYÜZ (Ana Sayfa)
# ==========================================
with st.sidebar:
    st.header("⚙️ Durum")
    st.info(f"📂 Okunan Kağıt: **{len(st.session_state.sinif_verileri)}**")
    if len(st.session_state.sinif_verileri) > 0:
        if st.button("🚨 Yeni Sınıf (Hafızayı Sil)", type="primary", use_container_width=True):
            tam_hafiza_temizligi()
    st.divider()
    st.caption("Yazılı Oku v2.1 - Tasarım")

st.title("🧠 AI Sınav Okuma V5.2")
st.markdown("---")

col_sol, col_sag = st.columns([1, 1], gap="large")

# SOL: Ayarlar
with col_sol:
    st.header("1. İstekler (Varsa)")
    ogretmen_promptu = st.text_area("Öğretmen Notu:", height=150, placeholder="Değerlendirme sırasında yapay zekaya direktiflerinizi yazabilirsiniz.")
    with st.expander("Görsel Cevap Anahtarı (Opsiyonel)"):
        rubrik_dosyasi = st.file_uploader("Cevap Anahtarı Resmi", type=["jpg", "png", "jpeg"], key="rubrik_up")
        rubrik_img = Image.open(rubrik_dosyasi) if rubrik_dosyasi else None
        if rubrik_img: st.image(rubrik_img, width=200)

# SAĞ: Yükleme
with col_sag:
    st.header("2. Öğrenci Kağıdı")
    
    # --- DÜZELTME BURADA YAPILDI ---
    # Seçenek ismini ve IF
