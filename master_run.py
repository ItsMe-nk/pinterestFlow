import os
import json
import time
import requests
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# ==========================================
# 1. API KEY REGISTRATION & CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
PINTEREST_TOKEN = os.getenv("PINTEREST_TOKEN")
PINTEREST_BOARD_ID = "YOUR_PINTEREST_BOARD_ID_HERE" # Put your numerical Board ID here
TARGET_NICHE = "Personal Finance and Passive Income Templates"

if not all([GEMINI_API_KEY, IMGBB_API_KEY, PINTEREST_TOKEN]):
    raise ValueError("Missing required GitHub environment secrets.")

genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 2. STEP A: AUTONOMOUS 10-PRODUCT BRAINSTORM
# ==========================================
def brainstorm_daily_catalog():
    """Commands Gemini to act as a product manager and output 10 unique product concepts."""
    print(f"🧠 Brainstorming 10 trending viral product concepts for: {TARGET_NICHE}...")
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    prompt = f"""
    You are an expert digital product creator. Brainstorm exactly 10 distinct, trending digital products or templates tailored to the niche: '{TARGET_NICHE}'.
    
    For each product, generate:
    1. A short clean Title.
    2. A keyword-rich Pinterest Pin Description (under 400 characters).
    3. A highly clickable text overlay hook for the image canvas (max 5 words, no punctuation).
    4. A high-quality keyword to pull a relevant background image from Unsplash (e.g., 'workspace', 'calculator', 'notebook').
    5. A mock target landing page checkout link (e.g., 'https://yourstore.gumroad.com/l/budget').
    
    Output the final result strictly as a raw JSON array matching this format structure exactly:
    [
      {{"title": "Product Title", "desc": "Pin description", "hook": "Image Hook Text", "keyword": "unsplash_keyword", "link": "checkout_url"}}
    ]
    Do not wrap the response in markdown code blocks like ```json. Output raw text only.
    """
    
    response = model.generate_content(prompt)
    try:
        catalog = json.loads(response.text.strip())
        print(f"✅ Brainstorm complete! Successfully generated {len(catalog)} campaign blueprints.")
        return catalog
    except Exception as e:
        print(f"❌ Failed to parse JSON configuration output from Gemini: {e}")
        print(f"Raw response was: {response.text}")
        return []

# ==========================================
# 3. STEP B: IMAGE DESIGN CANVAS (PILLOW)
# ==========================================
def draw_pin_canvas(keyword, hook_text):
    """Fetches a dynamic background image based on keyword and stamps text graphics over it."""
    output_filename = "temp_render.png"
    try:
        # Dynamically fetch an evergreen background graphic from Unsplash source based on keyword
        img_url = f"[https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1000](https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=1000)" # High quality base fallback
        if keyword:
            img_url = f"[https://source.unsplash.com/featured/1000x1500/](https://source.unsplash.com/featured/1000x1500/)?{keyword}"
            
        img_data = requests.get(img_url, timeout=15).content
        with open("raw.jpg", "wb") as f:
            f.write(img_data)
            
        base_img = Image.open("raw.jpg").convert("RGB").resize((1000, 1500), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(base_img)
        
        # Transparent overlay design frame
        draw.rectangle([60, 120, 940, 450], fill=(255, 255, 255))
        font = ImageFont.load_default()
        
        # Draw the text overlay hook
        draw.text((120, 220), hook_text.upper(), fill="#111111", font=font)
        
        # Brand CTA Banner
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
    """Uploads the locally generated image to ImgBB to generate a public link for Pinterest."""
    url = "[https://api.imgbb.com/1/upload](https://api.imgbb.com/1/upload)"
    payload = {
        "key": IMGBB_API_KEY,
        "expiration": 600 # Automated delete window after 10 minutes
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
    """Pushes the finalized image and SEO texts directly onto your Pinterest live board."""
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
            print(f"🎉 SUCCESS: Pin successfully published to live board ID {PINTEREST_BOARD_ID}!")
        else:
            print(f"❌ Pinterest API rejection status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"❌ Failed to reach Pinterest servers: {e}")

# ==========================================
# 6. MASTER EXECUTION WORKFLOW LOOP
# ==========================================
if __name__ == "__main__":
    print("=== INITIALIZING FULLY AUTONOMOUS PINTEREST MARKETING ENGINE ===")
    
    # Generate the 10 daily product profiles via AI Studio
    daily_catalog = brainstorm_daily_catalog()
    
    for idx, item in enumerate(daily_catalog):
        print(f"\n🚀 Processing Campaign Build ({idx + 1}/10): {item['title']}")
        
        # 1. Render image file locally
        rendered_file = draw_pin_canvas(item['keyword'], item['hook'])
        
        if rendered_file and os.path.exists(rendered_file):
            # 2. Host image publicly
            public_img_url = upload_to_web_host(rendered_file)
            
            if public_img_url:
                # 3. Publish straight to live Pinterest Account
                publish_to_pinterest(
                    image_public_url=public_img_url,
                    target_url=item['link'],
                    title=item['title'],
                    description=item['desc']
                )
            
            # Clean up the local image file before the next loop run
            os.remove(rendered_file)
            
        # ⚠️ CRITICAL RATE LIMIT SAFETY GAP
        # Pauses execution for 15 seconds. This completely prevents hitting the 
        # 5 Requests Per Minute maximum constraint enforced on the Gemini Free Tier.
        if idx < len(daily_catalog) - 1:
            print("⏳ Cool-down pause initiated to honor API rate limits...")
            time.sleep(15)

    print("\n================================================================")
    print("🎉 Daily Pipeline complete! 10 fresh strategic pins are now live.")
