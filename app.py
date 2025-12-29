from supabase import create_client, Client
import base64

url = "https://yuywshrmnvemvgsxevow.supabase.co"
key = "sb_publishable_echas_lmMXFYh0WBZJpliQ_y2O-5ksj"
supabase: Client = create_client(url, key)

@app.route('/save_letter', methods=['POST'])
def save_letter():
    data = request.get_json()
    letter = data['letter']
    child_id = data.get('child_id', 'test_child')
    img_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(img_data)

    # Upload to Supabase Storage
    file_path = f"{child_id}/{letter}.png"
    supabase.storage.from_('handwriting_letters').upload(file_path, img_bytes)

    # Get public URL
    image_url = supabase.storage.from_('handwriting_letters').get_public_url(file_path)['publicUrl']

    # Insert metadata into table
    supabase.table('child_handwriting').insert({
        'child_name': child_id,
        'letter': letter,
        'image_url': image_url
    }).execute()

    return f"Saved {letter} for {child_id}!"
