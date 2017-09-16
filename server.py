from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector
import re
import md5
import os
import binascii

app = Flask(__name__)
mysql = MySQLConnector(app, 'wall')
app.secret_key = 'ThisIsSecret'

emailRegex = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
r = re.compile(r'[a-zA-Z]+')

dev = True

@app.route('/')
def index():
    if 'user' in session:
        redirect('/profile')
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def register():
    for key in request.form.keys():
        print request.form[key]
        if len(request.form[key]) < 2:
            flash("All fields are required")
            break
        elif not request.form['first_name'].isalpha(): 
            flash("Invalid  first name!")
            break
        elif not request.form['last_name'].isalpha():
            flash("Invalid Last Name!")
            break
        elif not emailRegex.match(request.form['email']):
            flash("Invalid email...")
            break
        elif len(request.form['password']) < 9:
            flash("Password must be at least 8 char!")
            break
        elif request.form['confirm_password'] != request.form['password']: 
            flash("Passwords do not match!")
            break
        else:
            salt = binascii.b2a_hex(os.urandom(15))
            password = request.form['password']
            hashed_pw = md5.new(password + salt).hexdigest()
            query = "INSERT INTO user (first_name, last_name, email, password, salt, created_at, updated_at) VALUES (:first_name, :last_name, :email, :hashed_pw, :salt, NOW(), NOW())"
            data = {
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'email': request.form['email'],
                'hashed_pw': hashed_pw,
                'salt': salt
            }
            session['user'] = mysql.query_db(query, data)
            print "hello"
            return redirect('/profile')
        return redirect('/profile')
    return redirect('/')


@app.route('/signIn', methods=['POST'])
def sign_in():
    email = request.form['email']
    user_query = "SELECT * FROM user WHERE email = :email LIMIT 1"
    query_data = {'email': request.form['email']}
    user = mysql.query_db(user_query, query_data)
    if len(user) != 0:
        password = request.form['password']
        encrypted_password = md5.new(password + user[0]['salt']).hexdigest()
        if user[0]['password'] == encrypted_password:
            session['user'] = user[0]['id']
            #print 'user'
            return redirect('/profile')
        else:
            flash("Wrong password or username!")
    return redirect('/')

@app.route('/profile')
def show_user():
    if 'user' not in session:
    	return redirect('/')
    user_query = "SELECT CONCAT(first_name, ' ', last_name) as name, email FROM user WHERE id = :id"
    query_data = {'id': session['user']}
    user = mysql.query_db(user_query, query_data)
    print user
    message_query = "select messages.users_id as id, concat(user.first_name, ' ', user.last_name) as name, message, DATE_FORMAT(messages.created_at, ' %b ' ' %D ' ' %Y') as date from user JOIN messages ON messages.users_id = user.id"
    session['message'] = mysql.query_db(message_query)

    comments_query = "select comments.messages_id as id, concat(user.first_name, ' ', user.last_name) as name, comment, DATE_FORMAT(comments.created_at, ' %b ' ' %D ' ' %Y') as date from messages LEFT JOIN user ON user.id = messages.users_id LEFT JOIN comments ON comments.messages_id = messages.id"
    session['comments'] = mysql.query_db(comments_query)
    return render_template('/profile.html', name=user[0]['name'])


@app.route('/message', methods=['POST'])
def post():
    query = "INSERT INTO messages (message, created_at, updated_at, users_id) VALUES (:message, NOW(), NOW(), :users_id)"
    data = {
        'message': request.form['message'],
        'users_id': session['user']
    }
    mysql.query_db(query, data)
    print request.form['message']
    return redirect("/profile")


@app.route('/comment', methods=['POST'])
def post_comment():
    query = "INSERT INTO comments (comment, created_at, updated_at, users_id, messages_id) VALUES (:comment, NOW(), NOW(), :users_id, messages_id)"
    data = {
        'comment': request.form['comment'],
        'users_id': session['user'],
        'messages_id': request.form['message_id'],
    }
    mysql.query_db(query, data)
    print request.form['comment']
    return redirect("/profile")


@app.route('/sign_out')
def back():
    session.clear()
    return render_template('index.html')

app.run(debug=dev)
