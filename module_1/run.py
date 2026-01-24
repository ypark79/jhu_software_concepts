# Import the create_app function from main.py and call it to
# instantiate a flask object.
from main import create_app

# Instantiate a flask object by calling the create_app function.
app = create_app()

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 8080)
