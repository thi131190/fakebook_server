from flask import Flask, redirect, url_for, flash, render_template
from flask_login import login_required, logout_user
from .config import Config
from .models import db, login_manager
from .controllers.oauth import blueprint
# from .controllers.user import user_blueprint
# from .controllers.post import post_blueprint
from .cli import create_db
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)
CORS(app)


from .controllers.user import user_blueprint
app.register_blueprint(user_blueprint, url_prefix='/user')

from .controllers.post import post_blueprint
app.register_blueprint(post_blueprint, url_prefix='/posts')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out")
    return redirect(url_for("index"))


@app.route("/")
def index():
    return render_template("home.html")
