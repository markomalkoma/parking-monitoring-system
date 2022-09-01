from flasker.style import input_ok, input_error, submit, input_main, error_main
from flask import render_template, redirect, url_for, send_file, flash, request
from flasker import app, db
from flasker.forms import RegistrationForm, LoginForm, ParkingSpaceForm, ExitForm, StoperForm, AdminForm, DataForm
from flasker.models import User
from datetime import datetime
from flask_login import login_user, current_user, logout_user, login_required
import json


@app.route("/register", methods = ['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main')) 
    form = RegistrationForm()
    if form.validate_on_submit():# u protivnom ce samo ostati na toj strani
        user = User(username=form.username.data, 
                    email=form.email.data, 
                    phone=form.phone.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        form = LoginForm()
        return redirect(url_for('login',
                            form = form, 
                            input_ok = input_ok, 
                            input_error = input_error,
                            submit = submit))
    return render_template('register.html', 
                            form = form, 
                            input_ok = input_ok, 
                            input_error = input_error,
                            submit = submit)

'''
bez:
methods=['GET', 'POST']
Method Not Allowed
The method is not allowed for the requested URL.
'''

@app.route('/', methods=['GET', 'POST'])
@app.route("/login", methods=['GET', 'POST']) #urls must start with leading slash
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main')) 
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('main'))   
    return render_template('login.html', 
                            form = form, 
                            input_ok = input_ok, 
                            input_error = input_error,
                            submit = submit)


@app.route("/main", methods=['GET', 'POST'])
@login_required
def main():
    form = ParkingSpaceForm()
    if form.validate_on_submit():
        form = ParkingSpaceForm()
        parking_id=form.parking_id.data
        user = current_user
        user.parking_space = parking_id
        user.call_time = datetime.today()
        user.calls += 1
        user.status = 1
        db.session.commit()
        return redirect (url_for('exit'))
    return render_template('main.html', 
                            form=form,
                            input_ok = input_main, 
                            input_error = error_main,
                            submit = submit)


@app.route("/exit", methods=['GET', 'POST'])
@login_required
def exit():
    form = ExitForm()
    if form.validate_on_submit():
        user = current_user
        user.status = 0
        db.session.commit()  
        return redirect(url_for('main'))  
    user = current_user
    time = user.call_time.strftime('%Hh : %Mm : %Ss')
    space = user.parking_space
    username = user.username
    return render_template('exit.html',
                            form = form,
                            time = time,
                            space = space,
                            username = username,
                            submit = submit)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))   


@app.route("/api")
def api():
    objects = User.query.all()
    listing = {}
    listing['active'] = []
    for object in objects:
        d = {}
        d['ID'] = object.id
        d['TIME'] = object.call_time.strftime('%H %M %S')
        d['SPACE'] = object.parking_space
        d['STATUS'] = object.status
        d['COLLEAGUE'] = object.colleague
        listing['active'].append(d)
    return listing


#https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask

# post method - saffer
# r = requests.post(url, data = data)
# moglo bi jednostavnije sa  /stoper/<string:password>/<int:user_id> ali nije bezbedno i nema html
@app.route('/stoper', methods = ['GET','POST'])
def stoper():
    form = StoperForm()
    if request.method == 'POST': #if form.validate_on_submit(): - NE RADI jer nema submita (verovatno zbog toga)
        password = request.form.get('password')#names of form fields
        user_id = int(request.form.get('user_id'))#returned as a string
        admin = User.query.get(1)       
        if admin.password == password:
            user = User.query.get(user_id)
            user.status = 0
            db.session.commit() 
        return redirect(url_for('api'))    
    return render_template('stoper.html',
                            form = form,
                            input_main = input_main, 
                            input_ok = input_ok, 
                            input_error = input_error,
                            error_main = error_main,
                            submit = submit)


# moze i bez html-a
# r = requests.post(url, json = data)
@app.route('/jsoner', methods = ['POST'])
def jsoner():
    data = request.get_json()
    paser = data['paser']
    id = int(data['id'])
    admin = User.query.get(1)   
    if admin.password == paser:
        user = User.query.get(id)
        user.status = 0
        db.session.commit() 
    return redirect(url_for('api')) 


# uz def admin..
def complete():
    users = {'active':[]}
    complete = User.query.all()
    for user in complete:
        user_dict = {}
        user_dict['id'] = user.id
        user_dict['registration'] = user.registration_time.strftime("%Y/%m/%d %H:%M:%S")
        user_dict['email'] = user.email
        user_dict['permission'] = user.colleague
        user_dict['phone'] = user.phone
        user_dict['calls'] = user.calls
        user_dict['status'] = user.status
        user_dict['call_time'] = user.call_time
        users['active'].append(user_dict)
        users['active'] = sorted(users['active'], key=lambda x: x['registration'], reverse=True)
    return users

def admin_template(users, form):
    return render_template('admin.html',
                            users = users,
                            form = form,
                            input_main = input_main, 
                            input_ok = input_ok, 
                            input_error = input_error,
                            error_main = error_main,
                            submit = submit)

@app.route('/admin', methods = ['GET','POST'])
def admin():
    form = AdminForm()
    users = complete()
    if form.validate_on_submit():
        form = AdminForm()
        admin = User.query.get(1)
        if admin.password == form.password.data:
            user=User.query.get(form.ID.data)
            user.colleague=form.permission.data
            db.session.commit()
            users = complete()
            return admin_template(users, form)
    return admin_template(users, form)


@app.route('/data/<string:paser>')
def data(paser):
    admin = User.query.get(1)
    if admin.password == paser:
        objects = User.query.all()
        listing = {}
        listing['active'] = []
        for object in objects:
            d = {}
            d['ID'] = object.id
            d['TIME'] = object.call_time.strftime('%H %M %S')
            d['SPACE'] = object.parking_space
            d['PHONE'] = object.phone
            d['STATUS'] = object.status
            d['COLLEAGUE'] = object.colleague
            listing['active'].append(d)
        return listing


# send data in file
@app.route('/filer', methods = ['GET','POST'])
def filer():
    form = DataForm()
    if form.validate_on_submit():
        admin = User.query.get(1)       
        if admin.password == form.password.data:
            users = User.query.all()
            data= {}
            for user in users:
                data[user.id] = user.phone
                with open('data.json', 'w') as f:
                    json.dump(data, f, indent = 4)
            return send_file('../data.json', as_attachment = True, attachment_filename='colleagues.json')
    return render_template('data.html',
                            form = form,
                            input_ok = input_ok, 
                            input_error = input_error,
                            submit = submit)
