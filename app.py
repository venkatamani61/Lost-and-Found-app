from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# MongoDB Connection
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['Loss']
collection = db['items']

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/lost')
def lost_items():
    items = list(collection.find({'status': 'Lost'}))
    for item in items:
        item['_id'] = str(item['_id'])
    return render_template('items.html', items=items, status='Lost')

@app.route('/found')
def found_items():
    items = list(collection.find({'status': 'Found'}))
    for item in items:
        item['_id'] = str(item['_id'])
    return render_template('items.html', items=items, status='Found')

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        contact = request.form['contact']
        status = request.form['status']
        submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Handle Image Upload
        image_file = request.files['image']
        image_filename = ''
        if image_file and image_file.filename != '':
            image_filename = datetime.now().strftime('%Y%m%d%H%M%S_') + image_file.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        collection.insert_one({
            'name': name,
            'description': description,
            'contact': contact,
            'status': status,
            'submitted_at': submitted_at,
            'image': image_filename
        })

        return redirect(url_for('home'))
    else:
        return render_template('submit.html')

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        collection.delete_one({'_id': ObjectId(item_id)})
        return '', 204
    except Exception as e:
        print(f"Error Deleting: {e}")
        return '', 500

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')

    # Get dynamic port for Render (default to 5000 locally)
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting app on port {port}...")

    # Run Flask app
    app.run(host='0.0.0.0', port=port)

