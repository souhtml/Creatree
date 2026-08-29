import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# App & config
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
db_url = os.environ.get("DATABASE_URL", "sqlite:///creatree.db")
# Some Postgres hosts (Neon, Supabase, Render) hand out "postgres://" URLs,
# but SQLAlchemy 2.x requires the "postgresql://" scheme.
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Log in to keep growing your tree."
login_manager.login_message_category = "info"

RESERVED_USERNAMES = {"signup", "login", "logout", "dashboard", "static", "admin", "profile"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(200), default="")
    avatar_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    links = db.relationship(
        "Link", backref="owner", cascade="all, delete-orphan",
        order_by="Link.position"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(60), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    position = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None
        if not username or not username.isalnum():
            error = "Usernames can only contain letters and numbers."
        elif username in RESERVED_USERNAMES:
            error = "That username is reserved. Try another."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif User.query.filter_by(username=username).first():
            error = "That username is already taken."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "error")
            return render_template("signup.html", username=username, email=email)

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Welcome to Creatree! Let's plant your first links.", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Those details don't match an account.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/profile/<username>")
def profile(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    return render_template("profile.html", user=user)


@app.route("/l/<int:link_id>")
def follow_link(link_id):
    link = Link.query.get_or_404(link_id)
    link.clicks += 1
    db.session.commit()
    return redirect(link.url)


# ---------------------------------------------------------------------------
# Dashboard (auth required)
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@app.route("/dashboard/profile", methods=["POST"])
@login_required
def update_profile():
    current_user.bio = request.form.get("bio", "")[:200]
    current_user.avatar_url = request.form.get("avatar_url", "")[:500]
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/links/add", methods=["POST"])
@login_required
def add_link():
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()

    if not title or not url:
        flash("Every link needs a title and a URL.", "error")
        return redirect(url_for("dashboard"))

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    max_pos = db.session.query(db.func.max(Link.position)).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    link = Link(user_id=current_user.id, title=title, url=url, position=max_pos + 1)
    db.session.add(link)
    db.session.commit()
    flash("Link added.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/links/<int:link_id>/delete", methods=["POST"])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        abort(403)
    db.session.delete(link)
    db.session.commit()
    flash("Link removed.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/links/reorder", methods=["POST"])
@login_required
def reorder_links():
    order = request.form.getlist("order[]")
    for index, link_id in enumerate(order):
        link = Link.query.get(int(link_id))
        if link and link.user_id == current_user.id:
            link.position = index
    db.session.commit()
    return ("", 204)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def create_tables():
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
else:
    # On Vercel there's no long-running process to run create_tables() once
    # up front, so make sure the tables exist on cold start too.
    # create_all() is safe to call repeatedly — it skips tables that exist.
    try:
        create_tables()
    except Exception:
        pass
