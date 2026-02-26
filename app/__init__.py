from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
import os
from dotenv import load_dotenv

load_dotenv()

mongo = PyMongo()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['MONGO_URI'] = os.environ.get('MONGO_URI', 'mongodb://robin:123456789@baonamdts.com:22112/thuyvan_db')
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'warning'
    
    # User loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.views import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    return app
