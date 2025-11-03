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
  return render_template('login.html')

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

    if user[0] == username and user[1] == password:
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
    cmd = f"INSERT into users VALUES ('{username}', '{password}', '', {creation_date})"
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
  for row in c.execute("select * from blogs"):
      # header for each blog
      posts = posts +  "<h3>" + row[0] + " by " + row[1] + "</h3>"
      # content for each blog
      posts = posts + "<br>" + row[3]
      # last edited date (revise row[4] entry later based on how last_edited is stored)
      posts = posts + "<br>last edited on " + row[4]

  return render_template('homepage.html', username = session['username'], posts = posts)

@app.route("/logout")
def logout():
  session.pop('username', None)
  return redirect(url_for('index'))

@app.route("/create_page", methods=["GET", "POST"])
def create_page():
  if request.method == "POST":
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()

    blog_name = request.form['title']

    blog_creator = session['username']

    text = request.form['title']
    result = text.replace(" ", "_") #may need to be changed based on strange symbols
    blog_link = result

    blog_content = request.form['content']

    last_edited = 0

    cmd = f"INSERT into blogs VALUES ('{blog_name}', '{blog_creator}', '{blog_link}', '{blog_content}', {last_edited})"
    c.execute(cmd)
    db.commit()
    db.close()

    return redirect(url_for('homepage'))
  return render_template('create_page.html')

@app.route("/edit_page", methods=["GET", "POST"])
def edit_page():

    if request.method == "GET":
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        title = request.form("og_blog_name")
        og_title = f"SELECT * FROM blogs WHERE title = {title}"


    if request.method == "POST":
      db = sqlite3.connect(DB_FILE)
      c = db.cursor()

      blog_name = request.form['title']

      blog_creator = session['username']

      text = request.form['title']
      result = text.replace(" ", "_") #may need to be changed based on strange symbols
      blog_link = result

      blog_content = request.form['content']

      last_edited = last_edited + 1

      cmd = f"INSERT into blogs VALUES ('{blog_name}', '{blog_creator}', '{blog_link}', '{blog_content}', {last_edited})"
      c.execute(cmd)
      db.commit()
      db.close()

      return redirect(url_for('homepage'))
    return render_template('edit_page.html')

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
