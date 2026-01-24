from flask import Blueprint, render_template

bp = Blueprint('pages', __name__, template_folder='templates')

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/projects')
def projects():
    return render_template('projects.html')
