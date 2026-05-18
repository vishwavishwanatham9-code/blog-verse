from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
# ADMIN SETTINGS
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_DELETE_PASSWORD = "admin123"
app.secret_key = "blogverse"
ADMIN_PASSWORD = "admin123"

UPLOAD_FOLDER = 'static/images'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create images folder automatically
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

posts = []

users = {}

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:

            session['username'] = username

            return redirect('/home')

        else:
            return "Invalid Username or Password"

    return render_template('login.html')

# REGISTER
# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not re.match(email_pattern, username):
            return "Invalid Email Address"

        users[username] = password

        return redirect('/')

    return render_template('register.html')

# HOME
@app.route('/home')
def home():

    if 'username' not in session:
        return redirect('/')

    return render_template(
        'home.html',
        posts=posts,
        username=session['username']
    )

# CREATE POST
@app.route('/create', methods=['GET', 'POST'])
def create():

    if request.method == 'POST':

        title = request.form['title']
        content = request.form['content']

        file = request.files['image']

        filename = file.filename

        # File Extension
        extension = filename.split('.')[-1].lower()

        image_extensions = ['png', 'jpg', 'jpeg', 'gif']

        # Save Images
        if extension in image_extensions:
            file.save(os.path.join('static/images', filename))
            file_type = 'image'

        # Save Other Files
        else:
            file.save(os.path.join('static/files', filename))
            file_type = 'file'

        posts.append({
            'title': title,
            'content': content,
            'filename': filename,
            'type': file_type,
            'likes': 0,
            'comments': []
        })

        return redirect('/home')

    return render_template('create.html')
# LIKE
@app.route('/like/<int:id>')
def like(id):

    posts[id]['likes'] += 1

    return redirect('/home')

# COMMENT
@app.route('/comment/<int:id>', methods=['POST'])
def comment(id):

    text = request.form['comment']

    if text:
        posts[id]['comments'].append(text)

    return redirect('/home')
    
    # DELETE COMMENT
@app.route('/delete_comment/<int:post_id>/<int:comment_id>', methods=['GET', 'POST'])
def delete_comment(post_id, comment_id):

    if 'username' not in session:
        return redirect('/')

    username = session['username']

    # Only admin can delete comments
    if username != ADMIN_EMAIL:
        return "Only Admin Can Delete Comments"

    if request.method == 'POST':

        password = request.form['password']

        # Check admin password
        if password == ADMIN_DELETE_PASSWORD:

            if post_id < len(posts):

                if comment_id < len(posts[post_id]['comments']):

                    posts[post_id]['comments'].pop(comment_id)

            return redirect('/home')

        else:
            return "Wrong Admin Password"

    return render_template(
        'delete_comment.html',
        post_id=post_id,
        comment_id=comment_id
    )
# # ADMIN PASSWORD
ADMIN_PASSWORD = "navya123"

# DELETE POST WITH ADMIN AUTHORITY
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):

    # Check login
    if 'username' not in session:
        return redirect('/')

    if request.method == 'POST':

        admin_password = request.form['password']

        # Only admin password can delete
        if admin_password == ADMIN_PASSWORD:

            if id < len(posts):
                posts.pop(id)

            return redirect('/home')

        else:
            return "Only Admin Can Delete Posts"

    return render_template('delete.html', id=id)
# LOGOUT
@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)