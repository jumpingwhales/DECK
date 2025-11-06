from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import redirect
from flask import url_for
import csv
import sqlite3
import random

app = Flask(__name__)

app.secret_key = "secret_key_testing"
DB_FILE = "blog_website.db"

def initialize_db():
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, bio TEXT, creation_date INTEGER);")
  c.execute("CREATE TABLE IF NOT EXISTS blogs(blog_name TEXT, blog_creator TEXT, blog_link TEXT, blog_content TEXT, last_edited INTEGER);")
  c.execute("CREATE TABLE IF NOT EXISTS edits(edited_blog_name TEXT, blog_creator TEXT, timestamps TEXT);")

  db.commit()
  db.close()

@app.route("/", methods=['GET', 'POST'])
def index():
  if 'username' in session:
    return redirect(url_for('homepage'))
  else:
    text = "welcome"
    return render_template('login.html', text=text)

@app.route("/login", methods=["GET", "POST"])
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

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    username = request.form['username']
    password = request.form['password']
    creation_date = 0
    cmd = f"INSERT into users VALUES ('{username}', '{password}', 'temp', '{creation_date}')"
    c.execute(cmd)
    db.commit()
    db.close()
    session['username'] = username
    return redirect(url_for('homepage'))
  return render_template('register.html')

@app.route("/homepage")
def homepage():
  if 'username' not in session:
    return redirect(url_for('index'))
  posts = ""
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  c.execute("select * from blogs")
  posts = c.fetchall()

  return render_template('homepage.html', username = session['username'], posts = posts)

@app.route("/logout")
def logout():
  session.pop('username', None)
  return redirect(url_for('index'))

@app.route("/create_page", methods=["GET", "POST"])
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

        blog_content = request.form.get("content", "")
        blog_link = blog_content.replace(" ", "_")

        last_edited = 0

        cmd = f"INSERT into blogs VALUES ('{blog_name}', '{blog_creator}', '{blog_link}', '{blog_content}', {last_edited})"
        print(cmd)
        c.execute(cmd)
        db.commit()
        db.close()

        return redirect(url_for('homepage'))

@app.route("/edit_page", methods=["GET", "POST"])
def edit_page():

    if request.method == "GET":
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        c.execute("SELECT blog_name, blog_creator, blog_content FROM blogs")
        blogs = c.fetchall()
        db.close()

        return render_template('edit_page.html', blogs=blogs)


    if request.method == "POST":
      db = sqlite3.connect(DB_FILE)
      c = db.cursor()

      blog_name = request.form['title']

      blog_creator = session['username']

      text = request.form['title']
      result = text.replace(" ", "_")
      blog_link = result

      blog_content = request.form['content']

      cmd = f"UPDATE blogs SET blog_content = '{blog_content}', last_edited = last_edited + 1 WHERE blog_name = '{blog_name}'"
      c.execute(cmd)

      timestamp = 0
      edit_cmd = f"INSERT INTO edits VALUES ('{blog_name}', '{blog_creator}', '{timestamp}')"
      c.execute(edit_cmd)

      db.commit()
      db.close()

      return redirect(url_for('homepage'))

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
