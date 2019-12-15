from flask import Blueprint, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from src.models import User, Token
from src import db, login_manager
from itsdangerous import URLSafeTimedSerializer
import requests
from src import app


user_blueprint = Blueprint('user_bp', __name__)


@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


@user_blueprint.route('/get_user')
@login_required
def get_user():
    user = User.query.get(current_user.id)
    return jsonify({"user": user.get_json()})


@user_blueprint.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        email = request.get_json()['email']
        firstname = request.get_json()['firstname']
        lastname = request.get_json()['lastname']
        password = request.get_json()['password']
        check_email = User.query.filter_by(email=email).first()
        if check_email:
            return jsonify({"code": 409})
        else:
            new_user = User(
                email=email,
                firstname=firstname,
                lastname=lastname
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"code": 200})


@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.get_json()['email']
        password = request.get_json()['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            token = Token()
            token = token.create_token(current_user.id)
            return jsonify({"code": 200, "user": {"id": current_user.id, "email": current_user.email}, "apiKey": token.uuid})
        return jsonify({"code": 401})


@user_blueprint.route('/logout')
@login_required
def logout():
    api_key = request.headers.get('Authorization').replace('Token ', '', 1)
    token = Token.query.filter_by(uuid=api_key).first()
    if token:
        db.session.delete(token)
        db.session.commit()
        logout_user()
        return jsonify({"code": 200})
    return jsonify({"code": 400})


def send_email(token, email, name):
    url = f"https://api.mailgun.net/v3/{app.config['EMAIL_DOMAIN']}/messages"
    response = requests.post(url,
                             auth=("api", app.config['EMAIL_API']),
                             data={"from": "Nguyen Anh Thi <shi901311@gmail.com>",
                                   "to": [email],
                                   "subject": "Reset Password",
                                   "text": f"Go to {app.config['CLIENT_URL']}/new-password/{token} to set a new password please!"})

    print(response)


@user_blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.get_json()['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            print("Email not exist!")
            return jsonify({"code": 404})
        s = URLSafeTimedSerializer(app.secret_key)
        token = s.dumps(user.email, salt="UMEO")
        name = f'{user.firstname} {user.lastname}'
        print("TOKEN:", token)
        print("EMAIL", user.email)
        send_email(token, user.email, name)
        return jsonify({"code": 200})


@user_blueprint.route('/new-password/<token>', methods=['POST'])
def new_password(token):
    print("TOKEN: ", token)
    try:
        s = URLSafeTimedSerializer(app.secret_key)
        email = s.loads(token, salt="UMEO", max_age=3000)
    except:
        print("Invalid token")
        return jsonify({"code": 404})

    print("EMAIL", email)

    if request.method == "POST":
        if request.get_json()['password'] != request.get_json()['confirm_password']:
            print('Password not match!')
            return jsonify({"code": 400})
        user = User.query.filter_by(email=email).first()
        user.set_password(request.get_json()['password'])
        db.session.commit()
        print("You have set new password", "successful")
        return jsonify({"code": 200})


@user_blueprint.route('/follow/<int:id>', methods=['POST'])
@login_required
def follow(id):
    print(current_user.id, id)
    if current_user.id != id:
        followed_user = User.query.get(id)
        current_user.follow(followed_user)
        db.session.commit()
        return jsonify({"code": 200})
    return jsonify({"code": 400})


@user_blueprint.route('/unfollow/<int:id>', methods=['POST'])
@login_required
def unfollow(id):
    followed_user = User.query.get(id)
    current_user.unfollow(followed_user)
    db.session.commit()
    return jsonify({"code": 200})


@user_blueprint.route('/profile/<id>')
@login_required
def get_profile(id):
    user = User.query.get(id)
    return jsonify({"user": user.get_json(current_user)})


@user_blueprint.route('/search/<keyword>')
@login_required
def search_user(keyword):
    print("KEYWORD", keyword)
    users = [user.get_json()
             for user in User.query.filter(User.email.like(f"%{keyword}%")).all()]
    print("USERS", users)
    return jsonify(users)
