import os
import requests
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# Pull the API key securely from GitHub Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY environment configuration.")

genai.configure(api_key=GEMINI_API_KEY)

def generate_pinterest_hook(product_name, product_desc):
    print(f"🤖 Fetching AI generation for: {product_name}...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Take product: '{product_name}' Description: '{product_desc}'. Write a high-converting Pinterest image overlay hook (max 6 words). Output ONLY the text hook, no punctuation."
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return "Transform Your Strategy Today"

def create_pin_image(product_img_url, hook_text, output_filename):
    print(f"🎨 Canvas compilation for text: {hook_text}")
    try:
        img_data = requests.get(product_img_url, timeout=15).content
        with open("temp.jpg", "wb") as f:
            f.write(img_data)
        
        base_img = Image.open("temp.jpg").convert("RGB")
        base_img = base_img.resize((1000, 1500), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(base_img)
        
        # Draw design backdrop card
        draw.rectangle([50, 100, 950, 400], fill=(255, 255, 255))
        
        # Set standard fallback font mapping
        font = ImageFont.load_default()
        
        # Write text elements
        draw.text((100, 200), hook_text, fill="#111111", font=font)
        
        base_img.save(output_filename)
        print(f"✅ Saved Pin Image asset to repository context: {output_filename}")
        
        if os.path.exists("temp.jpg"):
            os.remove("temp.jpg")
    except Exception as e:
        print(f"❌ Graphics failure: {e}")

if __name__ == "__main__":
    # Your mock product catalog array (or replace with Google Sheets CSV fetch logic)
    CATALOG = [
        {
            "title": "E-Commerce Profit Spreadsheet",
            "desc": "Track your shop analytics on autopilot.",
            "url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1000",
            "out": "output_pin_1.png"
        }
    ]
    
    for item in CATALOG:
        hook = generate_pinterest_hook(item["title"], item["desc"])
        create_pin_image(item["url"], hook, item["out"])
