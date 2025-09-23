from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.binary import Binary
from datetime import datetime
import os
import base64

app = Flask(__name__)

# MongoDB Connection
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['Loss']
collection = db['items']

# Base64 filter for templates
@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Lost Items Page
@app.route('/lost')
def lost_items():
    items = list(collection.find({'status': 'Lost'}))
    for item in items:
        item['_id'] = str(item['_id'])
    return render_template('items.html', items=items, status='Lost')

# Found Items Page
@app.route('/found')
def found_items():
    items = list(collection.find({'status': 'Found'}))
    for item in items:
        item['_id'] = str(item['_id'])
    return render_template('items.html', items=items, status='Found')

# Submit Page
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        contact = request.form['contact']
        status = request.form['status']
        submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Handle Image Upload
        image_data = None
        image_filename = ''
        image_file = request.files['image']
        if image_file and image_file.filename != '':
            image_filename = image_file.filename
            image_data = Binary(image_file.read())  # Store image as Binary

        # Insert document into MongoDB
        collection.insert_one({
            'name': name,
            'description': description,
            'contact': contact,
            'status': status,
            'submitted_at': submitted_at,
            'image_filename': image_filename,
            'image_data': image_data
        })

        return redirect(url_for('home'))
    else:
        return render_template('submit.html')

# Delete Item
@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        collection.delete_one({'_id': ObjectId(item_id)})
        return '', 204
    except Exception as e:
        print(f"Error Deleting: {e}")
        return '', 500

if __name__ == '__main__':
    # Get dynamic port for deployment (default to 5000 locally)
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting app on port {port}...")

    # Run Flask app
    app.run(host='0.0.0.0', port=port)
