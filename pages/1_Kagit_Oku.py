import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re

# ==========================================
# 1. AYARLAR & HAFIZA
# ==========================================
st.set_page_config(page_title="AI Sınav Asistanı v3.8", layout="wide")

# --- DÜZELTME 1: ŞİFREYİ GÜVENLİ KASADAN AL ---
if "GOOGLE_API_KEY" in st.secrets:
    SABIT_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🚨 API Anahtarı bulunamadı! Lütfen Streamlit ayarlarından 'Secrets' kısmına ekleyin.")
    st.stop()

# Hafıza Ayarları
if 'yuklenen_resimler_v3' not in st.session_state:
    st.session_state.yuklenen_resimler_v3 = []

if 'sinif_verileri' not in st.session_state:
    st.session_state.sinif_verileri = []

if 'cam_key' not in st.session_state: st.session_state.cam_key = 0
if 'file_key' not in st.session_state: st.session_state.file_key = 0

def reset_cam(): st.session_state.cam_key += 1
def reset_file(): st.session_state.file_key += 1
def listeyi_temizle():
    st.session_state.yuklenen_resimler_v3 = []
    st.session_state.cam_key += 1
    st.session_state.file_key += 1
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
# 2. ARAYÜZ
# ==========================================
st.title("🧠 AI Yazılı Oku (Sinan S. v3.8)")
st.markdown("---")

col_sol, col_sag = st.columns([1, 1], gap="large")

with col_sol:
    st.header("1. Kriterler")
    ogretmen_promptu = st.text_area("Öğretmen Notu:", height=100, placeholder="Örn: Yapay zekanın dikkat etmesini istedikleriniz...")
    with st.expander("Cevap Anahtarı Yükle (İsteğe Bağlı)"):
        rubrik_dosyasi = st.file_uploader("Fotoğraf Seç", type=["jpg", "png", "jpeg"], key="rubrik_up")
        rubrik_img = Image.open(rubrik_dosyasi) if rubrik_dosyasi else None
        if rubrik_img: st.image(rubrik_img, width=200)

with col_sag:
    st.subheader("2. Öğrenci Kağıdı")
    mod = st.radio("Çalışma Modunu Seçin:", ["📂 Dosya Yükle (PC / Galeri)", "📸 Canlı Kamera (Sadece Mobil)"], horizontal=True)
    st.markdown("---")

    if "Dosya" in mod:
        st.info("Bilgisayardan veya galeriden seçin:")
        uploaded_file = st.file_uploader("Dosya Seç", type=["jpg", "png", "jpeg"], key=f"file_{st.session_state.file_key}")
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.session_state.yuklenen_resimler_v3.append(img)
            reset_file()
            st.rerun()
    else:
        st.warning("Kamera izni ister.")
        cam_img = st.camera_input("Fotoğrafı Çek", key=f"cam_{st.session_state.cam_key}")
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
        if st.button("🗑️ HEPSİNİ SİL", use_container_width=True, type="secondary"): listeyi_temizle()

# ==========================================
# 3. İŞLEM
# ==========================================
st.markdown("---")

if st.button("✅ KAĞIDI OKU VE DEĞERLENDİR", type="primary", use_container_width=True):
    if len(st.session_state.yuklenen_resimler_v3) == 0:
        st.warning("Lütfen önce kağıt yükleyin.")
    else:
        with st.spinner("Yapay zeka analiz yapıyor..."):
            try:
                genai.configure(api_key=SABIT_API_KEY)
                
                # --- DÜZELTME 2: MODEL TANIMINI İÇERİ ALDIM ---
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                base_prompt = """
                Rol: Deneyimli Türk Öğretmeni.
                Görev: Öğrenci kağıdını analiz et.
                ADIM 1: KİMLİK (İsim, Sınıf, No bul).
                ADIM 2: PUANLAMA (Her soruyu puanla).
                ÇIKTI (JSON):
                {
                  "kimlik": { "ad_soyad": "...", "sinif": "...", "numara": "..." },
                  "degerlendirme": [
                    { "no": "1", "soru": "...", "cevap": "...", "puan": 10, "tam_puan": 10, "yorum": "..." }
                  ]
                }
                """
                
                prompt_parts = [base_prompt]
                if ogretmen_promptu: prompt_parts.append(f"ÖĞRETMEN NOTU: {ogretmen_promptu}")
                if rubrik_img: prompt_parts.extend(["CEVAP ANAHTARI:", rubrik_img])
                prompt_parts.append("ÖĞRENCİ KAĞITLARI:")
                prompt_parts.extend(st.session_state.yuklenen_resimler_v3)

                response = model.generate_content(prompt_parts)
                json_text = extract_json(response.text)
                data = json.loads(json_text)

                kimlik = data.get("kimlik", {})
                sorular = data.get("degerlendirme", [])

                st.balloons()

                toplam = sum([float(x.get('puan', 0)) for x in sorular])
                max_toplam = sum([float(x.get('tam_puan', 0)) for x in sorular])

                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("👤 Öğrenci", kimlik.get("ad_soyad", "-"))
                    c2.metric("🏫 Sınıf", kimlik.get("sinif", "-"))
                    c3.metric("🔢 No", kimlik.get("numara", "-"))
                    c4.markdown(f"<h1 style='color:#28a745; margin:0;'>{int(toplam)} / {int(max_toplam)}</h1>", unsafe_allow_html=True)

                # VERİYİ KAYDET
                ogrenci_verisi = {
                    "Ad Soyad": kimlik.get("ad_soyad", "Bilinmeyen"),
                    "Numara": kimlik.get("numara", "-"),
                    "Toplam Puan": toplam,
                }
                for soru in sorular:
                    lbl = f"Soru {soru.get('no')}"
                    ogrenci_verisi[lbl] = soru.get('puan', 0)
                st.session_state.sinif_verileri.append(ogrenci_verisi)
                st.toast(f"💾 {kimlik.get('ad_soyad')} listeye eklendi!")

                # DETAYLARI GÖSTER
                for soru in sorular:
                    p = soru.get('puan', 0)
                    tp = soru.get('tam_puan', 0)
                    renk, ikon = ("green", "✅") if tp>0 and (p/tp)>=0.8 else ("red", "❌") if p==0 else ("orange", "⚠️")
                    
                    with st.container(border=True):
                        c1, c2 = st.columns([9, 1])
                        c1.markdown(f"#### {ikon} Soru {soru.get('no')}: {soru.get('soru')}")
                        c2.markdown(f"### :{renk}[{p}/{tp}]")
                        st.caption(f"**Öğrenci:** {soru.get('cevap', '-')}")
                        if renk=="green": st.success(soru.get('yorum'))
                        elif renk=="orange": st.warning(soru.get('yorum'))
                        else: st.error(soru.get('yorum'))

            except Exception as e:
                st.error(f"Hata oluştu: {e}")
