# an object of WSGI application
from flask import Flask, render_template

app = Flask(__name__)

# A decorator used to tell the application
# the URL is associated function
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    # Run the application
    app.run(host = '0.0.0.0', port = 8080)
