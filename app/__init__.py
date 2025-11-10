from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import redirect
from flask import url_for
import csv
import sqlite3
import random
import time
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret_key_testing"
DB_FILE = "blog_website.db"

def initialize_db():
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, bio TEXT, creation_date INTEGER);")
  c.execute("CREATE TABLE IF NOT EXISTS blogs(blog_name TEXT, blog_creator TEXT, creation_date INTEGER);")
  c.execute("CREATE TABLE IF NOT EXISTS entries(entry_title TEXT, entry_content TEXT, blog_name TEXT, blog_creator TEXT, timestamp INTEGER);")

  db.commit()
  db.close()

@app.route("/", methods=['GET', 'POST']) # load homepage if session exists, otherwise go to login
def index():
  if 'username' in session:
    return redirect(url_for('homepage'))
  else:
    text = ""
    return render_template('login.html', text=text)

@app.route("/login", methods=["GET", "POST"]) # log in to preexisting account on site
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    cmd = f"SELECT * FROM users WHERE username = '{username}'"
    c.execute(cmd)
    user = c.fetchone()
    db.close()

    if user == None  or user[0] != username or user[1] != password:
        print("username or password do not match records")
        text = "login failed, create new acc?"
        return render_template('login.html', text=text)
    elif  user[0] == username and user[1] == password:
      session['username'] = username
      return redirect(url_for('homepage'))
    else:
      return redirect(url_for('index'))
  return redirect(url_for('index'))

@app.route("/register", methods=["GET", "POST"]) # create new account and add to database
def register():
  if request.method == "POST":
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    username = request.form['username']
    password = request.form['password']

    # Check if username already exists
    cmd = f"SELECT * FROM users WHERE username = '{username}'"
    c.execute(cmd)
    existing_user = c.fetchone()

    if existing_user:
      db.close()
      text = "username already taken, try another one!"
      return render_template('register.html', text=text)

    bio = ""
    creation_date = int(time.time())

    cmd = f"INSERT into users VALUES ('{username}', '{password}', '{bio}', '{creation_date}')"
    c.execute(cmd)
    db.commit()
    db.close()
    session['username'] = username
    return redirect(url_for('homepage'))
  return render_template('register.html')

@app.route("/homepage") # welcome message and display of latest blogs
def homepage():
  if 'username' not in session:
    return redirect(url_for('index'))
  posts = ""
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  c.execute("select * from blogs ORDER BY creation_date DESC")
  posts = c.fetchall()
  db.close()

  # Format timestamps to EST
  formatted_posts = []
  for post in posts:
    blog_name, blog_creator, creation_date = post
    dt = datetime.fromtimestamp(creation_date)
    formatted_date = dt.strftime('%B %d, %Y at %I:%M %p EST')
    formatted_posts.append((blog_name, blog_creator, formatted_date))

  return render_template('homepage.html', username = session['username'], posts = formatted_posts)

@app.route("/logout")
def logout():
  session.pop('username', None)
  return redirect(url_for('index'))

@app.route("/profile", methods=["GET", "POST"]) # user profile
def profile():
    if 'username' not in session:
      return redirect(url_for('index'))
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    username = session['username']

    c.execute("SELECT bio from users WHERE username = ?", (username,))
    result = c.fetchone()
    bio = result[0] if result and result[0] else None

    c.execute("SELECT blog_name FROM blogs WHERE blog_creator = ?", (username,))
    blogs_raw = c.fetchall()

    # Get last edited date for each blog
    blogs = []
    for blog in blogs_raw:
        blog_name = blog[0]
        c.execute("SELECT MAX(timestamp) FROM entries WHERE blog_name = ?", (blog_name,))
        last_edit = c.fetchone()[0]
        if last_edit:
            dt = datetime.fromtimestamp(last_edit)
            formatted_date = dt.strftime('%B %d, %Y at %I:%M %p EST')
            blogs.append((blog_name, formatted_date))
        else:
            blogs.append((blog_name, "No entries yet"))

    db.close()
    return render_template("profile_page.html", username = username, bio = bio, curr_user = session['username'], blogs = blogs)

@app.route("/profile/<username>") # for viewing other people's profiles
def view_profile(username):
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    bio = result[0] if result and result[0] else None

    c.execute("SELECT blog_name FROM blogs WHERE blog_creator = ?", (username,))
    blogs_raw = c.fetchall()

    # Get last edited date for each blog
    blogs = []
    for blog in blogs_raw:
        blog_name = blog[0]
        c.execute("SELECT MAX(timestamp) FROM entries WHERE blog_name = ?", (blog_name,))
        last_edit = c.fetchone()[0]
        if last_edit:
            dt = datetime.fromtimestamp(last_edit)
            formatted_date = dt.strftime('%B %d, %Y at %I:%M %p EST')
            blogs.append((blog_name, formatted_date))
        else:
            blogs.append((blog_name, "No entries yet"))

    db.close()
    return render_template("profile_page.html", username = username, bio = bio, curr_user = session['username'], blogs = blogs)


