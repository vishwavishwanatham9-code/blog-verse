from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import os

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================

app.secret_key = "blogverse_secret"

# =========================
# DATABASE
# =========================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'blogverse.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =========================
# CLOUDINARY
# =========================

cloudinary.config(
    cloud_name="dytdch3w5",
    api_key="754274292374841",
    api_secret="pl9tcSg-eC_Uahnv-yXe1ut1qa0"
)

# =========================
# ADMIN PASSWORD
# =========================

ADMIN_PASSWORD = "admin123"

# =========================
# MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    content = db.Column(db.Text)
    filename = db.Column(db.String(500))
    type = db.Column(db.String(50))
    likes = db.Column(db.Integer, default=0)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    text = db.Column(db.String(500))

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    post_id = db.Column(db.Integer)
# =========================
# CREATE DATABASE
# =========================

with app.app_context():
    db.create_all()

# =========================
# HOME
# =========================

@app.route('/')
def home():

    if 'username' not in session:
        return redirect('/login')

    posts = Post.query.order_by(Post.id.desc()).all()

    return render_template(
        'home.html',
        posts=posts,
        username=session['username'],
        Comment=Comment
    )

# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "User already exists"

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

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:

            session['username'] = username

            return redirect('/')

        else:
            return "Invalid Email or Password"

    return render_template('login.html')

# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/login')

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

        file = request.files['image']

        if file:

            filename = secure_filename(file.filename)

            extension = filename.split('.')[-1].lower()

            image_extensions = ['png', 'jpg', 'jpeg', 'gif']

            # IMAGE
            if extension in image_extensions:

                upload_result = cloudinary.uploader.upload(file)

                file_url = upload_result['secure_url']

                post = Post(
                    title=title,
                    content=content,
                    filename=file_url,
                    type='image'
                )

            # FILE
            else:

                os.makedirs('static/files', exist_ok=True)

                filepath = os.path.join('static/files', filename)

                file.save(filepath)

                post = Post(
                    title=title,
                    content=content,
                    filename=filename,
                    type='file'
                )

            db.session.add(post)
            db.session.commit()

            return redirect('/')

    return render_template('create.html')
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
@app.route("/like/<int:post_id>")
def like(post_id):

    if "username" not in session:
        return redirect("/login")

    username = session["username"]

    liked = Like.query.filter_by(
        username=username,
        post_id=post_id
    ).first()

    post = Post.query.get(post_id)

    if liked:
        db.session.delete(liked)

        if post.likes > 0:
            post.likes -= 1

    else:
        new_like = Like(
            username=username,
            post_id=post_id
        )

        db.session.add(new_like)
        post.likes += 1

    db.session.commit()

    return redirect("/")
# =========================
# COMMENT
# =========================

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):

    text = request.form['comment']

    new_comment = Comment(
        post_id=post_id,
        text=text
    )

    db.session.add(new_comment)
    db.session.commit()

    return redirect('/')

# =========================
# DELETE POST
# =========================

@app.route('/delete/<int:post_id>', methods=['GET', 'POST'])
def delete(post_id):

    post = Post.query.get(post_id)

    if not post:
        return "Post not found"

    if request.method == 'POST':

        password = request.form['password']

        if password == ADMIN_PASSWORD:

            Comment.query.filter_by(post_id=post_id).delete()

            db.session.delete(post)

            db.session.commit()

            return redirect('/')

        else:
            return "Wrong Admin Password"

    return render_template('delete.html')

# =========================
# DELETE COMMENT
# =========================

@app.route('/delete_comment/<int:post_id>/<int:comment_id>', methods=['GET', 'POST'])
def delete_comment(post_id, comment_id):

    comment = Comment.query.get(comment_id)

    if not comment:
        return "Comment not found"

    if request.method == 'POST':

        password = request.form['password']

        if password == ADMIN_PASSWORD:

            db.session.delete(comment)

            db.session.commit()

            return redirect('/')

        else:
            return "Wrong Admin Password"

    return render_template('delete_comment.html')

# =========================
# MAIN
# =========================

if __name__ == '__main__':
    app.run(debug=True)