# an object of WSGI application
from flask import Flask

app = Flask(__name__)

# A decorator used to tell the application
# the URL is associated function
@app.route('/')

# A function displaying text as our "hello world base"
def hello():
    return "Welcome to Modern Software Concepts in Python!"

if __name__ == '__main__':
    # Run the application
    app.run(host = '0.0.0.0', port = 8080)
