
from flask import Flask, render_template,request, session, redirect, send_file, flash
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug import secure_filename
import math
from datetime import datetime
from flask_mail import Mail
import os

with open("config.json",'r') as c:
    params = json.load(c)["params"]
local_server= False

app = Flask(__name__,template_folder='Templates',static_folder="Static")
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)

mail = Mail(app)
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db= SQLAlchemy(app)
print("Connection Successfully!")
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.String(4000), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12))

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    subtitle = db.Column(db.String(45), nullable=False)
    content = db.Column(db.String(4500), nullable=False)
    date = db.Column(db.String(12))
    img_file = db.Column(db.String(20), nullable=False)




@app.route("/")
def home():
    posts = Posts.query.filter_by().all() #[0:params['no_of_post']]
    last = math.ceil(len(posts)/int (params['no_of_post']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int (params['no_of_post']):(page-1)*int (params['no_of_post'])+int (params['no_of_post'])]
    if (page == 1):
        prev = "#"
        next = "/?page="+str(page+1)
    elif (page == last):
        prev = "/?page="+str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template ("index.html", params=params, posts = posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template("about.html", params=params, post= posts)

@app.route("/dashboard", methods = ['GET','POST'] )
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template("dashboard.html",params=params, posts = posts)


    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('psw')
        if (username == params['admin_user'] and userpass == params['password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    return render_template("login.html", params=params)

@app.route("/edit/<string:sno>", methods = ['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            subtitle = request.form.get('subtitle')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if sno == '0':
                post = Posts(title= box_title, slug = slug, subtitle=subtitle, content = content, img_file = img_file, date = date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(sno = sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.subtile = subtitle
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect("/edit/" +sno)
        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params = params, post = post, sno=sno)


@app.route("/uploader", methods = ['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename (f.filename)))
            return "uploaded successfully"
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:sno>", methods = ['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno = sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")


@app.route("/contact", methods = ['GET','POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone= request.form.get('phone')
        msg= request.form.get('msg')
        entry = Contacts(name = name, phone = phone, msg = msg, date = datetime.now(), email = email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From Blog user'+ name,
                          sender = email,
                          recipients = [params['gmail_user']],
                          body = msg + "\n" + phone + "\n" + email
                          )
    
        flash("Thanks for submitting your details. We will get back to you soon", "success")
    return render_template("contact.html", params= params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def posts(post_slug):
    posts = Posts.query.filter_by(slug = post_slug).first()
    return render_template("post.html", params=params, post = posts)

#app.run(debug = True)
