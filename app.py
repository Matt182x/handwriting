from flask import Flask, render_template, request, send_file
from replit import db
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

app = Flask(__name__)

# Capture letter
@app.route('/')
def home():
    return render_template('alphabet.html')

@app.route('/save_letter', methods=['POST'])
def save_letter():
    data = request.get_json()
    letter = data['letter']
    child_id = data.get('child_id', 'child_001')
    img_data = data['image'].split(',')[1]
    
    # Store base64 string in Replit DB
    db[f"{child_id}_{letter}"] = img_data
    return f"Saved {letter} for {child_id}!"

# Generate simple card
@app.route('/generate_card/<child_id>')
def generate_card(child_id):
    letters = "abcdefghijklmnopqrstuvwxyz"
    
    # Create blank card
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    y = 50
    for letter in letters:
        key = f"{child_id}_{letter}"
        if key in db:
            img_bytes = base64.b64decode(db[key])
            letter_img = Image.open(BytesIO(img_bytes)).resize((50, 50))
            img.paste(letter_img, (50 + 60*letters.index(letter), y))

    draw.text((50, 300), "Thank you for the gift!", font=font, fill="black")
    output = BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return send_file(output, mimetype='image/png', download_name=f"{child_id}_card.png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
