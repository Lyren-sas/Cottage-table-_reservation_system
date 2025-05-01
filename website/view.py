import base64
from datetime import datetime
import io
import os
from flask import Blueprint, current_app, render_template, flash, redirect, send_file, url_for, request, session, jsonify
from flask_login import login_required, current_user
from . import get_db_connection
from .models import Notification, Reservation, OwnerCottage, Amenity, CottageAmenity
from typing import List
from datetime import datetime, timedelta


views = Blueprint('views', __name__)

@views.route('/')
def landing():
    """Landing page with featured cottages"""
    conn = get_db_connection()
    featured_cottages = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM owner_cottages LIMIT 6')  
        cottage_rows = cursor.fetchall()
        
        featured_cottages = [OwnerCottage(
            id=row['id'],
            user_id=row['user_id'],
            owner_name=row['owner_name'],
            cottage_no=row['cottage_no'],
            flag_color=row['flag_color'],
            cottage_image=row['cottage_image'],
            cottage_location=row['cottage_location'],
            cottage_description=row['cottage_description']
        ) for row in cottage_rows]
        
    except Exception as e:
        flash(f'Error fetching cottages: {str(e)}', 'error')    
        
    finally:
        if conn:
            conn.close()
    
    return render_template(
        'home.html', 
        user=current_user, 
        featured_cottages=featured_cottages, 
        role=current_user.role if current_user.is_authenticated else None
    )

@views.route('/owneraccount')
def ownerlanding():
    """Landing page with featured cottages"""
    conn = get_db_connection()
    featured_cottages = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM owner_cottages LIMIT 6')  
        cottage_rows = cursor.fetchall()
        
        featured_cottages = [OwnerCottage(
            id=row['id'],
            user_id=row['user_id'],
            owner_name=row['owner_name'],
            cottage_no=row['cottage_no'],
            flag_color=row['flag_color'],
            cottage_image=row['cottage_image'],
            cottage_location=row['cottage_location'],
            cottage_description=row['cottage_description']
        ) for row in cottage_rows]
        
    except Exception as e:
        flash(f'Error fetching cottages: {str(e)}', 'error')    
        
    finally:
        if conn:
            conn.close()
    
    return render_template(
        'owner_home.html', 
        user=current_user, 
        featured_cottages=featured_cottages, 
        role=current_user.role if current_user.is_authenticated else None
    )

@views.route('/user-notifications')
@login_required
def user_notifications():
    """Display all notifications for the current user"""
    conn = get_db_connection()
    try:
        
        notifications = Notification.get_user_notifications(conn, current_user.id)
        
        # Format timestamps for display
        for notification in notifications:
            
            if isinstance(notification.created_at, str):
                notification.created_at = datetime.strptime(notification.created_at, '%Y-%m-%d %H:%M:%S')
            
            
            notification.created_at = notification.created_at.strftime('%b %d, %Y at %I:%M %p')
            
            
            notification.is_read = notification.read
            
    except Exception as e:
        flash(f'Error fetching notifications: {str(e)}', 'error')
        notifications = []
    finally:
        conn.close()
    
    return render_template('notifications.html', notifications=notifications, user=current_user)

from flask import Blueprint, request, jsonify
import sqlite3
from datetime import datetime

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/api/payments', methods=['POST'])
def submit_payment():
    try:
        data = request.get_json()
        reservation_id = data['reservation_id']
        reference_number = data['reference_number']
        amount = data['amount']
        payment_method = data['payment_method']
        payment_date = data['payment_date']
        status = data['status']

        # Connect to the SQLite database
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Insert payment into payment table
        cursor.execute('''
            INSERT INTO payments (
                reservation_id, user_id, amount, payment_method,
                payment_status, transaction_id, payment_date, notes,
                receipt_number, payment_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reservation_id, data['user_id'], amount, payment_method,
            status, data['transaction_id'], payment_date, data.get('notes'),
            data.get('receipt_number'), data.get('payment_details')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True}), 200

    except Exception as e:
        print("Error submitting payment:", e)
        return jsonify({'success': False, 'message': str(e)}), 500



@views.route('/user_image/<int:user_id>')
def user_image(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_image FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row['user_image']:
            try:
                # First, try to decode as base64
                image_data = base64.b64decode(row['user_image'])
                return send_file(
                    io.BytesIO(image_data),
                    mimetype='image/jpeg',  # Consider using MIME type detection
                    max_age=3600  # Add cache control for better performance
                )
            except Exception as e:
                current_app.logger.info(f"Base64 decode failed, treating as binary: {str(e)}")
                # If already binary, serve directly
                return send_file(
                    io.BytesIO(row['user_image']),
                    mimetype='image/jpeg',
                    max_age=3600
                )
        else:
            # Serve a default image
            default_image_path = os.path.join(current_app.root_path, 'static', 'default_profile.png')
            return send_file(default_image_path, mimetype='image/png', max_age=3600)
            
    except Exception as e:
        current_app.logger.error(f"Error serving user image: {str(e)}")
        # Always return something - fallback to default image
        default_image_path = os.path.join(current_app.root_path, 'static', 'default_profile.png')
        return send_file(default_image_path, mimetype='image/png', max_age=3600)
