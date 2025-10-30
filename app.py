import gradio as gr
import json
import os
from dotenv import load_dotenv
import time
import traceback 

# --- GEREKLİ IMPORTLAR (LANGCHAIN YOK) ---
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import chromadb

# --- Ayarlar ve API Anahtarı ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 
DATA_FILE = "travel_routes.json"
VECTOR_DB_PATH = "/tmp/vector_db_gradio_final" # DB Klasör adı (Hugging Face için /tmp klasörü)
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"

# --- Hata Kontrolü: API Anahtarı ---
API_KEY_ERROR = False 
if not GOOGLE_API_KEY:
    print("🚨 HATA: Google API anahtarı .env dosyasında bulunamadı!")
    print("Lütfen proje ana klasöründe .env dosyası oluşturup GOOGLE_API_KEY='...' anahtarınızı ekleyin.")
    API_KEY_ERROR = True
else:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"🚨 HATA: Google API anahtarı yapılandırılırken hata oluştu: {e}")
        API_KEY_ERROR = True

# --- Modelleri ve DB'yi Tutacak Global Değişkenler ---
llm = None
embeddings_model = None
vector_collection = None 
data_json = None 

# ====================================================
# >>> YENİ EKLEME 1: Coğrafi Yardımcı Fonksiyonlar <<<
# ====================================================

def calculate_distance(lat1, lon1, lat2, lon2):
    """Basit Öklid mesafesi karesini döndürür (Sıralama için)."""
    return (lat1 - lat2)**2 + (lon1 - lon2)**2

def generate_and_order_route(city, day_plan_text):
    """LLM'in oluşturduğu metinsel rotayı alır, koordinatları çeker ve en yakın komşu mantığıyla yeniden sıralar."""
    global data_json

    if not data_json or city not in data_json or "Places" not in data_json[city]:
        return f"❌ Rota oluşturmak için yeterli yer detayı bilgisi ({city} için) bulunamadı."

    city_places_data = data_json[city]["Places"]
    
    ordered_places = []
    sentences = day_plan_text.replace("\n", " ").split('.')
    
    for sentence in sentences:
        for place_name in city_places_data.keys():
            if place_name in sentence and place_name not in ordered_places:
                ordered_places.append(place_name)
                break 

    if not ordered_places:
        return f"⚠️ Rota metni ayrıştırılamadı. LLM'den gelen formatı kontrol edin:\n{day_plan_text}"

    start_place_name = ordered_places[0]
    start_coords = city_places_data.get(start_place_name, {})
    
    if not all(k in start_coords for k in ["latitude", "longitude"]):
        return f"❌ Başlangıç yerinin ({start_place_name}) koordinatları eksik. Sıralama yapılamaz."
    
    start_lat, start_lon = start_coords["latitude"], start_coords["longitude"]
    
    remaining_places = ordered_places[1:]
    final_ordered_route = [start_place_name]
    current_lat, current_lon = start_lat, start_lon
    
    while remaining_places:
        best_next_place = None
        min_dist = float('inf')

        for place_name in remaining_places:
            place_data = city_places_data.get(place_name, {})
            if place_data and all(k in place_data for k in ["latitude", "longitude"]):
                dist = calculate_distance(current_lat, current_lon, place_data["latitude"], place_data["longitude"])
                
                if dist < min_dist:
                    min_dist = dist
                    best_next_place = place_name
        
        if best_next_place:
            final_ordered_route.append(best_next_place)
            current_lat = city_places_data[best_next_place]["latitude"]
            current_lon = city_places_data[best_next_place]["longitude"]
            remaining_places.remove(best_next_place)
        else:
            final_ordered_route.extend(remaining_places)
            break

    route_output = f"**🗺️ Önerilen Optimal Rota (Başlangıç: {start_place_name})**:\n"
    for i, place in enumerate(final_ordered_route):
        route_output += f"{i+1}. {place}\n"
    
    return route_output


