# 🗺️ Gelişmiş RAG Tabanlı Seyahat Asistanı (Gemini & ChromaDB)

Bu proje, bir Bilgi Erişim (Retrieval-Augmented Generation - RAG) mimarisinin Python ve Gradio kullanılarak nasıl uygulanabileceğini göstermektedir.

## 🎯 Proje Amacı

Bu projenin temel amacı, Büyük Dil Modellerinin (LLM) bilgiye dayalı, **kontrollü ve doğrulanabilir** yanıtlar üretme yeteneğini sergilemektir.

**Neden Seyahat Asistanı?**

Seyahat etmek benim için büyük bir tutku. Ancak yurt dışına çıktığımda, **etkili ve zaman/maliyet açısından optimize edilmiş seyahat rotaları** oluşturmanın ne kadar zor olduğunu bizzat deneyimledim. Farklı yerleri tek tek araştırmak, en yakın komşuluk mantığıyla sıralamak ve tüm bu bilgiyi tek bir akıcı planda birleştirmek **büyük bir zaman ve çaba gerektiriyor.**

Bu chatbot, tam da bu zorluğu aşmak için tasarlandı:

1.  **Semantik Arama (RAG):** Kullanıcı sorusunun anlamını vektörlere dönüştürerek, önceden yüklenmiş kapsamlı veri setimizden (`travel_routes.json`) en alakalı bilgiyi anında bulma.
2.  **Dinamik ve Optimize Rota Oluşturma:** LLM'den alınan planları, yerlerin coğrafi koordinatlarına göre **en yakın komşu mantığıyla optimize edilmiş sıraya** koyarak, kullanıcıya pratik ve zahmetsiz bir rota sunma.

Bu sayede, karmaşık araştırma süreçlerini otomatize ederek seyahatlerin keyfini çıkarmaya daha fazla odaklanmanızı sağlıyoruz.

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