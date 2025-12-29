
import os
import base64
import requests
from io import BytesIO
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
from supabase import create_client

# Flask setup
app = Flask(__name__)

# Supabase credentials from environment variables
SUPABASE_URL =  "https://yuywshrmnvemvgsxevow.supabase.co"
SUPABASE_KEY = "sb_publishable_echas_lmMXFYh0WBZJpliQ_y2O-5ksj"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ensure temporary folder
os.makedirs("fonts_temp", exist_ok=True)

# Routes
@app.route('/')
def home():
    return render_template('alphabet.html')

@app.route('/save_letter', methods=['POST'])
def save_letter():
    data = request.get_json()
    letter = data['letter']
    child_id = data.get('child_id', 'child_001')
    img_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(img_data)

    # Upload letter PNG to Supabase Storage
    file_path = f"{child_id}/{letter}.png"
    supabase.storage.from_('letters').upload(file_path, img_bytes, {"content-type": "image/png"}, upsert=True)
    image_url = supabase.storage.from_('letters').get_public_url(file_path)['publicUrl']

    # Insert metadata into letters table
    supabase.table('letters').insert({
        'child_id': child_id,
        'letter': letter,
        'image_url': image_url
    }).execute()

    return f"Saved {letter} for {child_id}!"

@app.route('/generate_font/<child_id>')
def generate_font(child_id):
    import fontforge
    letters = "abcdefghijklmnopqrstuvwxyz"
    letters_folder = f"fonts_temp/{child_id}"
    os.makedirs(letters_folder, exist_ok=True)

    # Download letter PNGs from Supabase
    for letter in letters:
        file_path = f"{child_id}/{letter}.png"
        url = supabase.storage.from_('letters').get_public_url(file_path)['publicUrl']
        response = requests.get(url)
        with open(os.path.join(letters_folder, f"{letter}.png"), 'wb') as f:
            f.write(response.content)

    # Generate TTF
    font = fontforge.font()
    font.fontname = f"{child_id}_handwriting"
    font.fullname = f"{child_id} Handwriting"
    font.familyname = f"{child_id} Handwriting"

    for letter in letters:
        glyph = font.createChar(ord(letter))
        png_path = os.path.join(letters_folder, f"{letter}.png")
        glyph.importOutlines(png_path)
        glyph.autoHint()

    ttf_path = f"{child_id}_handwriting.ttf"
    font.generate(ttf_path)

    # Upload TTF to Supabase Storage
    with open(ttf_path, "rb") as f:
        supabase.storage.from_('letters').upload(f"{child_id}/child_handwriting.ttf", f.read(), {"content-type": "font/ttf"}, upsert=True)
    ttf_url = supabase.storage.from_('letters').get_public_url(f"{child_id}/child_handwriting.ttf")['publicUrl']

    # Insert into fonts table
    supabase.table('fonts').insert({
        'child_id': child_id,
        'font_url': ttf_url
    }).execute()

    return f"Font generated and uploaded: {ttf_url}"

@app.route('/generate_card/<child_id>')
def generate_card(child_id):
    # Get font URL from fonts table
    font_data = supabase.table('fonts').select('font_url').eq('child_id', child_id).execute()
    if len(font_data.data) == 0:
        return "No font found for this child."

    font_url = font_data.data[-1]['font_url']  # latest font
    response = requests.get(font_url)
    font_file = BytesIO(response.content)

    # Generate card
    font = ImageFont.truetype(font_file, 48)
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((50, 150), "Thank you for the gift!", font=font, fill='black')
    output_path = f"{child_id}_card.png"
    img.save(output_path)

    return send_file(output_path, mimetype='image/png')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