# ====================================================
# >>> BAŞLANGIÇ FONKSİYONLARI (DB OLUŞTURMA GÜNCELLENDİ) <<<
# ====================================================

def initialize_models_and_db():
    """Gerekli modelleri ve veritabanını yükler/oluşturur."""
    global llm, embeddings_model, vector_collection, data_json, API_KEY_ERROR

    if API_KEY_ERROR: 
        print("❌ API Anahtarı hatası nedeniyle başlatma işlemi durduruldu.")
        return False 

    # 1. JSON verisini yükle
    try:
        if data_json is None: 
            if not os.path.exists(DATA_FILE):
                raise FileNotFoundError(f"Veri dosyası bulunamadı: {DATA_FILE}")
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data_json = json.load(f)
            print("✅ JSON Verisi başarıyla yüklendi.")
    except Exception as e:
        print(f"🚨 HATA: JSON verisi yüklenemedi! {e}")
        API_KEY_ERROR = True 
        return False

    # 2. LLM yükle (Gemini)
    if llm is None:
        try:
            print("⏳ Google Gemini LLM yükleniyor...")
            generation_config = {"temperature": 0.7, "top_p": 0.95, "top_k": 64}
            llm = genai.GenerativeModel(
              model_name="gemini-2.5-flash", 
              generation_config=generation_config
            )
            print("✅ Google Gemini LLM Başarıyla Yüklendi.")
        except Exception as e:
            print(f"🚨 HATA: Google Gemini LLM başlatılırken hata oluştu: {e}")
            API_KEY_ERROR = True 
            return False

    # 3. Embedding modelini yükle
    if embeddings_model is None:
        try:
            print(f"⏳ Embedding modeli ({embedding_model_name}) yükleniyor/indiriliyor...")
            start_time = time.time()
            embeddings_model = SentenceTransformer(
                model_name_or_path=embedding_model_name,
                device='cpu' 
            )
            end_time = time.time()
            print(f"✅ Embedding Modeli Başarıyla Yüklendi. ({end_time - start_time:.2f} saniye)")
        except Exception as e:
            print(f"🚨 HATA: Embedding modeli yüklenirken hata oluştu: {e}")
            API_KEY_ERROR = True 
            return False

    # 4. Vektör Veritabanını yükle/oluştur
    if vector_collection is None:
        try:
            client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
            collection_name = "travel_routes_collection"
            vector_collection = client.get_or_create_collection(name=collection_name)
            
            if vector_collection.count() == 0:
                print(f"⏳ Vektör veritabanı '{VECTOR_DB_PATH}' ilk kez dolduruluyor... (Gelişmiş Strateji)")
                start_time = time.time()
                
                documents_to_add = []
                metadatas_to_add = []
                ids_to_add = []
                doc_id_counter = 0

                for city, city_data in data_json.items():
                    # 1. BELGE TÜRÜ: Şehrin Genel Planı ve Kategorileri
                    content_genel = f"# Şehir: {city}\n\n## Günlük Planlar\n"
                    if "Days" in city_data and isinstance(city_data["Days"], dict):
                        sorted_days = sorted(city_data["Days"].keys(), key=lambda x: int(x) if x.isdigit() else float('inf'))
                        for day_num in sorted_days: activities = city_data["Days"][day_num]; content_genel += f"**{day_num}. Gün:** {', '.join(activities)}\n"
                    content_genel += "\n## Aktivite Kategorileri\n"
                    for category, places in city_data.items():
                        if category not in ["Days", "Places"] and isinstance(places, list): content_genel += f"**{category}:** {', '.join(places)}\n"
                    
                    documents_to_add.append(content_genel.strip())
                    metadatas_to_add.append({"source_city": city, "type": "Genel Plan"})
                    ids_to_add.append(f"doc_city_{doc_id_counter}")
                    doc_id_counter += 1

                    # 2. BELGE TÜRÜ: Her Yer İçin Ayrı Ayrı (Detaylar)
                    if "Places" in city_data and isinstance(city_data["Places"], dict):
                        for place_name, place_details in city_data["Places"].items():
                            content_yer = f"# Yer: {place_name} ({city})\n\n"
                            if "description" in place_details: content_yer += f"Açıklama: {place_details['description']}\n"
                            if "tips" in place_details: content_yer += f"İpucu: {place_details['tips']}\n"
                            categories_for_place = []
                            for category, places_list in city_data.items():
                                if category not in ["Days", "Places"] and isinstance(places_list, list) and place_name in places_list:
                                    categories_for_place.append(category)
                            if categories_for_place: content_yer += f"Kategoriler: {', '.join(categories_for_place)}\n"
                            
                            # --- KORDINAT EKLEME İŞLEMİ BURADA YAPILDI ---
                            place_lat = place_details.get("latitude")
                            place_lon = place_details.get("longitude")

                            metadata_for_place = {
                                "source_city": city, 
                                "type": "Yer Detayı", 
                                "place_name": place_name
                            }
                            
                            # Eğer koordinatlar varsa metadata'ya ekle
                            if isinstance(place_lat, (int, float)) and isinstance(place_lon, (int, float)):
                                metadata_for_place["latitude"] = place_lat
                                metadata_for_place["longitude"] = place_lon
                            # --- KORDINAT EKLEME BİTTİ ---

                            documents_to_add.append(content_yer.strip())
                            metadatas_to_add.append(metadata_for_place) # Güncellenmiş metadata
                            ids_to_add.append(f"doc_place_{doc_id_counter}")
                            doc_id_counter += 1
                
                print(f"   - {len(documents_to_add)} adet daha odaklı Document oluşturuldu.")
                print("   - Vektörler (Embeddings) oluşturuluyor...")
                embeddings_list = embeddings_model.encode(documents_to_add).tolist()
                print("   - Vektörler oluşturuldu.")
                print(f"   - Veritabanına ekleniyor...")
                if documents_to_add:
                    vector_collection.add(embeddings=embeddings_list, documents=documents_to_add, metadatas=metadatas_to_add, ids=ids_to_add)
                end_time = time.time()
                print(f"✅ Vektör veritabanı oluşturuldu ve kaydedildi. ({end_time - start_time:.2f} saniye)")
            else:
                print(f"✅ Mevcut vektör veritabanı '{VECTOR_DB_PATH}' başarıyla yüklendi ({vector_collection.count()} doküman).")

        except Exception as e:
            print(f"🚨 HATA: Vektör veritabanı oluşturulurken/yüklenirken hata oluştu: {e}\n{traceback.format_exc()}")
            API_KEY_ERROR = True 
            return False

    return True 

