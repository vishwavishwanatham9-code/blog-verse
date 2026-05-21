from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, session
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogverse.db'

db = SQLAlchemy(app)

# =========================
# DATABASE MODELS
# =========================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(100))


class Post(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    content = db.Column(db.Text)

    filename = db.Column(db.String(500))

    type = db.Column(db.String(20))

    likes = db.Column(db.Integer, default=0)


class Comment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(db.String(500))

    post_id = db.Column(
        db.Integer,
        db.ForeignKey('post.id')
    )

# =========================
# CLOUDINARY CONFIG
# =========================

cloudinary.config(
    cloud_name="dytdch3w5",
    api_key="754274292374841",
    api_secret="pl9tcSg-eC_Uahnv-yXe1ut1qa0"
)

# =========================
# ADMIN SETTINGS
# =========================

ADMIN_EMAIL = "admin@gmail.com"

ADMIN_DELETE_PASSWORD = "admin123"

app.secret_key = "blogverse"

# =========================
# UPLOAD FOLDER
# =========================

UPLOAD_FOLDER = 'static/images'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

os.makedirs('static/files', exist_ok=True)

# =========================
# LOGIN
# =========================

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(
            email=username,
            password=password
        ).first()

        if user:

            session['username'] = username

            return redirect('/home')

        else:
            return "Invalid Username or Password"

    return render_template('login.html')

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_pattern, username):
            return "Invalid Email Address"

        existing_user = User.query.filter_by(email=username).first()

        if existing_user:
            return "Email Already Registered"

        new_user = User(
            email=username,
            password=password
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect('/')

    return render_template('register.html')

# =========================
# HOME
# =========================

@app.route('/home')
def home():

    if 'username' not in session:
        return redirect('/')

    return render_template(
        'home.html',
        posts=Post.query.all(),
        username=session['username'],
        Comment=Comment
    )

# =========================
# CREATE POST
# =========================

@app.route('/create', methods=['GET', 'POST'])
def create():

    if 'username' not in session:
        return redirect('/')

    if request.method == 'POST':

        title = request.form['title']

        content = request.form['content']

        file = request.files['image']

        filename = secure_filename(file.filename)

        extension = filename.split('.')[-1].lower()

        image_extensions = ['png', 'jpg', 'jpeg', 'gif']

        if extension in image_extensions:

            result = cloudinary.uploader.upload(file)

            file_url = result['secure_url']

            file_type = 'image'

        else:

            file.save(os.path.join('static/files', filename))

            file_url = filename

            file_type = 'file'

        new_post = Post(
            title=title,
            content=content,
            filename=file_url,
            type=file_type
        )

        db.session.add(new_post)

        db.session.commit()

        return redirect('/home')

    return render_template('create.html')

# =========================
# LIKE POST
# =========================

@app.route('/like/<int:id>')
def like(id):

    post = Post.query.get(id)

    if post:

        post.likes += 1

        db.session.commit()

    return redirect('/home')

# =========================
# COMMENT
# =========================

@app.route('/comment/<int:id>', methods=['POST'])
def comment(id):

    text = request.form['comment']

    if text:

        new_comment = Comment(
            text=text,
            post_id=id
        )

        db.session.add(new_comment)

        db.session.commit()

    return redirect('/home')
# DELETE COMMENT
# DELETE COMMENT
@app.route('/delete_comment/<int:post_id>/<int:comment_id>', methods=['GET', 'POST'])
def delete_comment(post_id, comment_id):

    if 'username' not in session:
        return redirect('/')

    username = session['username']

    # ONLY ADMIN CAN DELETE COMMENTS
    if username != "admin@gmail.com":
        return "Only Admin Can Delete Comments"

    if request.method == 'POST':

        password = request.form['password']

        # CHECK ADMIN PASSWORD
        if password == "admin123":

            comment = Comment.query.get(comment_id)

            if comment:
                db.session.delete(comment)
                db.session.commit()

            return redirect('/home')

        else:
            return "Wrong Admin Password"

    return render_template(
        'delete_comment.html',
        post_id=post_id,
        comment_id=comment_id
    )
    # =========================
# =========================
# DELETE POST
# =========================

@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_post(id):

    # CHECK LOGIN
    if 'username' not in session:
        return redirect('/')

    username = session['username']

    # ONLY ADMIN CAN DELETE POSTS
    if username != ADMIN_EMAIL:
        return "Only Admin Can Delete Posts"

    # GET POST
    post = Post.query.get(id)

    if not post:
        return "Post Not Found"

    # WHEN PASSWORD SUBMITTED
    if request.method == 'POST':

        password = request.form['password']

        # CHECK ADMIN PASSWORD
        if password == ADMIN_DELETE_PASSWORD:

            # DELETE ALL COMMENTS OF POST
            comments = Comment.query.filter_by(post_id=id).all()

            for comment in comments:
                db.session.delete(comment)

            # DELETE POST
            db.session.delete(post)

            db.session.commit()

            return redirect('/home')

        else:
            return "Wrong Admin Password"

    # OPEN DELETE PAGE
    return render_template(
        'delete_post.html',
        post_id=id
    )
if __name__ == "__main__":

      with app.app_context():
        db.create_all()

app.run(debug=True)