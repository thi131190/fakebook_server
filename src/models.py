from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import LoginManager, UserMixin, current_user
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request
import uuid

db = SQLAlchemy()


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer,
                               db.ForeignKey('users.id')),
                     db.Column('followed_id', db.Integer,
                               db.ForeignKey('users.id'))
                     )


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True)
    firstname = db.Column(db.String(256))
    lastname = db.Column(db.String(256))
    password = db.Column(db.String(256))
    avatar = db.Column(db.String(256))
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_like(self, post):
        return post in self.like_posts

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(or_(followers.c.follower_id == self.id, Post.user_id == self.id)
                                                                         ).order_by(Post.created_at.desc())

    def get_json(self, user=None):
        return {
            "id": self.id,
            "email": self.email,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "avatar": self.avatar,
            "isFollowing": False if not user else user.is_following(self)
        }


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)

    def create_token(self, current_user_id):
        token = Token(user_id=current_user_id, uuid=str(uuid.uuid4().hex))
        db.session.add(token)
        db.session.commit()
        return token


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def get_json(self):
        return {
            "id": self.id,
            "body": self.body,
            "author": User.query.get(self.user_id).get_json(),
            "isLiked": bool(Like.query.filter_by(user_id=current_user.id, post_id=self.id).first()),
            "likeCount": Like.query.filter_by(post_id=self.id).count(),
            "commentCount": Comment.query.filter_by(post_id=self.id).count(),
            "created_at": self.created_at.strftime("%d-%b-%Y"),
        }


class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    post_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def get_json(self):
        return {
            "id": self.id,
            "body": self.body,
            "commenter": User.query.get(self.user_id).get_json(),
            "post": Post.query.get(self.post_id).get_json(),
            "created_at": self.created_at.strftime("%d-%b-%Y"),
        }


# setup login manager
login_manager = LoginManager()
login_manager.login_view = "google.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Token ', '', 1)
        token = Token.query.filter_by(uuid=api_key).first()
        if token:
            return token.user
    return None
