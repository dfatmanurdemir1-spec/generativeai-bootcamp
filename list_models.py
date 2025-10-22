import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("🚨 GOOGLE_API_KEY .env dosyasında bulunamadı!")

# API key ile konfigürasyon
genai.configure(api_key=API_KEY)

# Kullanılabilir modelleri listele
models = genai.list_models()
for m in models:
    print(m)