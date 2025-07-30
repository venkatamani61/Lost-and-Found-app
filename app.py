from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pytz
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)  # <-- Define app FIRST

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # <-- NOW set config after app is defined

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MongoDB Connection
MONGO_URI = "mongodb+srv://malleshma389:9966890456@cluster0.lihxidx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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
        file = request.files['image']

        # Get current time in IST
        india_tz = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(india_tz).strftime('%Y-%m-%d %H:%M:%S')

        image_path = ''
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        collection.insert_one({
            'name': name,
            'description': description,
            'contact': contact,
            'status': status,
            'submitted_at': timestamp,
            'image_path': image_path
        })

        return redirect(url_for('home'))
    else:
        return render_template('submit.html')

@app.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    collection.delete_one({'_id': ObjectId(item_id)})
    return '', 204  # Success No Content

if __name__ == '__main__':
    app.run(debug=True, port=5003)
