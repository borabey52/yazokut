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
    /* SOL MENÜ TASARIMI */
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
    
    /* BAŞLIK BOYUTLARI */
    h1 { font-size: 3rem !important; font-weight: 800 !important; color: #1E3A8A; }
    h2 { font-size: 2rem !important; font-weight: 700 !important; }
    h3 { font-size: 1.5rem !important; }

    /* --- KAMERA BUTONU TÜRKÇELEŞTİRME --- */
    button[kind="primary"] { color: transparent !important; }
    div[data-testid="stCameraInput"] button[kind="primary"]::after {
        content: "📸 FOTOĞRAFI ÇEK";
        color: white;
        font-weight: bold;
        position: absolute;
        left: 0; right: 0; top: 0; bottom: 0;
        display: flex; align-items: center; justify-content: center;
    }
    
    /* Temizleme butonu */
    div[data-testid="stCameraInput"] button[kind="secondary"] { color: transparent !important; }
    div[data-testid="stCameraInput"] button[kind="secondary"]::after {
        content: "🔄 Yeniden Çek";
        color: #31333F;
        font-weight: bold;
        position: absolute;
        left: 0; right: 0; top: 0; bottom: 0;
        display: flex; align-items: center; justify-content: center;
    }
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
    st.caption("Yazılı Oku v2.3 - Lite Model")

st.title("🧠 AI Sınav Okuma V5.3")
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
    
    SECENEK_DOSYA = "📂 Dosya Yükle"
    SECENEK_KAMERA = "📸 Kameradan Çek"
    
    mod = st.radio("Yükleme Yöntemi:", [SECENEK_DOSYA, SECENEK_KAMERA], horizontal=True)
    st.markdown("---")

    if mod == SECENEK_DOSYA:
        uploaded_file = st.file_uploader("Kağıt Seç", type=["jpg", "png", "jpeg"], key=f"file_{st.session_state.file_key}", label_visibility="collapsed")
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.session_state.yuklenen_resimler_v3.append(img)
            reset_file()
            st.rerun()
            
    elif mod == SECENEK_KAMERA:
        cam_img = st.camera_input("Fotoğrafı Çek", key=f"cam_{st.session_state.cam_key}", label_visibility="collapsed")
        if cam_img:
            img = Image.open(cam_img)
            st.session_state.yuklenen_resimler_v3.append(img)
            reset_cam()
            st.rerun()

    if len(st.session_state.yuklenen_resimler_v3) > 0:
        st.success(f"📎 {len(st.session_state.yuklenen_resimler_v3)} sayfa hafızada.")
        cols = st.columns(4)
        for i, img in enumerate(st.session_state.yuklenen_resimler_v3):
            with cols[i % 4]: st.image(img, use_container_width=True, caption=f"Sayfa {i+1}")
        if st.button("🗑️ Temizle", type="secondary", use_container_width=True): listeyi_temizle()

# ==========================================
# 3. YAPAY ZEKA İŞLEMİ
# ==========================================
st.markdown("---")

if st.button("✅ KAĞIDI OKU VE PUANLA", type="primary", use_container_width=True):
    if not SABIT_API_KEY:
        st.error("🚨 API Anahtarı Eksik! (Settings > Secrets)")
    elif len(st.session_state.yuklenen_resimler_v3) == 0:
        st.warning("⚠️ Kağıt yüklemediniz.")
    else:
        with st.spinner("Yapay zeka kağıdı okuyor..."):
            try:
                genai.configure(api_key=SABIT_API_KEY)
                
                # --- ÇÖZÜM BURADA: LİSTEDEKİ ÇALIŞAN MODEL ---
                model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05")
                
                base_prompt = """
                Sen öğretmensin. Sınav kağıdını oku ve puanla.
                ÇIKTI (SADECE JSON):
                {
                  "kimlik": { "ad_soyad": "...", "numara": "..." },
                  "degerlendirme": [
                    { "no": "1", "soru": "...", "cevap": "...", "puan": 0, "tam_puan": 10, "yorum": "..." }
                  ]
                }
                """
                content = [base_prompt]
                if ogretmen_promptu: content.append(f"NOT: {ogretmen_promptu}")
                if rubrik_img: content.extend(["CEVAP ANAHTARI:", rubrik_img])
                content.append("KAĞITLAR:")
                content.extend(st.session_state.yuklenen_resimler_v3)

                response = model.generate_content(content)
                json_text = extract_json(response.text)
                data = json.loads(json_text)

                kimlik = data.get("kimlik", {})
                sorular = data.get("degerlendirme", [])
                toplam = sum([float(x.get('puan', 0)) for x in sorular])
                maksimum = sum([float(x.get('tam_puan', 0)) for x in sorular])

                st.balloons()
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Öğrenci", kimlik.get("ad_soyad", "-"))
                    c2.metric("No", kimlik.get("numara", "-"))
                    c3.markdown(f"<h2 style='color:green'>{int(toplam)} / {int(maksimum)}</h2>", unsafe_allow_html=True)

                kayit = {"Ad Soyad": kimlik.get("ad_soyad", "-"), "Numara": kimlik.get("numara", "-"), "Toplam Puan": toplam}
                for s in sorular: kayit[f"Soru {s.get('no')}"] = s.get('puan', 0)
                st.session_state.sinif_verileri.append(kayit)
                st.toast("Kaydedildi!")

                for s in sorular:
                    p = s.get('puan', 0)
                    tp = s.get('tam_puan', 0)
                    renk = "green" if p==tp else "red" if p==0 else "orange"
                    with st.expander(f"Soru {s.get('no')} ({int(p)}/{int(tp)})"):
                        st.write(f"**Cevap:** {s.get('cevap')}")
                        st.markdown(f"**Yorum:** :{renk}[{s.get('yorum')}]")

            except Exception as e:
                st.error(f"Hata: {e}")
