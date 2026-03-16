from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from database import init_db
from models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    init_db()

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to continue.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    # Register blueprints
    from auth import auth_bp
    from main import main_bp
    from students import students_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp)

    @app.route('/')
    def index():
        return redirect(url_for('main.dashboard'))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
