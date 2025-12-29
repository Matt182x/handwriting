import base64
from flask import Flask, render_template, request
import os

app = Flask(__name__)
os.makedirs('letter_samples', exist_ok=True)

@app.route('/')
def home():
    return render_template('alphabet.html')

@app.route('/save_letter', methods=['POST'])
def save_letter():
    data = request.get_json()
    letter = data['letter']
    img_data = data['image'].split(',')[1]  # remove header
    img_bytes = base64.b64decode(img_data)
    filename = os.path.join('letter_samples', f'{letter}.png')
    with open(filename, 'wb') as f:
        f.write(img_bytes)
    return f"Saved {letter}!"

if __name__ == "__main__":
    app.run(debug=True)
