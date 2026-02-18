from flask import Flask
from io import open
import os
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'dev-secret-key-resumeiq-secure' # Fixed key for development
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resumeiq.db'
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

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False)