# ====================================================
# >>> RAG FONKSİYONU (Konum Filtresi ve Rota Sıralama Eklendi) <<<
# ====================================================

def ask_travel_bot(user_question, user_location=None): 
    """
    Gradio'nun ana RAG fonksiyonu. user_location parametresi eklendi.
    """
    global llm, embeddings_model, vector_collection, data_json, API_KEY_ERROR

    if API_KEY_ERROR or not llm or not embeddings_model or not vector_collection:
        error_msg = "🚨 Üzgünüm, bir başlangıç hatası nedeniyle cevap veremiyorum. Lütfen terminal loglarını kontrol edin."
        return error_msg, [], "Hata: Sistem başlatılamadı." 

    print(f"\n❓ Kullanıcı Sorusu: {user_question}")
    full_response = "" 
    images_found = set()
    context = "Bağlam bulunamadı." 
    is_route_request = False
    
    try:
        start_time = time.time()
        where_filter = {}
        city_to_check = None 
        bounding_box_degrees = 0.015 # Yaklaşık 1.6 km

        # 1. Konum Filtresi Hazırlığı
        if user_location:
            try:
                lat_str, lon_str = user_location.split(',')
                user_lat = float(lat_str.strip())
                user_lon = float(lon_str.strip())
                print(f"🌍 Konum Filtresi Hazırlanıyor: ({user_lat}, {user_lon})")
                where_filter = {
                    "$and": [
                        {"latitude": {"$gte": user_lat - bounding_box_degrees, "$lte": user_lat + bounding_box_degrees}},
                        {"longitude": {"$gte": user_lon - bounding_box_degrees, "$lte": user_lon + bounding_box_degrees}}
                    ]
                }
            except:
                print("🚨 Konum formatı hatalı. Koordinat filtresi uygulanmayacak.")
        
            
        # 2. Soruyu Vektöre Çevir (Filtre varsa tekrar yapmamak için yukarı taşıdık)
        query_vector = embeddings_model.encode([user_question])[0].tolist()

        # 3. ChromaDB'de Arama Yap
        
        # Filtreleme sadece 'where_filter' doluysa yapılır.
        # Rota oluşturma dışındaki normal sorular için 'user_location' boşsa, filtreyi boş bırak.
        if where_filter:
            print(f"🔍 ChromaDB Sorgusu: Konum Filtresi Uygulanıyor.")
            results = vector_collection.query(
                query_embeddings=[query_vector],
                n_results=10, 
                include=["metadatas", "documents"],
                where=where_filter # Konum filtresi
            )
        else:
            print("🔍 ChromaDB Sorgusu: Konum Filtresi Uygulanmıyor (Normal RAG).")
            results = vector_collection.query(
                query_embeddings=[query_vector],
                n_results=10, # 10 alakalı sonuç getir
                include=["metadatas", "documents"] 
            )
        
        # 4. Bağlamı (Context) Oluştur
        context = "\n\n---\n\n".join(results['documents'][0]) if results['documents'] else "Bilgi bulunamadı."
        print(f"📚 Bulunan Bağlam (Context): {context[:200]}...")
        # --- YENİ ŞEHİR TESPİTİ (RAG SONUÇLARINDAN) ---
        # Rota optimizasyonu için 'city_to_check' değişkenini burada dolduruyoruz.
        if results['metadatas'] and results['metadatas'][0]:
            # Bulunan ilk dokümanın metadatasından şehri al
            metadata_found = results['metadatas'][0][0] 
            if 'source_city' in metadata_found:
                city_to_check = metadata_found['source_city']
                print(f"📍 RAG ile Şehir Tespiti Başarılı: {city_to_check}")
        # --- YENİ ŞEHİR TESPİTİ BİTTİ ---

        # 5. Prompt Hazırlığı
        current_city = city_to_check if city_to_check else "ilgili şehir"
        
        if "günlük gezi planı oluştur" in user_question.lower() or "rota oluştur" in user_question.lower():
            is_route_request = True
            template = f"""Sen son derece organize bir seyahat planlayıcısısın. Kullanıcının isteği doğrultusunda, sadece {current_city} şehri için en verimli 3 günlük gezi rotasını oluştur.
Planı oluştururken, sana sağlanan bağlamdaki yerleri kullan ve rotayı mantıksal bir sıraya koy.
**Çıktı Formatı (ÇOK ÖNEMLİ):**
Cevabının tamamı, her gün için bir ana fikir cümlesi ve ardından o gün yapılacak aktivitelerin **SIRALI LİSTESİ** olmalıdır.
**Planın tamamını TEK BİR METİN BLOKU** olarak oluştur.

ÖRNEK ÇIKTI FORMATI (Kopyalama yapma, kendi planını oluştur):
"Paris'te ilk gün Eyfel Kulesi çevresindeki aktivitelerle başlıyoruz. Ardından Seine Nehri'ne geçilecek.
1. Gün: Eiffel Kulesi. Trocadéro Bahçeleri. Seine Nehri Turu.
2. Gün: Louvre Müzesi. Notre Dame Katedrali'ni dışarıdan görerek Montmartre'a geçeceğiz.
3. Gün: Champs-Élysées'de yürüyüş. Arc de Triomphe'u ziyaret. Luxembourg Bahçeleri'nde mola."

Bağlam (Context):
{context}

Soru (Question):
{user_question}

{current_city} Şehri İçin 3 Günlük Gezi Planı (Sıralı Metin): """
        else:
            is_route_request = False
            template = f"""Sen yardımsever bir seyahat asistanısın. Sadece sana verilen aşağıdaki bağlamı (context) kullanarak kullanıcının sorusunu cevapla.
Bağlam; şehirler hakkında günlük planlar, aktivite kategorileri (Kültür, Doğa vb.) ve önemli yerler hakkında detaylar (açıklama, ipucu) içerir.
Sana verilen bağlamda 10 farklı şehirden alakasız bilgiler olabilir. Sen sadece kullanıcının sorusuyla ilgili olan parçaları dikkate al.
Örneğin, soru "Eiffel Kulesi" hakkında ise, bağlamdaki "Topkapı Sarayı" veya "Galata Kulesi" bilgilerini dikkate alma.
Sadece soruyla ilgili bilgileri kullanarak cevap üret.
Eğer cevap bağlamda açıkça yoksa, kibarca 'Bu konuda sağlanan bilgiler arasında detay bulamadım.' de. Tahmin yürütme.

Bağlam (Context):
{context}

Soru (Question):
{user_question}

Cevap (Türkçe): """
        
        # 6. Gemini'yi Çağır (Generation)
        print("🤖 Gemini'den cevap bekleniyor...")
        response = llm.generate_content(template)
        
        if not response.parts:
             full_response = "Gemini'den bir cevap alınamadı. Lütfen tekrar deneyin."
             print("🚨 HATA: Gemini'den boş cevap (no parts) alındı.")
        else:
             llm_text_output = response.text
             print(f"🤖 Ham Cevap Alındı: {llm_text_output[:100]}...")

        end_time = time.time()
        print(f"   -> Cevap {end_time - start_time:.2f} saniyede üretildi.")

        # 7. Rota Oluşturma Mantığını Uygula
        if is_route_request and city_to_check and "Gün" in llm_text_output:
             full_response = generate_and_order_route(city_to_check, llm_text_output)
        else:
             full_response = llm_text_output
        
        # 8. Görsel Bulma
        if data_json and not is_route_request: 
            for city, city_data in data_json.items():
                if "Places" in city_data:
                    for place, details in city_data["Places"].items():
                        if place.lower() in full_response.lower() and "image" in details and details["image"]:
                            image_path = details["image"]
                            if os.path.exists(image_path):
                                images_found.add(image_path) 
                                print(f"🖼️ Görsel bulundu (metinden): {image_path}")
        
        unique_images = list(images_found)
        if unique_images:
             print(f"   -> Arayüze {len(unique_images)} görsel gönderiliyor.")
        
        return full_response, unique_images, context

    except Exception as e:
        error_msg = f"😔 Soru işlenirken bir hata oluştu: {e}"
        if "API key not valid" in str(e) or "API_KEY_INVALID" in str(e) or "404" in str(e) or "quota" in str(e):
            error_msg = f"🚨 HATA: Google API ile ilgili bir sorun oluştu: {e}"
        print(f"ERROR: {error_msg}\n{traceback.format_exc()}")
        return error_msg, [], context 

