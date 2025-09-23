from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson import ObjectId
import gridfs
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret"
bcrypt = Bcrypt(app)

# MongoDB Atlas
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["Loss"]
fs = gridfs.GridFS(db)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "user_login"

# User class
class User(UserMixin):
    def __init__(self, username, role="user"):
        self.id = username
        self.role = role

@login_manager.user_loader
def load_user(username):
    user = db.users.find_one({"username": username})
    if user:
        return User(username=user["username"], role="user")
    admin = db.admins.find_one({"username": username})
    if admin:
        return User(username=admin["username"], role="admin")
    return None

# -------------------
# Routes for Users
# -------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/lost")
def lost_items():
    return redirect(url_for("items", status="lost"))

@app.route("/found")
def found_items():
    return redirect(url_for("items", status="found"))

@app.route("/items")
def items():
    city = request.args.get("city")
    status = request.args.get("status")
    query = {}
    if city and city != "all":
        query["location"] = city
    if status:
        query["status"] = status

    items = list(db.items.find(query))
    cities = db.items.distinct("location")
    return render_template("items.html", items=items, cities=cities, city=city, status=status)

@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    if current_user.role != "user":
        flash("Only normal users can submit items!", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        contact = request.form['contact']
        status = request.form['status']
        location = request.form['location']
        image_file = request.files['image']

        image_id = fs.put(image_file.read(), filename=image_file.filename)

        db.items.insert_one({
            "name": name,
            "description": description,
            "contact": contact,
            "status": status,
            "location": location,
            "image_id": image_id,
            "submitted_by": current_user.id,
            "submitted_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        flash("Item submitted successfully!", "success")
        return redirect(url_for('home'))

    return render_template("submit.html")

# -------------------
# User Authentication
# -------------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if db.users.find_one({"username": username}):
            flash("User already exists!", "danger")
            return redirect(url_for("register"))
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        db.users.insert_one({"username": username, "password": hashed_pw})
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("user_login"))
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            login_user(User(username=user["username"], role="user"))
            return redirect(url_for("home"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def user_logout():
    logout_user()
    return redirect(url_for("home"))

# -------------------
# Admin Authentication
# -------------------
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = db.admins.find_one({"username": username})
        if admin and bcrypt.check_password_hash(admin["password"], password):
            login_user(User(username=admin["username"], role="admin"))
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Admins only!", "danger")
        return redirect(url_for("home"))
    items = db.items.find()
    admins = db.admins.find()
    return render_template("admin_dashboard.html", items=items, admins=admins)

@app.route("/admin/add", methods=["POST"])
@login_required
def add_admin():
    if current_user.role != "admin":
        flash("Admins only!", "danger")
        return redirect(url_for("home"))
    username = request.form["username"]
    password = request.form["password"]
    if db.admins.find_one({"username": username}):
        flash("Admin exists!", "danger")
    else:
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        db.admins.insert_one({"username": username, "password": hashed_pw})
        flash("Admin created!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_item/<item_id>", methods=["POST"])
@login_required
def admin_delete_item(item_id):
    if current_user.role != "admin":
        flash("Admins only!", "danger")
        return redirect(url_for("home"))
    db.items.delete_one({"_id": ObjectId(item_id)})
    flash("Item deleted!", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))

# -------------------
# Serve Images
# -------------------
from flask import Response
@app.route("/image/<image_id>")
def get_image(image_id):
    try:
        img = fs.get(ObjectId(image_id))
        return Response(img.read(), mimetype="image/jpeg")
    except:
        return "Image Not Found", 404

# -------------------
if __name__ == "__main__":
    if not os.path.exists("static/uploads"):
        os.makedirs("static/uploads")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
