from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail,Message
from flask_migrate import Migrate


#instantiate an object of Flask
app = Flask(__name__,instance_relative_config=True)

csrf=CSRFProtect(app)

from conferenceapp import config
app.config.from_object(config.ProductionConfig)
app.config.from_pyfile('config.py',silent=False)


db =SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app,db)

#load your routes here

from conferenceapp.myroutes import adminroute,userroute
from conferenceapp import forms
from conferenceapp import models

#load he config
