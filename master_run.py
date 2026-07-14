import os
import json
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from google import genai

# ==========================================
# 1. API KEY REGISTRATION & CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
PINTEREST_TOKEN = os.getenv("PINTEREST_TOKEN")

# 👉 Ensure your numerical Board ID is pasted here:
PINTEREST_BOARD_ID = "1030902239643629536" 
TARGET_NICHE = "Beauty Templates and Salon Business Forms"

# 💰 YOUR AFFILIATE LINK BANK
# We are keeping just 1 link for testing. Add more here later!
AFFILIATE_LINKS = [
    "https://clickbank.net/your-test-link"
]

if not all([GEMINI_API_KEY, IMGBB_API_KEY, PINTEREST_TOKEN]):
    raise ValueError("Missing required GitHub environment secrets. Check your main.yml env mapping.")

if not AFFILIATE_LINKS:
    raise ValueError("You must add at least one affiliate link to the bank.")

# Initialize the new Google GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. STEP A: AUTONOMOUS BRAINSTORMING
# ==========================================
def brainstorm_daily_catalog():
    print(f"🧠 Brainstorming 1 trending viral product concept for: {TARGET_NICHE}...")
    
    prompt = f"""
    You are an expert digital product creator. Brainstorm exactly 1 distinct, trending digital product or template tailored to the niche: '{TARGET_NICHE}'.
    
    For each product, generate:
    1. A short clean Title.
    2. A keyword-rich Pinterest Pin Description (under 400 characters).
    3. A highly clickable text overlay hook for the image canvas (max 5 words, no punctuation).
    4. A high-quality keyword to pull a relevant background image (e.g., 'skincare', 'makeup brushes', 'salon').
    
    Output the final result strictly as a raw JSON array matching this format structure exactly:
    [
      {{"title": "Product Title", "desc": "Pin description", "hook": "Image Hook Text", "keyword": "image_keyword"}}
    ]
    Do not wrap the response in markdown code blocks. Output raw text only.
    """
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempting generation with gemini-3.5-flash (Attempt {attempt + 1}/{max_retries})...")
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt,
            )
            catalog = json.loads(response.text.strip())
            print(f"✅ Brainstorm complete! Generated {len(catalog)} blueprint(s).")
            return catalog
            
        except Exception as e:
            error_msg = str(e)
            
            # If we hit a rate limit (429) or server overload (503), wait and retry
            if "429" in error_msg or "503" in error_msg:
                wait_time = 15 * (attempt + 1) # Waits 15s, then 30s, then 45s
                print(f"⚠️ Server busy or rate limited. Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                continue 
                
            # If it's a completely different error, stop immediately
            print(f"❌ Fatal Error: {error_msg[:100]}...")
            return []
            
    print("❌ CRITICAL: Failed to generate after maximum retries.")
    return []

# ==========================================
# 3. STEP B: IMAGE DESIGN CANVAS (PILLOW)
# ==========================================
def draw_pin_canvas(keyword, hook_text):
    output_filename = "temp_render.png"
    try:
        # Clean keyword and use Pollinations AI with a 60-second timeout
        safe_keyword = keyword.replace(" ", "%20")
        img_url = f"https://image.pollinations.ai/prompt/aesthetic%20{safe_keyword}%20background?width=1000&height=1500&nologo=true"
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        img_data = requests.get(img_url, headers=headers, timeout=60).content
        
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
        if os.path.exists("raw.jpg"): 
            os.remove("raw.jpg")
            
        return output_filename
    except Exception as e:
        print(f"❌ Design generation error: {e}")
        return None

# ==========================================
# 4. STEP C: TEMPORARY WEB HOSTING (IMGBB)
# ==========================================
def upload_to_web_host(local_file_path):
    url = "https://api.imgbb.com/1/upload" # Clean URL without markdown brackets!
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
    endpoint = "https://api.pinterest.com/v5/pins"
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
    print("=== INITIALIZING AFFILIATE MARKETING ENGINE ===")
    
    daily_catalog = brainstorm_daily_catalog()
    
    for idx, item in enumerate(daily_catalog):
        print(f"\n🚀 Processing Campaign Build ({idx + 1}/{len(daily_catalog)}): {item['title']}")
        
        target_affiliate_link = AFFILIATE_LINKS[idx % len(AFFILIATE_LINKS)]
        print(f"🔗 Routing traffic to: {target_affiliate_link}")
        
        rendered_file = draw_pin_canvas(item['keyword'], item['hook'])
        
        if rendered_file and os.path.exists(rendered_file):
            public_img_url = upload_to_web_host(rendered_file)
            
            if public_img_url:
                publish_to_pinterest(
                    image_public_url=public_img_url,
                    target_url=target_affiliate_link,
                    title=item['title'],
                    description=item['desc']
                )
            os.remove(rendered_file)
            
        if idx < len(daily_catalog) - 1:
            print("⏳ Cool-down pause initiated to honor API rate limits...")
            time.sleep(15)

    print("\n================================================================")
    print("🎉 Pipeline complete! Check your Pinterest board.")
