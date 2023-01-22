from flask import Flask, jsonify, request, Response, render_template, send_file, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy  import SQLAlchemy
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from io import BytesIO
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from db import db_init, db
from models import Img,User
import random,requests
from flask_mail import Mail,Message
from flask_cors import CORS, cross_origin


app = Flask(__name__)
# SQLAlchemy config. Read more: https://flask-sqlalchemy.palletsprojects.com/en/2.x/

app.config['SECRET_KEY'] = 'scriptProject'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['CORS_HEADERS'] = 'Content-Type'
app.config["CACHE_TYPE"] = "null"
app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"]= 465
app.config["MAIL_USERNAME"]='yuyeensan@kkumail.com'
app.config['MAIL_PASSWORD']=''                    #you have to give your password of gmail account
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
mail = Mail(app)

cors = CORS(app)

db_init(app)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


url = 'https://notify-api.line.me/api/notify'
token = 'MPEt71sg8IbygPqMxFvoaZ9RLS0IY3VodTSaHWV20ow'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+ token}


@app.route('/')
@cross_origin()
def starter():
    return render_template("starter.html")

@app.route('/index')
@cross_origin()
def index():
    return render_template("index.html")

@app.route('/otp-message', methods=['POST'])
@cross_origin()
def otp_message():
    data = request.json
    recipientsEmail = data["email"]
    randomResult = random.randint(100000, 999999)
    msg = Message(subject='OTP',sender='yuyeensan@kkumail.com', recipients=[recipientsEmail])
    msg.body=str('OTP ของคุณคือ '+ str(randomResult) +' ใส่รหัสนี้เพื่อทำการเข้าสู่ระบบ รหัสมีอายุ 30 วินาที')
    mail.send(msg)
    numberJson = {
        "otp_number": randomResult
    }
    return jsonify(numberJson)

    # randomResult = random.randint(100000, 999999)
    # msg = 'OTP ของคุณคือ '+ str(randomResult) +' ใส่รหัสนี้เพื่อทำการเข้าสู่ระบบ รหัสมีอายุ 30 วินาที'
    # requests.post(url, headers=headers, data = {'message': msg})
    # numberJson = {
    #     "otp_number": randomResult
    # }
    # return jsonify(numberJson)

@app.route('/uploadImages', methods=['POST'])
@cross_origin()
def uploadImages():
    pic = request.files['pic']
    if not pic:
        return 'No pic uploaded!', 400

    filename = secure_filename(pic.filename)
    mimetype = pic.mimetype
    if not filename or not mimetype:
        return 'Bad upload!', 400

    img = Img(img=pic.read(), name=filename, mimetype=mimetype)
    db.session.add(img)
    db.session.commit()

    return render_template("index.html"), 200

@app.route('/<int:id>')
@cross_origin()
def get_img(id):
    img = Img.query.filter_by(id=id).first()
    if not img:
        return 'Img Not Found!', 404

    return Response(img.img, mimetype=img.mimetype)

@app.route('/downloadImages/<int:id>', methods=['GET','POST'])
@cross_origin()
def downloadImages(id):
    img = Img.query.filter_by(id=id).first()
    if not img:
        return render_template("index.html"), 200
    return send_file(BytesIO(img.img), attachment_filename='Photo.png', as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
@cross_origin()
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print(user)
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return render_template("index.html", email=user.email)

        return '<h1>Invalid username or password</h1>'
        

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
@cross_origin()
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return render_template("starter.html")
    return render_template('signup.html', form=form)

@app.route('/dashboard')
@cross_origin()
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)

@app.route('/logout')
@cross_origin()
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)