from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#$pip install flask-login
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '36ce948df933389b9cf86d8d864bb98f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

#manage user sessions (login/logout)
login_manager = LoginManager(app)
# kao u djangu - moras reci aplikaciji ako stranica odbija logovanje gde da ode
login_manager.login_view = 'login'

from flasker import rutes

