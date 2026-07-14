import requests
from PIL import Image, ImageDraw, ImageFont

def create_pin_image(product_img_url, hook_text, output_path="final_pin.png"):
    # 1. Download raw product image
    img_data = requests.get(product_img_url).content
    with open("temp.jpg", "wb") as handler:
        handler.write(img_data)
    
    # 2. Open image and resize/crop to Pinterest 2:3 dimensions (1000x1500)
    base_img = Image.open("temp.jpg").convert("RGB")
    base_img = base_img.resize((1000, 1500), Image.Resampling.LANCZOS)
    
    # 3. Initialize drawing overlay
    draw = ImageDraw.Draw(base_img)
    
    # 4. Draw a background text card box (e.g., solid background for text readability)
    # Coordinates: (left, top, right, bottom)
    draw.rectangle([50, 100, 950, 400], fill="#FFFFFF") 
    
    # 5. Add text overlay (Assumes you have a standard .ttf font file in your folder)
    try:
        font = ImageFont.truetype("Arial.ttf", 60)
    except IOError:
        font = ImageFont.load_default()
        
    # Write the text hook inside the white box area
    draw.text((100, 150), hook_text, fill="#111111", font=font)
    
    # 6. Save final production image
    base_img.save(output_path)
    print("Pin graphic generated successfully!")
