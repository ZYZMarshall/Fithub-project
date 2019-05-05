###########################
# Run the main Flask app. #
###########################
from fithub import create_app

# Run the Flask application.
app = create_app()

if __name__ == '__main__':
    app.run(debug = True)
    