# --- Modelleri Başlat ---
print("--- Uygulama Başlatılıyor ---")
models_ready = False
if not API_KEY_ERROR: 
    models_ready = initialize_models_and_db()
print("--- Başlatma Tamamlandı ---")

# --- Gradio Arayüzü (Orijinal Tek Sütunlu Yapı) ---
with gr.Blocks(theme=gr.themes.Soft(), title="RAG Seyahat Asistanı") as demo:
    gr.Markdown("# 🗺️ RAG Seyahat Asistanı")
    gr.Markdown("Şehir planları, kategori önerileri ve yer detayları hakkında sorular sorun.")
    
    # --- Kontrol ve Girdi Alanları ---
    gr.Markdown("### ⚙️ Kontrol Paneli")
    city_dropdown = gr.Dropdown(
        label="Şehir Seçin",
        choices=list(data_json.keys()) if data_json else [],
        value=None
    )
    category_radio = gr.Radio(
        label="Konu Seçin",
        choices=["Genel Plan", "Kültür", "Doğa", "Yemek", "Alışveriş", "Yer Detayı"],
        value="Genel Plan"
    )
    quick_prompt_btn = gr.Button("Soruyu Hazırla 🚀")
    
    status_indicator = gr.Textbox("Başlatılıyor...", label="Sistem Durumu", interactive=False)
    if not models_ready:
         status_indicator.value = "🚨 HATA! Terminali kontrol edin."
    else:
         status_indicator.value = "✅ Hazır"
    gr.Markdown("---")

    # --- Sohbet Alanı ---
    answer_output = gr.Markdown(label="🤖 Cevap")
    image_gallery = gr.Gallery(label="📷 İlgili Görseller", show_label=True, elem_id="gallery", columns=2, height="auto")
    
    question_input = gr.Textbox(label="📍 Sorunuzu yazın", placeholder="Örn: İstanbul'da Balık-Ekmek nerede yenir? / Paris için rota oluştur.")
    
    with gr.Row():
        submit_button = gr.Button("Gönder", variant="primary", scale=3)
        clear_button = gr.ClearButton(
            components=[question_input, answer_output, image_gallery],
            value="Sohbeti Temizle 🗑️",
            scale=1
        )
        
    # --- Konum Girişi (Rota Sıralaması için) ---
    location_input = gr.Textbox(
        label="Mevcut Konumunuz (Rota Sıralaması için Koordinat Girin)", 
        placeholder="Örn: 48.8584, 2.2945 (Enlem, Boylam)"
    )

    gr.Examples(
        examples=[
            "Paris'te kültürel neler yapılır?", 
            "Eiffel Kulesi için ipucu var mı?",
            "Paris için 3 günlük en verimli gezi rotasını oluştur." # Yeni test
        ],
        inputs=question_input
    )
    
    with gr.Accordion("Geliştirici: RAG Bağlam (Context) Paneli", open=False):
        debug_output = gr.Textbox(label="Bulunan Bağlam", interactive=False, lines=10)

    # --- Fonksiyon Bağlantıları ---
    def create_quick_prompt(city, category):
        if not city:
            return gr.update(value="Lütfen önce bir şehir seçin.")
        if category == "Genel Plan":
            return f"{city} için 3 günlük gezi planı nedir?"
        return f"{city} şehrinde {category.lower()} ile ilgili ne gibi aktiviteler veya yerler var?"

    quick_prompt_btn.click(
        fn=create_quick_prompt,
        inputs=[city_dropdown, category_radio],
        outputs=[question_input]
    )
    
    # Fonksiyon çağrısı güncellendi: İki input alıyor
    submit_button.click(
        fn=ask_travel_bot, 
        inputs=[question_input, location_input], 
        outputs=[answer_output, image_gallery, debug_output] 
    )
    question_input.submit(
        fn=ask_travel_bot, 
        inputs=[question_input, location_input], 
        outputs=[answer_output, image_gallery, debug_output]
    )

# --- Uygulamayı Başlat ---
if __name__ == "__main__":
    if models_ready:
        print("\n🚀 Gradio Blocks arayüzü başlatılıyor...")
        demo.launch() 
    else:
         print("\n❌ Modeller düzgün başlatılamadığı için Gradio arayüzü başlatılamadı.")
         with gr.Blocks(theme=gr.themes.Soft()) as demo_error:
              gr.Markdown("# 🚨 Başlatma Hatası")
              gr.Markdown("Uygulama başlatılırken bir sorun oluştu. Lütfen terminal loglarını kontrol edin.")
              gr.Textbox(f"API Anahtarı Durumu: {'Bulunamadı' if API_KEY_ERROR else 'Bulundu'}", label="API Key", interactive=False)
              gr.Textbox(f"Modeller Hazır mı?: {'Evet' if models_ready else 'Hayır'}", label="Modeller", interactive=False)
         demo_error.launch()
