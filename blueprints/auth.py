from flask import session, Blueprint, render_template, request, jsonify, redirect, url_for, flash
from blueprints.forms import RegisterForm, LoginForm
from databaseModel import UserModel
from exts import db
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("index1.html", message=None)
    else:
        form = LoginForm(request.form)
        if form.validate():
            username = form.username.data
            password = form.password.data
            user = UserModel.query.filter_by(username=username).first()
            if not user:
                return render_template("index1.html", message="The user does not exist, please try again.")
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for("qa.index"))
            else:
                return render_template("index1.html", message="Password error, please try again.")
        else:
            errors = [f"{field}: {error}" for field, errors in form.errors.items() for error in errors]
            return render_template("index1.html", message=" ".join(errors))

@bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html", message=None)
    else:
        form = RegisterForm(request.form)
        if form.validate():
            email = form.email.data
            username = form.username.data
            password = form.password.data
            user = UserModel(
                email=email,
                username=username,
                password=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            return render_template("index1.html", message="Registration successful, please log in.")
        else:
            return render_template("register.html", message="Registration failed, please check input.")

