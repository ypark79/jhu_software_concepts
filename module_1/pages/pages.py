# The function of pages.py is to house the blueprint that will serve
# as the foundation of the web application infrastructure. It will
# also house all of the routes to the html/webpages.
from flask import Blueprint, render_template

bp = Blueprint('pages', __name__, template_folder='templates')

# Route the 3 webpages required by the assignment and establish
# functions that render the html files inside the templates folder.
@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/projects')
def projects():
    return render_template('projects.html')
