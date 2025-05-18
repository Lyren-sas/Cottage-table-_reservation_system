import base64
import io
import sqlite3
from tkinter import Image
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import OwnerCottage, User,Owner
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from . import get_db_connection
from datetime import datetime
import re


auth = Blueprint('auth', __name__)

def validate_email(email):
    """Enhanced email validation with more robust regex"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None and len(email) <= 120

def validate_password(password):
    """Password validation with complexity requirements"""
    return (
        len(password) >= 8 and 
        any(char.isupper() for char in password) and 
        any(char.islower() for char in password) and 
        any(char.isdigit() for char in password) and 
        any(not char.isalnum() for char in password)
    )

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db_connection()
        try:
           
            if not validate_email(email):
                flash('Invalid email format.', 'error')
                return render_template('home.html', user=current_user)

            user = User.get_user_by_email(conn, email)
           
            if user and check_password_hash(user.password, password):
                login_user(user, remember=True)
                
               
                flash(f'Welcome back, {user.name}!', 'success')
                
                if user.role == 'user':
                    return redirect(url_for('views.landing', role_user=user.role))
                else:
                    flash('Email or Password is incorrect', 'error')
              
            else:
                flash('Acoount does not exist, Pls Try Again', 'error')
                
        except Exception as e:
            flash(f'An error occurred during login: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()
    
    return render_template('home.html', user=current_user)

@auth.route('/owner/login', methods=['GET', 'POST'])
def loginowner():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        conn = get_db_connection()
        try:
            if not validate_email(email):
                flash('Invalid email format.', 'error')
                return render_template('owner_home.html', user=current_user)

            owner = Owner.get_owner_by_email(conn, email)
           
            if owner and check_password_hash(owner.password, password):
                login_user(owner, remember=True)
                flash(f'Welcome back, {owner.name}!', 'success')
                return redirect(url_for('dashboard.dashboard_view'))
            else:
                flash('Email or Password is incorrect', 'error')
                
        except Exception as e:
            flash(f'An error occurred during login: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()
    
    return render_template('owner_home.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    if current_user.role == 'user':
        logout_user()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('views.landing'))
    elif current_user.role == 'owner':
        logout_user()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('owner_views.ownerlanding'))
    

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        name = request.form.get('name', '').strip()
        password1 = request.form.get('password1', '')
        password2 = request.form.get('password2', '')
        security_question = request.form.get('security_question', '').strip()
        security_answer = request.form.get('security_answer', '').strip()
        
        conn = get_db_connection()
        try:
            # Store form data for repopulation
            form_data = {
                'email': email,
                'username': username,
                'name': name,
                'security_question': security_question,
                'security_answer': security_answer
            }
            
            # Comprehensive validation
            if not validate_email(email):
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Invalid email format.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            
            if not validate_password(password1):
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            
            user_email = User.get_user_by_email(conn, email)
            user_name = User.get_user_by_username(conn, username)
            
            if user_email:
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Email already exists.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif user_name:
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Username already exists.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif len(email) < 4:
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Email must be greater than 3 characters.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif len(username) < 2:
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Username must be greater than 1 character.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif len(name) < 2:
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Name must be greater than 1 character.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif password1 != password2:
                return render_template('home.html', 
                                    user=current_user,
                                    signup_error='Passwords don\'t match.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            else:
                # Create user
                new_user = User(
                    email=email,
                    username=username,
                    name=name,
                    password=generate_password_hash(password1, method='pbkdf2:sha256'),
                    date_created=datetime.utcnow(),
                    role="user",
                    security_question=security_question,
                    security_answer=security_answer
                )
                user_id = new_user.save_to_db(conn)
                
                # Login after signup
                login_user(new_user, remember=True)
                flash(f'Welcome to Norzagaray Cottage Reservation, {new_user.name}!', 'success')
                return redirect(url_for('views.landing'))
        except Exception as e:
            return render_template('home.html', 
                                user=current_user,
                                signup_error=str(e),
                                signup_data=form_data,
                                show_signup_modal=True)
        finally:
            if conn:
                conn.close()
    
    return render_template('home.html', user=current_user)

@auth.route('/owner/signup', methods=['GET', 'POST'])
def owner_signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        name = request.form.get('name', '').strip()
        password1 = request.form.get('password1', '')
        password2 = request.form.get('password2', '')
        security_question = request.form.get('security_question', '').strip()
        security_answer = request.form.get('security_answer', '').strip()
        
        conn = get_db_connection()
        try:
            # Store form data for repopulation
            form_data = {
                'email': email,
                'username': username,
                'name': name,
                'security_question': security_question,
                'security_answer': security_answer
            }
            
            # Comprehensive validation
            if not validate_email(email):
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Invalid email format.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            
            if not validate_password(password1):
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            
            owner_email = Owner.get_owner_by_email(conn, email)
            owner_name = Owner.get_owner_by_username(conn, username)
            
            if owner_email:
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Email already exists.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif owner_name:
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Username already exists.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif len(email) < 4:
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Email must be greater than 3 characters.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif len(username) < 2:
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Username must be greater than 1 character.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif len(name) < 2:
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Name must be greater than 1 character.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            elif password1 != password2:
                return render_template('owner_home.html', 
                                    user=current_user,
                                    signup_error='Passwords don\'t match.',
                                    signup_data=form_data,
                                    show_signup_modal=True)
            else:
                # Create owner
                new_owner = Owner(
                    email=email,
                    username=username,
                    name=name,
                    password=generate_password_hash(password1, method='pbkdf2:sha256'),
                    date_created=datetime.utcnow(),
                    role="owner",
                    security_question=security_question,
                    security_answer=security_answer
                )
                user_id = new_owner.save_to_db(conn)
                
                # Login after signup
                login_user(new_owner, remember=True)
                flash(f'Welcome to Norzagaray Cottage Reservation, {new_owner.name}!', 'success')
                return redirect(url_for('owner_views.ownerlanding'))
        except Exception as e:
            return render_template('owner_home.html', 
                                user=current_user,
                                signup_error=str(e),
                                signup_data=form_data,
                                show_signup_modal=True)
        finally:
            if conn:
                conn.close()
    
    return render_template('owner_home.html', user=current_user)

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get current user data
    current_user_db = User.get_user_by_id(conn, current_user.id)

    # Handle POST requests
    if request.method == 'POST':
        if 'submit_profile' in request.form:
            # Update profile
            name = request.form.get('name')
            phone = request.form.get('phone')

            # Handle profile image upload
            profile_image = current_user_db.user_image
            if 'profile_image' in request.files and request.files['profile_image'].filename:
                file = request.files['profile_image']
                if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
                    encoded_image = base64.b64encode(file.read()).decode('utf-8')
                    profile_image = encoded_image

            # Update user fields
            current_user_db.name = name
            current_user_db.phone = phone
            current_user_db.user_image = profile_image

            # Save to DB
            current_user_db.update_in_db(conn)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))

        elif 'change_password' in request.form and current_user_db.role == 'user':
            # Change password
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not check_password_hash(current_user_db.password, current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('auth.profile'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('auth.profile'))

            if not validate_password(new_password):
                flash('Password must be at least 8 characters long with uppercase, lowercase, number, and special character.', 'error')
                return redirect(url_for('auth.profile'))

            hashed_password = generate_password_hash(new_password)
            current_user_db.password = hashed_password
            current_user_db.update_in_db(conn)
            flash('Password updated successfully!', 'success')
            return redirect(url_for('auth.profile'))

        elif 'submit_qr' in request.form and current_user_db.role == 'owner':
            # QR Code Upload for Cottage
            cottage_id = request.form.get('cottage_id')

            cursor.execute('SELECT id FROM owner_cottages WHERE id = ? AND user_id = ?', (cottage_id, current_user_db.id))
            cottage = cursor.fetchone()

            if not cottage:
                flash('You do not have permission to update this cottage.', 'error')
                return redirect(url_for('auth.profile'))

            if 'qr_code' in request.files and request.files['qr_code'].filename:
                file = request.files['qr_code']
                if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png'}):
                    # Optional file size limit (2MB)
                    file_content = file.read()
                    if len(file_content) > 2 * 1024 * 1024:
                        flash('File is too large. Maximum 2MB allowed.', 'error')
                        return redirect(url_for('auth.profile'))

                    encoded_qr = base64.b64encode(file_content).decode('utf-8')

                    cursor.execute('UPDATE owner_cottages SET payment_qr_code = ? WHERE id = ?', (encoded_qr, cottage_id))
                    conn.commit()
                    flash('QR code updated successfully!', 'success')
                    return redirect(url_for('auth.profile'))
                else:
                    flash('Invalid file format. Please upload JPG, JPEG, or PNG.', 'error')
            else:
                flash('Please select a file to upload.', 'error')

    # For GET requests
    owner_cottages = None
    if current_user_db.role == 'owner':
        cursor.execute('''
            SELECT id, cottage_no, payment_qr_code 
            FROM owner_cottages 
            WHERE user_id = ?
        ''', (current_user_db.id,))
        owner_cottages = cursor.fetchall()

    # Profile image setup
    profile_image = current_user_db.user_image if current_user_db.user_image else None

    cursor.close()
    conn.close()

    return render_template('profile.html',
                           user=current_user_db,
                           profile_image=profile_image,
                           owner_cottages=owner_cottages)

# Helper function to check file type
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions




def validate_password(password):
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    return has_upper and has_lower and has_digit and has_special

@auth.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    question = request.form.get('security_question')
    answer = request.form.get('security_answer')
    new_password = request.form.get('new_password')
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    if not user:
        flash('No user found with that email.', 'danger')
        return redirect(url_for('index'))
    # Map code to question text
    question_map = {
        'mother_maiden': "What is your mother's maiden name?",
        'first_pet': "What was your first pet's name?",
        'birth_city': "In what city were you born?",
        'favorite_teacher': "Who was your favorite teacher?"
    }
    db_question = question_map.get(user['security_question'], user['security_question'])
    if db_question != question or user['security_answer'].lower() != answer.strip().lower():
        flash('Security question or answer is incorrect.', 'danger')
        return redirect(url_for('index'))
    hashed_pw = generate_password_hash(new_password)
    conn.execute('UPDATE users SET user_pass = ? WHERE id = ?', (hashed_pw, user['id']))
    conn.commit()
    flash('Password reset successful. You can now log in.', 'success')
    return redirect(url_for('views.landing'))

@auth.route('/owner/forgot_password', methods=['POST'])
def owner_forgot_password():
    email = request.form.get('email')
    question = request.form.get('security_question')
    answer = request.form.get('security_answer')
    new_password = request.form.get('new_password')
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM owners WHERE email = ?', (email,))
    owner = cursor.fetchone()
    if not owner:
        flash('No owner found with that email.', 'danger')
        return redirect(url_for('owner.owner_login'))
    if owner['security_question'] != question or owner['security_answer'].lower() != answer.strip().lower():
        flash('Security question or answer is incorrect.', 'danger')
        return redirect(url_for('owner.owner_login'))
    hashed_pw = generate_password_hash(new_password)
    conn.execute('UPDATE owners SET password = ? WHERE id = ?', (hashed_pw, owner['id']))
    conn.commit()
    flash('Password reset successful. You can now log in.', 'success')
    return redirect(url_for('owner.owner_login'))

@auth.route('/get_security_question')
def get_security_question():
    email = request.args.get('email', '').strip()
    conn = get_db_connection()
    cursor = conn.execute('SELECT security_question FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    if not user or not user['security_question']:
        return jsonify({'success': False, 'message': 'No security question found for this email.'})
    # Map code to question text
    question_map = {
        'mother_maiden': "What is your mother's maiden name?",
        'first_pet': "What was your first pet's name?",
        'birth_city': "In what city were you born?",
        'favorite_teacher': "Who was your favorite teacher?"
    }
    question_code = user['security_question']
    question_text = question_map.get(question_code, question_code)
    return jsonify({'success': True, 'question': question_text})

@auth.route('/owner/get_security_question')
def owner_get_security_question():
    email = request.args.get('email', '').strip()
    conn = get_db_connection()
    cursor = conn.execute('SELECT security_question FROM owners WHERE email = ?', (email,))
    owner = cursor.fetchone()
    conn.close()
    if not owner or not owner['security_question']:
        return jsonify({'success': False, 'message': 'No security question found for this email.'})
    # Map code to question text
    question_map = {
        'mother_maiden': "What is your mother's maiden name?",
        'first_pet': "What was your first pet's name?",
        'birth_city': "In what city were you born?",
        'favorite_teacher': "Who was your favorite teacher?"
    }
    question_code = owner['security_question']
    question_text = question_map.get(question_code, question_code)
    return jsonify({'success': True, 'question': question_text})
