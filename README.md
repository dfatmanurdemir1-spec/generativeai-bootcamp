# 🗺️ Gelişmiş RAG Tabanlı Seyahat Asistanı (Gemini & ChromaDB)

Bu proje, bir Bilgi Erişim (Retrieval-Augmented Generation - RAG) mimarisinin Python ve Gradio kullanılarak nasıl uygulanabileceğini göstermektedir.

## 🎯 Proje Amacı

Temel amaç, Büyük Dil Modellerinin (LLM) bilgiye dayalı, kontrol edilebilir ve doğrulanabilir yanıtlar üretme yeteneğini sergilemektir. Bu demo, önceden yüklenmiş bir JSON veri seti (`travel_routes.json`) üzerinden çalışmaktadır.

**Öne Çıkan Özellikler:**
1.  **Semantik Arama (RAG):** Kullanıcı sorusunun anlamını vektörlere dönüştürerek en alakalı bilgiyi bulma.
2.  **Dinamik Rota Oluşturma:** LLM'den alınan planları, yerlerin coğrafi koordinatlarına göre en yakın komşu mantığıyla optimize edilmiş sıraya koyma.

## 🛠️ Kurulum ve Çalıştırma Talimatları

Projeyi çalıştırmak için gerekli adımlar aşağıdadır. Bu adımlar, Akbank ekibinin projeyi kolayca ayağa kaldırması için tasarlanmıştır.

### 1. Ön Koşullar
* Python 3.x
* Git (GitHub'a yükleme için gereklidir)

### 2. Ortam Hazırlığı
1.  Proje dosyalarını indirin/klonlayın.
2.  Komut Satırında (Terminal) proje ana dizinine gidin.
3.  Sanal Ortam Oluşturun (Opsiyonel ama önerilir): `python -m venv venv`
4.  Sanal Ortamı Aktif Edin: (Windows'ta: `.\venv\Scripts\activate` / MacOS/Linux'ta: `source venv/bin/activate`)

### 3. Bağımlılıkları Yükleme
Kurulması gereken kütüphaneler `requirements.txt` dosyasında listelenmiştir.
```bash
pip install -r requirements.txt