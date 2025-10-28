from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import redirect
from flask import url_for
import csv
import sqlite3

app = Flask(__name__)

DB_FILE = "blog_website.db"

db = sqlite3.connect(DB_FILE)
c = db.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, bio TEXT, creation_date INTEGER);")
c.execute("CREATE TABLE IF NOT EXISTS blogs(blog_name TEXT, blog_creator TEXT, blog_link TEXT, blog_content TEXT, last_edited INTEGER);")
c.execute("CREATE TABLE IF NOT EXISTS edits(edited_blog_name TEXT, blog_creator TEXT, timestamps TEXT);")

c.execute("DELETE FROM users")
c.execute("DELETE FROM blogs")
c.execute("DELETE FROM edits")

@app.route("/", methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('loggedIn'))
    return render_template('login.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
       username = request.form['username']
       password = request.form['password']
       session['username'] = username
    return render_template('register.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
       username = request.form['username']
       password = request.form['password']
       cmd = f"INSERT into users VALUES '{username}', '{password}'"
       c.execute(cmd)
       return render_template('homepage.html')

@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    return render_template("template.html") # placeholder

@app.route("/logout")
def logout():
    session.pop('username', None)
    return render_template('logout.html')

if __name__ == "__main__":
    app.debug = True
    app.run()
