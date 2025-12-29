import os
import base64
from io import BytesIO
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw
from supabase import create_client
from dotenv import load_dotenv
import requests


# Load .env
load_dotenv()

app = Flask(__name__)

# Supabase client
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

LETTERS = "abcdefghijklmnopqrstuvwxyz"

@app.route("/")
def index():
    return render_template("alphabet.html", letters=LETTERS)

@app.route("/save_letter", methods=["POST"])
def save_letter():
    import base64

    # --- Parse JSON ---
    try:
        data = request.get_json(force=True)
        if not data or "letter" not in data or "image" not in data:
            return {"status": "error", "message": "Missing letter or image"}
        letter = data["letter"].lower()
        image_data = data["image"].split(",")[1]
        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        print("JSON parse error:", e)
        return {"status": "error", "message": str(e)}

    # --- Upload to storage ---
    path = f"{letter}.png"
    try:
        try:
            supabase.storage.from_("handwriting").remove([path])
        except Exception:
            pass  # ignore if file not exists
        supabase.storage.from_("handwriting").upload(
            path,
            image_bytes,
            {"content-type": "image/png"}
        )
    except Exception as e:
        print("Storage upload error:", e)
        return {"status": "error", "message": str(e)}

    # --- Get public URL (string) ---
    try:
        image_url = supabase.storage.from_("handwriting").get_public_url(path)
        # image_url is already a string in your library version
    except Exception as e:
        print("Error getting public URL:", e)
        return {"status": "error", "message": str(e)}

    # --- Upsert table ---
    try:
        supabase.table("handwriting_letters").upsert({
            "letter": letter,
            "image_url": image_url
        }).execute()
    except Exception as e:
        print("Table insert error:", e)
        return {"status": "error", "message": str(e)}

    print(f"Saved letter '{letter}' to Supabase: {image_url}")
    return {"status": "saved"}


# Generate card from all letters
@app.route("/generate_card")
def generate_card():
    rows = supabase.table("handwriting_letters").select("*").order("letter").execute().data

    if not rows:
        return "No letters found."

    canvas = Image.new("RGB", (1200, 600), "white")
    x, y = 50, 200

    for row in rows:
        img = Image.open(BytesIO(requests.get(row["image_url"]).content))
        img = img.resize((40, 80))
        canvas.paste(img, (x, y))
        x += 45

    output = "thank_you_card.png"
    canvas.save(output)

    return send_file(output, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
