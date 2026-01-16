from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import get_connection 
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            sql = "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, email, message))
            conn.commit()
            conn.close()
            flash("Message sent successfully!", "success")
            return redirect(url_for("contact"))
        except Exception as e:
            print(f"Database Error: {e}")
            flash("Error saving message!", "error")
            return redirect(url_for("contact"))
    return render_template("contact.html")

# Admin Auth Routes 
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s",
                       (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            session["admin"] = True
            flash("Login successful.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password!", "error")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out successfully", "success")
    return redirect("/admin/login")

@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect("/admin/login")
    
    # Uploads folder
    photos = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        photos = os.listdir(app.config['UPLOAD_FOLDER'])
        
    return render_template("admin_dashboard.html", photos=photos)

# Admin Upload Photo Route
@app.route("/admin/upload", methods=["GET", "POST"])
def upload_image():
    if "admin" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        file = request.files.get('file')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            flash("Photo upload success!", "success")
            return redirect(url_for("admin_dashboard"))
            
    return render_template("upload.html") 

# Admin Messages Management 
@app.route("/admin/messages")
def admin_messages():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("admin_messages.html", messages=data)

@app.route("/admin/messages/delete/<int:id>")
def delete_message(id):
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Message deleted!", "error")
    return redirect("/admin/messages")

# --- Admin Projects Management ---
@app.route("/admin/projects")
def admin_projects():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template("admin_projects.html", projects=data)

@app.route("/admin/projects/add", methods=["GET", "POST"])
def add_project():
    if "admin" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]
        link = request.form["link"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (title, description, link) VALUES (%s, %s, %s)",
                       (title, desc, link))
        conn.commit()
        conn.close()
        flash("Project added!", "success")
        return redirect("/admin/projects")
    return render_template("admin_add_project.html")

@app.route("/admin/projects/edit/<int:id>", methods=["GET", "POST"])
def edit_project(id):
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id=%s", (id,))
    project = cursor.fetchone()

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]
        link = request.form["link"]
        cursor.execute("UPDATE projects SET title=%s, description=%s, link=%s WHERE id=%s", 
                       (title, desc, link, id))
        conn.commit()
        conn.close()
        flash("Project updated!", "success")
        return redirect("/admin/projects")
    conn.close()
    return render_template("admin_edit_project.html", project=project)

@app.route("/admin/projects/delete/<int:id>")
def delete_project(id):
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    flash("Project deleted!", "error")
    return redirect("/admin/projects")

# --- Admin Skills Management ---
@app.route("/admin/skill")
def admin_skill():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills ORDER BY id DESC") 
    data = cursor.fetchall()
    conn.close()
    return render_template("admin_skill.html", skills=data)

@app.route("/admin/skill/add", methods=["GET", "POST"])
def add_skill():
    if "admin" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO skills (title, description) VALUES (%s, %s)",
                       (title, description))
        conn.commit()
        conn.close()
        flash("Skill added!", "success")
        return redirect("/admin/skill")
    return render_template("admin_add_skill.html")

@app.route("/admin/skill/edit/<int:id>", methods=["GET", "POST"])
def edit_skill(id):
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        cursor.execute("UPDATE skills SET title=%s, description=%s WHERE id=%s", 
                       (title, description, id))
        conn.commit()
        conn.close()
        flash("Skill updated!", "success")
        return redirect("/admin/skill")

    cursor.execute("SELECT * FROM skills WHERE id=%s", (id,)) 
    skill = cursor.fetchone()
    conn.close()
    if skill is None:
        flash("Skill not found.", "error")
        return redirect("/admin/skill")
    return render_template("admin_edit_skill.html", skill=skill)

@app.route("/admin/skill/delete/<int:id>")
def delete_skill(id):
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills WHERE id=%s", (id,)) 
    conn.commit()
    conn.close()
    flash("Skill deleted!", "error")
    return redirect("/admin/skill")
# photo delete 
@app.route("/admin/delete-photo/<filename>")
def delete_photo(filename):
    if "admin" not in session:
        return redirect("/admin/login")

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f"Photo {filename} deleted successfully!", "error") 
        else:
            flash("File not found!", "error")
            
    except Exception as e:
        flash(f"Error: {str(e)}", "error")

    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)