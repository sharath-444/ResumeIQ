from flask import Flask
from io import open
import os
import sys
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    # Detect if we are running in a bundled PyInstaller environment
    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(__name__)

    # Use environment variable for secret key in production, fallback for dev
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-resumeiq-secure')
    # Detect Environment
    is_vercel = os.environ.get('VERCEL') == '1'
    is_frozen = getattr(sys, 'frozen', False)

    if is_vercel:
        # Vercel Environment (Cloud)
        # SQLite is ephemeral on Vercel, but works for the current session.
        # Uploads go to /tmp as Vercel has a read-only filesystem except for /tmp.
        app_data_path = os.getcwd() 
        app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app_data_path, "resumeiq.db")}'
        print("Running in Cloud (Vercel) mode")
    elif is_frozen:
        # Desktop Bundle Environment (.exe)
        app_data_path = os.path.join(os.path.expanduser('~'), 'Documents', 'ResumeIQ_Data')
        app.config['UPLOAD_FOLDER'] = os.path.join(app_data_path, 'uploads')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app_data_path, "resumeiq.db")}'
        print(f"Running in Desktop (Frozen) mode. Data at: {app_data_path}")
    else:
        # Standard Development Environment
        app_data_path = os.getcwd()
        app.config['UPLOAD_FOLDER'] = 'uploads'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumeiq.db'
        print("Running in Development mode")

    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Init extensions
    from models import db as models_db # Import db from models to avoid circular import issues
    models_db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    login_manager.login_view = 'auth.login'
    
    # Import Models
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register Blueprints
    from routes.auth import auth as auth_blueprint
    from routes.main import main as main_blueprint
    from routes.admin import admin as admin_blueprint
    
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint)
    
    # Create DB and Default Admin
    with app.app_context():
        models_db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed_password = bcrypt.generate_password_hash('password123').decode('utf-8')
            admin = User(username='admin', password=hashed_password, role='admin')
            models_db.session.add(admin)
            models_db.session.commit()
            print("Default Admin Created")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
