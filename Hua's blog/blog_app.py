import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
DATA_FILE = 'posts.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_posts(posts):
    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=4)

def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            posts = json.load(f)
            # Ensure every post has a 'comments' field
            for post in posts:
                if 'comments' not in post:
                    post['comments'] = []
            return posts
    return []


posts = load_posts()

@app.route('/')
def home():
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/new_post')
def new_post():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('new_post.html')

@app.route('/add_post', methods=['POST'])
def add_post():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    title = request.form['title']
    content = request.form['content']
    filename = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    posts.append({"title": title, "content": content, "filename": filename, "comments": []})
    save_posts(posts)
    return redirect(url_for('home'))

@app.route('/delete_post/<int:index>', methods=['POST'])
def delete_post(index):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    if 0 <= index < len(posts):
        del posts[index]
        save_posts(posts)
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    if request.form['password'] == 'Suijinyang@12':
        session['logged_in'] = True
    else:
        flash('Incorrect password!')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    try:
        post = posts[post_id] if 0 <= post_id < len(posts) else None
        if post is None:
            return "Post not found", 404
        return render_template('post.html', post=post, post_id=post_id)
    except Exception as e:
        app.logger.error(f"Error in view_post: {e}")
        return "An error occurred", 500

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    try:
        post = posts[post_id] if 0 <= post_id < len(posts) else None
        if post is None:
            return "Post not found", 404
        author = request.form['author']
        content = request.form['content']
        app.logger.info(f"Adding comment by {author}: {content}")
        post['comments'].append({"author": author, "content": content})
        app.logger.info(f"Updated comments: {post['comments']}")
        save_posts(posts)
        app.logger.info("Posts saved successfully.")
        return redirect(url_for('view_post', post_id=post_id))
    except Exception as e:
        app.logger.error(f"Error in add_comment: {e}")
        return "An error occurred", 500

@app.route('/delete_comment/<int:post_id>/<int:comment_index>', methods=['POST'])
def delete_comment(post_id, comment_index):
    try:
        post = posts[post_id] if 0 <= post_id < len(posts) else None
        if post is None:
            return "Post not found", 404
        if 0 <= comment_index < len(post['comments']):
            del post['comments'][comment_index]
            save_posts(posts)
        return redirect(url_for('view_post', post_id=post_id))
    except Exception as e:
        app.logger.error(f"Error in delete_comment: {e}")
        return "An error occurred", 500


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, host='0.0.0.0', port=5000)
