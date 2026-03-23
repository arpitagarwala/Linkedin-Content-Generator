import google.generativeai as genai

genai.configure(api_key="AIzaSyCQobSJlYC9gO8UhIxgoF3ew7QrWk_Hi8g")
try:
    models = genai.list_models()
    print("Available Models:")
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
