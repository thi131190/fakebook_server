from flask import Blueprint, request, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from src.models import User, Token, Post, Like, Comment
from src import db, login_manager
from itsdangerous import URLSafeTimedSerializer
import requests
from src import app


post_blueprint = Blueprint('post_bp', __name__)


@post_blueprint.route('/')
# @login_required
def get_all_posts():
    # posts = [post.get_json() for post in current_user.followed_posts()]
    posts = [post.get_json() for post in Post.query.all()]
    return jsonify(posts)


@post_blueprint.route('/', methods=['POST'])
@login_required
def create_new_post():
    if request.method == 'POST':
        new_post = Post(
            body=request.get_json()['body'],
            post_img=request.get_json()['image_url'],
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
    return jsonify({"code": 200})


@post_blueprint.route('/<id>')
@login_required
def get_post_by_id(id):
    post = Post.query.get(int(id))
    return jsonify(post.get_json())


@post_blueprint.route('/<id>', methods=['DELETE'])
@login_required
def delete_post(id):
    if request.method == "DELETE":
        post = Post.query.filter_by(id=id).first()
        if post:
            comments = Comment.query.filter_by(post_id=id).all()
            for comment in comments:
                db.session.delete(comment)

            likes = Like.query.filter_by(post_id=id).all()
            for like in likes:
                db.session.delete(like)

            db.session.commit()
            db.session.delete(post)
            db.session.commit()
            return jsonify({"code": 200})
        return jsonify({"code": 404})


@post_blueprint.route('/<id>/like', methods=['POST'])
@login_required
def like(id):
    is_liked = Like.query.filter_by(
        user_id=current_user.id, post_id=id).first()
    if not is_liked:
        like = Like(user_id=current_user.id, post_id=id)
        db.session.add(like)
        db.session.commit()
        return jsonify({"code": 200, "status": True})
    db.session.delete(is_liked)
    db.session.commit()
    return jsonify({"code": 200, "status": False})


@post_blueprint.route('/<id>', methods=['PUT'])
def update_post(id):
    if request.method == 'PUT':
        post = Post.query.get(id)
        if post:
            post.body = request.get_json()['body']
            post.post_img = request.get_json()['image_url']
            db.session.commit()
            return jsonify({"code": 200})
        return jsonify({"code": 404})


@post_blueprint.route('/<id>/comments', methods=['POST'])
def create_comment(id):
    comment = Comment(
        user_id=current_user.id,
        post_id=id,
        body=request.get_json()['body']
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify({"code": 200})


@post_blueprint.route('/<id>/comments/', methods=['GET'])
def get_all_comments_of_post_id(id):
    comments = [comment.get_json()
                for comment in Comment.query.filter_by(post_id=id).all()]
    return jsonify(comments)
