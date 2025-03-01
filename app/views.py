from flask import Blueprint

views = Blueprint("views", __name__)

# Example route
@views.route("/")
def home():
    return "Hello, world!"
