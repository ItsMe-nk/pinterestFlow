import os
import json
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from google import genai # NEW SDK IMPORT

# ==========================================
# 1. API KEY REGISTRATION & CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
PINTEREST_TOKEN = os.getenv("PINTEREST_TOKEN")

# 👉 Ensure your numerical Board ID is pasted here:
PINTEREST_BOARD_ID = "1030902239643629536" 
TARGET_NICHE = "Beauty Templates"

if not all([GEMINI_API_KEY, IMGBB_API_KEY, PINTEREST_TOKEN]):
    raise ValueError("Missing required GitHub environment secrets. Check your main.yml env mapping.")

# Initialize the new Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. STEP A: AUTONOMOUS 10-PRODUCT BRAINSTORM
# ==========================================
def brainstorm_daily_catalog():
    print(f"🧠 Brainstorming 10 trending viral product concepts for: {TARGET_NICHE}...")
    
    prompt = f"""
    You are an expert digital product creator. Brainstorm exactly 10 distinct, trending digital products or templates tailored to the niche: '{TARGET_NICHE}'.
    
    For each product, generate:
    1. A short clean Title.
    2. A keyword-rich Pinterest Pin Description (under 400 characters).
    3. A highly clickable text overlay hook for the image canvas (max 5 words, no punctuation).
    4. A high-quality keyword to pull a relevant background image from Unsplash (e.g., 'workspace', 'calculator', 'notebook').
    5. A mock target landing page checkout link (e.g., '[https://yourstore.gumroad.com/l/budget](https://yourstore.gumroad.com/l/budget)').
    
    Output the final result strictly as a raw JSON array matching this format structure exactly:
    [
      {{"title": "Product Title", "desc": "Pin description", "hook": "Image Hook Text", "keyword": "unsplash_keyword", "link": "checkout_url"}}
    ]
    Do not wrap the response in markdown code blocks like ```json. Output raw text only.
    """
    
    # 💡 The Waterfall List: The script will try these in order from top to bottom
    models_to_try = [
        'gemini-3.5-flash',  # Primary choice
        'gemini-2.5-flash',  # First backup (highly reliable)
        'gemini-2.5-pro'     # Final backup
    ]
    
    for model_name in models_to_try:
        try:
            print(f"🔄 Attempting generation with {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            
            catalog = json.loads(response.text.strip())
            print(f"✅ Brainstorm complete using {model_name}! Generated {len(catalog)} blueprints.")
            return catalog
            
        except Exception as e:
            # Catch the 503 (or any other error) and prepare to try the next model
            error_msg = str(e)
            print(f"⚠️ Warning: {model_name} failed. Moving to backup... (Error: {error_msg[:80]}...)")
            
            if model_name == models_to_try[-1]:
                # If we just failed on the very last backup model, log a critical failure
                print("❌ CRITICAL: All backup models are currently unavailable. Exiting run.")
                return []
            
            # Wait 3 seconds before hitting the next model to avoid spamming the API
            time.sleep(3)
            
    return []

# ==========================================
# 3. STEP B: IMAGE DESIGN CANVAS (PILLOW)
# ==========================================
def draw_pin_canvas(keyword, hook_text):
    output_filename = "temp_render.png"
    try:
        img_url = f"[https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1000](https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1000)" 
        if keyword:
            img_url = f"[https://source.unsplash.com/featured/1000x1500/](https://source.unsplash.com/featured/1000x1500/)?{keyword}"
            
        img_data = requests.get(img_url, timeout=15).content
        with open("raw.jpg", "wb") as f:
            f.write(img_data)
            
        base_img = Image.open("raw.jpg").convert("RGB").resize((1000, 1500), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(base_img)
        
        draw.rectangle([60, 120, 940, 450], fill=(255, 255, 255))
        font = ImageFont.load_default()
        
        draw.text((120, 220), hook_text.upper(), fill="#111111", font=font)
        
        draw.rectangle([0, 1420, 1000, 1500], fill="#E60023")
        draw.text((420, 1445), "CLICK TO DOWNLOAD", fill="#FFFFFF", font=font)
        
        base_img.save(output_filename)
        if os.path.exists("raw.jpg"): os.remove("raw.jpg")
        return output_filename
    except Exception as e:
        print(f"❌ Design generation error: {e}")
        return None

# ==========================================
# 4. STEP C: TEMPORARY WEB HOSTING (IMGBB)
# ==========================================
def upload_to_web_host(local_file_path):
    url = "[https://api.imgbb.com/1/upload](https://api.imgbb.com/1/upload)"
    payload = {
        "key": IMGBB_API_KEY,
        "expiration": 600
    }
    try:
        with open(local_file_path, "rb") as file:
            files = {"image": file}
            response = requests.post(url, data=payload, files=files)
            data = response.json()
            return data["data"]["url"]
    except Exception as e:
        print(f"❌ Hosting upload failed: {e}")
        return None

# ==========================================
# 5. STEP D: PINTEREST PUBLISHER ENGINE
# ==========================================
def publish_to_pinterest(image_public_url, target_url, title, description):
    endpoint = "[https://api.pinterest.com/v5/pins](https://api.pinterest.com/v5/pins)"
    headers = {
        "Authorization": f"Bearer {PINTEREST_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "board_id": PINTEREST_BOARD_ID,
        "title": title[:99],
        "description": description[:499],
        "media_source": {
            "source_type": "image_url",
            "url": image_public_url
        },
        "link": target_url
    }
    try:
        res = requests.post(endpoint, json=payload, headers=headers)
        if res.status_code in [200, 201]:
            print(f"🎉 SUCCESS: Pin successfully published to live board!")
        else:
            print(f"❌ Pinterest API rejection status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"❌ Failed to reach Pinterest servers: {e}")

# ==========================================
# 6. MASTER EXECUTION WORKFLOW LOOP
# ==========================================
if __name__ == "__main__":
    print("=== INITIALIZING FULLY AUTONOMOUS PINTEREST MARKETING ENGINE ===")
    
    daily_catalog = brainstorm_daily_catalog()
    
    for idx, item in enumerate(daily_catalog):
        print(f"\n🚀 Processing Campaign Build ({idx + 1}/{len(daily_catalog)}): {item['title']}")
        
        rendered_file = draw_pin_canvas(item['keyword'], item['hook'])
        
        if rendered_file and os.path.exists(rendered_file):
            public_img_url = upload_to_web_host(rendered_file)
            
            if public_img_url:
                publish_to_pinterest(
                    image_public_url=public_img_url,
                    target_url=item['link'],
                    title=item['title'],
                    description=item['desc']
                )
            os.remove(rendered_file)
            
        if idx < len(daily_catalog) - 1:
            print("⏳ Cool-down pause initiated to honor API rate limits...")
            time.sleep(15)

    print("\n================================================================")
    print("🎉 Daily Pipeline complete!")
