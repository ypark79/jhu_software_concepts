from flask import Flask
from pages.routes import pages_bp

app = Flask(__name__)

app.register_blueprint(pages_bp)
