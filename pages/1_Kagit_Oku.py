import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import re

# ==========================================
# 1. AYARLAR & GÜVENLİK
# ==========================================
st.set_page_config(page_title="AI Sınav Okuma", layout="wide")

# API Anahtarını Streamlit Secrets'tan alıyoruz (En güvenli yöntem)
if "GOOGLE_API_KEY" in st.secrets:
    SABIT_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Eğer secrets yoksa, hata vermemesi için boş geçiyoruz (Aşağıda kontrol edeceğiz)
    SABIT_API_KEY = ""

# Hafıza Başlatma (Resimler için)
if 'yuklenen_resimler_v3' not in st.session_state:
    st.session_state.yuklenen_resimler_v3 = []

# Hafıza Başlatma (Sınıf Listesi için)
if 'sinif_verileri' not in st.session_state:
    st.session_state.sinif_verileri = []

# Yükleme araçlarını sıfırlamak için anahtarlar
if 'cam_key' not in st.session_state: st.session_state.cam_key = 0
if 'file_key' not in st.session_state: st.session_state.file_key = 0

def reset_cam(): st.session_state.cam_key += 1
def reset_file(): st.session_state.file_key += 1

def listeyi_temizle():
    st.session_state.yuklenen_resimler_v3 = []
    reset_cam()
    reset_file()
    st.rerun()

# JSON Temizleme Fonksiyonu (Yapay zeka bazen ```json etiketi ekler, onu temizleriz)
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
# 2. ARAYÜZ TASARIMI
# ==========================================
st.title("🧠 AI Sınav Okuma Sistemi")
st.markdown("---")

col_sol, col_sag = st.columns([1, 1], gap="large")

# --- SOL TARAFA: KRİTERLER ---
with col_sol:
    st.header("1. Kriterler ve Ayarlar")
    ogretmen_promptu = st.text_area(
        "Öğretmen Notu / Cevap Anahtarı:",
        height=150,
        placeholder="Örn: 1. Soru 10 puan, cevap 'Ankara' olmalı. Gidiş yoluna puan ver..."
    )

    with st.expander("Görsel Cevap Anahtarı Yükle (İsteğe Bağlı)"):
        rubrik_dosyasi = st.file_uploader("Cevap Anahtarı Resmi", type=["jpg", "png", "jpeg"], key="rubrik_up")
        rubrik_img = Image.open(rubrik_dosyasi) if rubrik_dosyasi else None
        if rubrik_img: st.image(rubrik_img, width=200, caption="Cevap Anahtarı")

# --- SAĞ TARAFA: KAĞIT YÜKLEME ---
with col_sag:
    st.header("2. Öğrenci Kağıdı")
    
    # Yükleme Yöntemi Seçimi
    mod = st.radio("Yükleme Yöntemi:", ["📂 Dosya Yükle", "📸 Kamera"], horizontal=True)
    
    st.markdown("---")

    if mod == "📂 Dosya Yükle":
        uploaded_file = st.file_uploader("Kağıt Seç", type=["jpg", "png", "jpeg"], key=f"file_{st.session_state.file_key}")
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.session_state.yuklenen_resimler_v3.append(img)
            reset_file()
            st.rerun()
            
    else: # Kamera Modu
        cam_img = st.camera_input("Fotoğraf Çek", key=f"cam_{st.session_state.cam_key}")
        if cam_img:
            img = Image.open(cam_img)
            st.session_state.yuklenen_resimler_v3.append(img)
            reset_cam()
            st.rerun()

    # Yüklenen Resimleri Göster
    if len(st.session_state.yuklenen_resimler_v3) > 0:
        st.success(f"📎 Hafızada **{len(st.session_state.yuklenen_resimler_v3)}** sayfa var.")
        
        # Resimleri yan yana küçük göster
        cols = st.columns(4)
        for i, img in enumerate(st.session_state.yuklenen_resimler_v3):
            with cols[i % 4]:
                st.image(img, use_container_width=True, caption=f"Sayfa {i+1}")
        
        if st.button("🗑️ Hepsini Sil (Yeni Öğrenci)", type="secondary", use_container_width=True):
            listeyi_temizle()

# ==========================================
# 3. YAPAY ZEKA İŞLEMİ
# ==========================================
st.markdown("---")

