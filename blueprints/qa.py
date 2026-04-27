from flask import Blueprint, render_template, request, redirect, url_for, g,session,current_app,flash
from databaseModel import UserModel
from werkzeug.utils import secure_filename
import os

bp = Blueprint("qa", __name__, url_prefix="/")
bp.config = {'UPLOAD_FOLDER': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'src')}
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def save_image(image):
    if image:
        image_filename = secure_filename(image.filename)
        image.save(os.path.join(bp.config['UPLOAD_FOLDER'], image_filename))
        return image_filename
    return None

@bp.before_request
def my_before_request():
    user_id = session.get("user_id")
    if user_id:
        user = UserModel.query.get(user_id)
        setattr(g, "user", user)
    else:
        setattr(g, "user", None)

@bp.context_processor
def my_context_processor():
    return {"user": g.user}


# 修改后的 index 视图
@bp.route("/", methods=['POST', 'GET'])
def index():
    if g.user is None:  # 如果用户未登录，重定向到登录页面
        return redirect(url_for('auth.login'))
    else:  # 如果用户已登录，显示主页
        return render_template("homepage.html", author=g.user)