@app.route("/edit_profile", methods=["GET", "POST"]) # edit bio in user profile
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    if request.method == "POST":
        bio = request.form.get("bio")
        if bio is not None:
            c.execute("UPDATE users SET bio = ? WHERE username = ?", (bio, username))
            db.commit()
        db.close()
        return redirect(url_for('profile'))

    c.execute("SELECT bio FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    bio = result[0] if result and result[0] else None

    db.close()
    return render_template("edit_profile.html", username = username, bio = bio)


@app.route("/create_page", methods=["GET", "POST"]) # create new blog container
def create_page():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == "GET":
        user = session['username']
        return render_template('create_page.html', user=user)

    if request.method == "POST":
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        blog_name = request.form.get("title", "")
        blog_creator = session['username']
        creation_date = int(time.time())

        cmd = f"INSERT into blogs VALUES ('{blog_name}', '{blog_creator}', {creation_date})"
        print(cmd)
        c.execute(cmd)

        # Add initial entry
        entry_title = request.form.get("entry_title", "")
        entry_content = request.form.get("entry_content", "")
        timestamp = int(time.time())

        cmd = f"INSERT INTO entries VALUES ('{entry_title}', '{entry_content}', '{blog_name}', '{blog_creator}', {timestamp})"
        c.execute(cmd)

        db.commit()
        db.close()

        return redirect(url_for('homepage'))

@app.route("/edit_page") # show user's blogs as clickable list
def edit_page():
    if 'username' not in session:
        return redirect(url_for('index'))

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    username = session['username']

    c.execute(f"SELECT blog_name, blog_creator FROM blogs WHERE blog_creator = '{username}'")
    blogs = c.fetchall()
    db.close()

    return render_template('edit_page.html', blogs=blogs)

@app.route("/view_blog/<blog_name>") # view blog and its entries
def view_blog(blog_name):
    if 'username' not in session:
        return redirect(url_for('index'))

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    c.execute(f"SELECT blog_creator FROM blogs WHERE blog_name = '{blog_name}'")
    blog_info = c.fetchone()

    c.execute(f"SELECT entry_title, entry_content, timestamp FROM entries WHERE blog_name = '{blog_name}' ORDER BY timestamp DESC")
    entries = c.fetchall()
    db.close()

    blog_creator = blog_info[0] if blog_info else ""

    # Format timestamps for entries
    formatted_entries = []
    for entry in entries:
        entry_title, entry_content, timestamp = entry
        dt = datetime.fromtimestamp(timestamp)
        formatted_date = dt.strftime('%B %d, %Y at %I:%M %p EST')
        formatted_entries.append((entry_title, entry_content, formatted_date))

    return render_template('view_blog.html', blog_name=blog_name, blog_creator=blog_creator, entries=formatted_entries)

@app.route("/edit_blog/<blog_name>", methods=["GET", "POST"]) # edit blog entries
def edit_blog(blog_name):
    if 'username' not in session:
        return redirect(url_for('index'))

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    if request.method == "POST":
        entry_title = request.form.get("entry_title", "")
        entry_content = request.form.get("entry_content", "")
        old_title = request.form.get("old_title", "")
        blog_creator = session['username']

        if old_title:
            timestamp = int(time.time())
            cmd = f"UPDATE entries SET entry_title = '{entry_title}', entry_content = '{entry_content}', timestamp = {timestamp} WHERE blog_name = '{blog_name}' AND entry_title = '{old_title}'"
            c.execute(cmd)
        else:
            timestamp = int(time.time())
            cmd = f"INSERT INTO entries VALUES ('{entry_title}', '{entry_content}', '{blog_name}', '{blog_creator}', {timestamp})"
            c.execute(cmd)

        db.commit()
        db.close()
        return redirect(url_for('edit_blog', blog_name=blog_name))

    c.execute(f"SELECT blog_creator FROM blogs WHERE blog_name = '{blog_name}'")
    blog_info = c.fetchone()

    c.execute(f"SELECT entry_title, entry_content, timestamp FROM entries WHERE blog_name = '{blog_name}' ORDER BY timestamp DESC")
    entries = c.fetchall()
    db.close()

    blog_creator = blog_info[0] if blog_info else ""

    if blog_creator != session['username']:
        return redirect(url_for('homepage'))

    return render_template('edit_blog.html', blog_name=blog_name, entries=entries)

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