# Butona basılınca çalışacak kısım
if st.button("✅ KAĞIDI OKU VE PUANLA", type="primary", use_container_width=True):
    
    # Önce Hata Kontrolleri
    if not SABIT_API_KEY:
        st.error("🚨 API Anahtarı Bulunamadı! Lütfen Streamlit ayarlarından 'Secrets' kısmına GOOGLE_API_KEY ekleyin.")
    elif len(st.session_state.yuklenen_resimler_v3) == 0:
        st.warning("⚠️ Lütfen önce en az bir sayfa sınav kağıdı yükleyin.")
    else:
        # Her şey tamamsa işlem başlar
        with st.spinner("Yapay zeka kağıdı inceliyor, lütfen bekleyin..."):
            try:
                # 1. Gemini Ayarları
                genai.configure(api_key=SABIT_API_KEY)
                
                # --- KRİTİK NOKTA: Model İsmi ---
                # Resim okuyabilen tek hızlı model budur.
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # 2. Prompt Hazırlığı
                ana_prompt = """
                Sen uzman bir öğretmensin. Görevin bu sınav kağıdını okumak ve puanlamak.
                
                ADIM 1: KİMLİK TESPİTİ
                - Kağıdın üzerindeki Öğrenci Adı, Soyadı ve Numarasını bul.
                - Bulamazsan "-" yaz.
                
                ADIM 2: PUANLAMA
                - Soruları tek tek incele.
                - Cevap anahtarı verilmişse ona uy, verilmemişse kendi bilgine göre adil puanla.
                
                ADIM 3: ÇIKTI FORMATI (ÇOK ÖNEMLİ)
                - Sonucu SADECE aşağıdaki JSON formatında ver. Başka hiçbir şey yazma.
                {
                  "kimlik": { "ad_soyad": "Öğrenci Adı", "numara": "123" },
                  "degerlendirme": [
                    { "no": "1", "soru": "Soru metni...", "cevap": "Öğrencinin cevabı...", "puan": 10, "tam_puan": 10, "yorum": "Eksiksiz" },
                    { "no": "2", "soru": "Soru metni...", "cevap": "Öğrencinin cevabı...", "puan": 5, "tam_puan": 10, "yorum": "Yarısı doğru" }
                  ]
                }
                """
                
                # Prompt parçalarını birleştiriyoruz (Metin + Resimler)
                icerik = [ana_prompt]
                
                if ogretmen_promptu:
                    icerik.append(f"ÖĞRETMENİN EK NOTLARI: {ogretmen_promptu}")
                
                if rubrik_img:
                    icerik.append("CEVAP ANAHTARI GÖRSELİ:")
                    icerik.append(rubrik_img)
                
                icerik.append("ÖĞRENCİ KAĞITLARI:")
                # Yüklenen tüm resimleri ekle
                icerik.extend(st.session_state.yuklenen_resimler_v3)

                # 3. Yapay Zekaya Gönder
                response = model.generate_content(icerik)
                
                # 4. Gelen Cevabı İşle
                json_metni = extract_json(response.text)
                veri = json.loads(json_metni)

                # Verileri Ayrıştır
                kimlik = veri.get("kimlik", {})
                sorular = veri.get("degerlendirme", [])

                # Toplam Puan Hesapla
                toplam_puan = sum([float(x.get('puan', 0)) for x in sorular])
                maksimum_puan = sum([float(x.get('tam_puan', 0)) for x in sorular])

                # Kutlama Efekti
                st.balloons()

                # --- SONUÇLARI EKRANA YAZDIR ---
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("👤 Öğrenci", kimlik.get("ad_soyad", "Bilinmiyor"))
                    c2.metric("🔢 Numara", kimlik.get("numara", "-"))
                    # Puanı yeşil ve büyük yazdır
                    c3.markdown(f"<h1 style='color:green;'>Not: {int(toplam_puan)} / {int(maksimum_puan)}</h1>", unsafe_allow_html=True)

                # --- SONUÇLARI HAFIZAYA KAYDET (Excel tablosu için) ---
                kayit_verisi = {
                    "Ad Soyad": kimlik.get("ad_soyad", "Bilinmiyor"),
                    "Numara": kimlik.get("numara", "-"),
                    "Toplam Puan": toplam_puan
                }
                # Her sorunun puanını tabloya sütun olarak ekle
                for soru in sorular:
                    etiket = f"Soru {soru.get('no')}"
                    kayit_verisi[etiket] = soru.get('puan', 0)
                
                st.session_state.sinif_verileri.append(kayit_verisi)
                st.success(f"💾 {kimlik.get('ad_soyad')} başarıyla sınıf listesine eklendi!")

                # --- DETAYLI SORU ANALİZİ GÖSTERİMİ ---
                st.subheader("📝 Detaylı Değerlendirme")
                for soru in sorular:
                    p = float(soru.get('puan', 0))
                    tp = float(soru.get('tam_puan', 0))
                    
                    # Renklendirme Mantığı
                    if p == tp: renk = "green"    # Tam puan
                    elif p == 0: renk = "red"     # Sıfır puan
                    else: renk = "orange"         # Kısmi puan

                    with st.expander(f"Soru {soru.get('no')} - Puan: {int(p)}/{int(tp)}", expanded=True):
                        st.write(f"**Soru:** {soru.get('soru')}")
                        st.write(f"**Öğrenci Cevabı:** {soru.get('cevap')}")
                        st.markdown(f"**Yorum:** :{renk}[{soru.get('yorum')}]")

            except Exception as e:
                st.error("Bir hata oluştu!")
                st.error(f"Hata Detayı: {e}")
                st.info("İpucu: Eğer '404' veya 'model not found' hatası alıyorsanız, requirements.txt dosyasını kontrol edin.")
