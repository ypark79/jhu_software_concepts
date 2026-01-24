# Import the blueprint object from pages.py in order to register the
# blueprint in main.py.
from flask import Flask
from pages.pages import bp

# Establish the create_app function to instantiate a flask object. This
# will be imported in run.py, which starts up the web application.
def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
