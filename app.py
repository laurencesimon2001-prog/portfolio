from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import get_connection
import os
from werkzeug.utils import secure_filename
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------
# App Config
# ------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_fallback_key")  # production: set env variable

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ------------------------
# Helpers
# ------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            flash("Please log in first", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

# ------------------------
# Public Routes
# ------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/projects")
def projects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("projects.html", projects=data)

@app.route("/skill")
def skill():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("skill.html", skills=data)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        if not name or not email or not message:
            flash("All fields are required!", "error")
            return redirect(url_for("contact"))

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)",
                (name, email, message)
            )
            conn.commit()
            conn.close()
            flash("Message sent successfully!", "success")
        except Exception as e:
            print(e)
            flash("Database error!", "error")
        return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_connection()
        cursor = conn.cursor() # db.py မှာ DictCursor ပါပြီးသားမို့လို့ ဒီမှာ ဘာမှထည့်စရာမလိုပါ
        cursor.execute("SELECT * FROM admins WHERE username=%s", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin['password'], password):
            session["admin"] = admin['id']
            flash("Login successful", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials", "error")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("admin_login"))

# ------------------------
# Admin Dashboard
# ------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    photos = os.listdir(app.config['UPLOAD_FOLDER']) if os.path.exists(app.config['UPLOAD_FOLDER']) else []
    return render_template("admin_dashboard.html", photos=photos)

# ------------------------
# File Upload
# ------------------------
@app.route("/admin/upload", methods=["GET", "POST"])
@admin_required
def upload_image():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == '':
            flash("No file selected", "error")
            return redirect(request.url)
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in {'png', 'jpg', 'jpeg', 'gif'}:
            flash("Invalid file type", "error")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash("Upload successful", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("upload.html")

@app.route("/admin/delete-photo/<filename>")
@admin_required
def delete_photo(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"Photo {filename} deleted", "success")
    else:
        flash("File not found", "error")
    return redirect(url_for("admin_dashboard"))

# ------------------------
# Messages CRUD
# ------------------------
@app.route("/admin/messages")
@admin_required
def admin_messages():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("admin_messages.html", messages=data)

@app.route("/admin/messages/delete/<int:id>")
@admin_required
def delete_message(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Message deleted", "success")
    return redirect(url_for("admin_messages"))

# ------------------------
# Projects CRUD
# ------------------------
@app.route("/admin/projects")
@admin_required
def admin_projects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("admin_projects.html", projects=data)

@app.route("/admin/projects/add", methods=["GET", "POST"])
@admin_required
def add_project():
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")
        link = request.form.get("link")

        if not title:
            flash("Title is required!", "error")
            return redirect(url_for("add_project"))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (title, description, link) VALUES (%s, %s, %s)",
            (title, desc, link)
        )
        conn.commit()
        conn.close()
        flash("Project added", "success")
        return redirect(url_for("admin_projects"))

    return render_template("admin_add_project.html")

@app.route("/admin/projects/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_project(id):
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")
        link = request.form.get("link")

        cursor.execute(
            "UPDATE projects SET title=%s, description=%s, link=%s WHERE id=%s",
            (title, desc, link, id)
        )
        conn.commit()
        conn.close()
        flash("Project updated", "success")
        return redirect(url_for("admin_projects"))

    cursor.execute("SELECT * FROM projects WHERE id=%s", (id,))
    project = cursor.fetchone()
    conn.close()
    return render_template("admin_edit_project.html", project=project)

@app.route("/admin/projects/delete/<int:id>")
@admin_required
def delete_project(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Project deleted", "success")
    return redirect(url_for("admin_projects"))

# ------------------------
# Skills CRUD
# ------------------------
@app.route("/admin/skill")
@admin_required
def admin_skill():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("admin_skill.html", skills=data)

@app.route("/admin/skill/add", methods=["GET", "POST"])
@admin_required
def add_skill():
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")

        if not title:
            flash("Title is required!", "error")
            return redirect(url_for("add_skill"))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO skills (title, description) VALUES (%s, %s)",
            (title, desc)
        )
        conn.commit()
        conn.close()
        flash("Skill added", "success")
        return redirect(url_for("admin_skill"))

    return render_template("admin_add_skill.html")

@app.route("/admin/skill/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_skill(id):
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")
        cursor.execute(
            "UPDATE skills SET title=%s, description=%s WHERE id=%s",
            (title, desc, id)
        )
        conn.commit()
        conn.close()
        flash("Skill updated", "success")
        return redirect(url_for("admin_skill"))

    cursor.execute("SELECT * FROM skills WHERE id=%s", (id,))
    skill = cursor.fetchone()
    conn.close()
    return render_template("admin_edit_skill.html", skill=skill)

@app.route("/admin/skill/delete/<int:id>")
@admin_required
def delete_skill(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Skill deleted", "success")
    return redirect(url_for("admin_skill"))

# ------------------------
# Run App
# ------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)