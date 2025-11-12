import google.generativeai as genai

genai.configure(api_key="AIzaSyCrCLsotI6rKauU08ZHi7o9nIXJdtRkGgQ")

print("📋 Danh sách models khả dụng:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"  ✓ {m.name}")