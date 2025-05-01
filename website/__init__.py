import os
from flask import Flask
from flask_login import LoginManager
import sqlite3
from .models import User

def get_db_connection():
    """Consistent database connection method"""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)  
    app.config['UPLOAD_FOLDER'] = 'uploads' 
    
  
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    
    from .view import views
    from .auth import auth
    from .my_cottages import cottages
    from .reservation import reservation_bp
    from .make_reservations import make_reservation_bp
    from .my_reservation import my_reservation
    from .notifications import notifications_bp
    from .discovery import discoveries
    from .dashboard import dashboard
    from .owner_notification import owner_bp
    from .payment import payment_bp
    from .rating import ratings
    
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(cottages, url_prefix='/')
    app.register_blueprint(my_reservation, url_prefix='/')
    app.register_blueprint(make_reservation_bp, url_prefix='/')
    app.register_blueprint(reservation_bp, url_prefix='/')
    app.register_blueprint(notifications_bp, url_prefix='/')
    app.register_blueprint(discoveries, url_prefix='/')
    app.register_blueprint(dashboard, url_prefix='/')
    app.register_blueprint(owner_bp, url_prefix='/')
    app.register_blueprint(payment_bp, url_prefix='/')
    app.register_blueprint(ratings, url_prefix='/')


    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        
        try:
            conn = get_db_connection()
            user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            conn.close()
            
            if user_data:
                return User(
                    id=user_data['id'], 
                    email=user_data['email'], 
                    username=user_data['username'], 
                    password=user_data['user_pass'],
                    name=user_data['name'],
                    role=user_data['role'],
                    user_image=user_data['user_image']
                )
        except sqlite3.Error:
           
            return None
        return None

    return app

def create_app_1():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)  
    app.config['UPLOAD_FOLDER'] = 'uploads' 
    
  
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    
    from .view_owner import view_owner
    from .auth import auth
    from .my_cottages import cottages
    from .reservation import reservation_bp
    from .make_reservations import make_reservation_bp
    from .my_reservation import my_reservation
    from .notifications import notifications_bp
    from .discovery import discoveries
    from .dashboard import dashboard
    from .owner_notification import owner_bp
    from .view import payment_bp
    from .rating import ratings

    app.register_blueprint(view_owner, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(cottages, url_prefix='/')
    app.register_blueprint(my_reservation, url_prefix='/')
    app.register_blueprint(make_reservation_bp, url_prefix='/')
    app.register_blueprint(reservation_bp, url_prefix='/')
    app.register_blueprint(notifications_bp, url_prefix='/')
    app.register_blueprint(discoveries, url_prefix='/')
    app.register_blueprint(dashboard, url_prefix='/')
    app.register_blueprint(owner_bp, url_prefix='/')
    app.register_blueprint(payment_bp, url_prefix='/')
    app.register_blueprint(ratings, url_prefix='/')
    

    login_manager = LoginManager()
    login_manager.login_view = 'auth.loginowner'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        
        try:
            conn = get_db_connection()
            user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            conn.close()
            
            if user_data:
                return User(
                    id=user_data['id'], 
                    email=user_data['email'], 
                    username=user_data['username'], 
                    password=user_data['user_pass'],
                    name=user_data['name'],
                    role=user_data['role'],
                    user_image=user_data['user_image']
                )
        except sqlite3.Error:
           
            return None
        return None

    return app
