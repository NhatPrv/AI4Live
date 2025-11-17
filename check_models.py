import requests
import json

# API key từ gemini_lesson.py
API_KEY = "AIzaSyAwdh4mOMaIx74psQSTD3EHepcc8eFEpwY"

# Lấy danh sách models
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    print("=" * 60)
    print("CÁC MODEL GEMINI KHẢ DỤNG VỚI API KEY NÀY:")
    print("=" * 60)
    
    models = data.get('models', [])
    
    # Lọc các model có thể generateContent
    usable_models = []
    for model in models:
        name = model.get('name', '')
        display_name = model.get('displayName', '')
        methods = model.get('supportedGenerationMethods', [])
        
        if 'generateContent' in methods:
            model_id = name.replace('models/', '')
            usable_models.append((model_id, display_name))
            print(f"✅ {model_id}")
            print(f"   Tên: {display_name}")
            print()
    
    print("=" * 60)
    print(f"Tổng số: {len(usable_models)} model khả dụng")
    print("=" * 60)
    
    # Recommend model
    if usable_models:
        print("\n💡 KHUYẾN NGHỊ:")
        for model_id, display_name in usable_models[:3]:
            if 'flash' in model_id.lower():
                print(f"   - {model_id} (nhanh, tiết kiệm)")
            elif 'pro' in model_id.lower():
                print(f"   - {model_id} (chất lượng cao)")
    
except Exception as e:
    print(f"❌ Lỗi khi gọi API: {e}")
