# 🗺️ Gelişmiş RAG Tabanlı Seyahat Asistanı (Gemini & ChromaDB)

Bu proje, Akbank GenAI Bootcamp'i için geliştirilmiş, coğrafi rota optimizasyonu özelliğine sahip, gelişmiş bir RAG (Retrieval-Augmented Generation) tabanlı seyahat asistanıdır.

## 🚀 Canlı Demo (Hugging Face)

Uygulamanın canlı çalışan versiyonuna aşağıdaki linkten ulaşabilirsiniz:

**[➡️ Buraya Tıklayarak Canlı Demoyu Deneyin](https://huggingface.co/spaces/fatmanurdemir/Chatbot-Travel_Assistant)**

---

## 🖥️ Örnek Kullanım & Product Kılavuzu

Projenin temel özelliklerini ve Uğurcan Bey'in geribildirimi üzerine eklenen rota optimizasyonunu gösteren bazı kullanım örnekleri aşağıdadır.

### 1. Rota Sorgusu ve Coğrafi Optimizasyon

Kullanıcı bir şehir için rota istediğinde, asistan önce LLM (Gemini) kullanarak bir plan oluşturur. Ardından, bu plandaki yerleri `travel_routes.json` dosyasındaki koordinatlara göre **en yakın komşu mantığıyla (coğrafi olarak) yeniden sıralayarak** kullanıcıya optimize edilmiş bir rota sunar.

![Örnek Rota Sorgusu](images/ornek_sorgu.png)
*Görsel 1: Kullanıcının rota sorgusu

