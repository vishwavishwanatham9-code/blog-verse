from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import os
import re

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================

app.secret_key = "your_secret_key"

# =========================
# DATABASE
# =========================

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogverse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# CLOUDINARY CONFIG
# =========================

cloudinary.config(
    cloud_name="YOUR_CLOUD_NAME",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET"
)

# =========================
# ADMIN SETTINGS
# =========================

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_DELETE_PASSWORD = "admin123"

# =========================
# DATABASE MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    image = db.Column(db.String(500))
    author = db.Column(db.String(100))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    username = db.Column(db.String(100))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

# =========================
# CREATE DATABASE
# =========================

with app.app_context():
    db.create_all()

# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('home.html', posts=posts)

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Username already exists"

        new_user = User(
            username=username,
            password=password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            session['username'] = username
            return redirect('/')

        return "Invalid username or password"

    return render_template('login.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# =========================
# CREATE POST
# =========================

@app.route('/create', methods=['GET', 'POST'])
def create():

    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']
        content = request.form['content']

        image_file = request.files['image']

        image_url = ""

        if image_file and image_file.filename != "":

            filename = secure_filename(image_file.filename)

            upload_result = cloudinary.uploader.upload(image_file)

            image_url = upload_result['secure_url']

        new_post = Post(
            title=title,
            content=content,
            image=image_url,
            author=session['username']
        )

        db.session.add(new_post)
        db.session.commit()

        return redirect('/')

    return render_template('create.html')

# =========================
# VIEW POST
# =========================

@app.route('/post/<int:post_id>')
def post(post_id):

    single_post = Post.query.get_or_404(post_id)

    comments = Comment.query.filter_by(post_id=post_id).all()

    return render_template(
        'post.html',
        post=single_post,
        comments=comments
    )

# =========================
# ADD COMMENT
# =========================

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):

    if 'username' not in session:
        return redirect('/login')

    content = request.form['content']

    new_comment = Comment(
        content=content,
        username=session['username'],
        post_id=post_id
    )

    db.session.add(new_comment)
    db.session.commit()

    return redirect(f'/post/{post_id}')

# =========================
# DELETE POST
# =========================

@app.route('/delete/<int:post_id>', methods=['GET', 'POST'])
def delete(post_id):

    if 'username' not in session:
        return redirect('/login')

    username = session['username']

    if username != ADMIN_EMAIL:
        return "Only Admin Can Delete Posts"

    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':

        password = request.form['password']

        if password == ADMIN_DELETE_PASSWORD:

            comments = Comment.query.filter_by(post_id=post_id).all()

            for comment in comments:
                db.session.delete(comment)

            db.session.delete(post)
            db.session.commit()

            return redirect('/')

        else:
            return "Wrong Admin Password"

    return render_template(
        'delete_post.html',
        post=post
    )

# =========================
# DELETE COMMENT
# =========================

@app.route('/delete_comment/<int:post_id>/<int:comment_id>', methods=['GET', 'POST'])
def delete_comment(post_id, comment_id):

    if 'username' not in session:
        return redirect('/login')

    username = session['username']

    if username != ADMIN_EMAIL:
        return "Only Admin Can Delete Comments"

    comment = Comment.query.get_or_404(comment_id)

    if request.method == 'POST':

        password = request.form['password']

        if password == ADMIN_DELETE_PASSWORD:

            db.session.delete(comment)
            db.session.commit()

            return redirect(f'/post/{post_id}')

        else:
            return "Wrong Admin Password"

    return render_template(
        'delete_comment.html',
        comment=comment,
        post_id=post_id
    )

# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)