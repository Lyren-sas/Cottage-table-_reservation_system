import base64
from datetime import datetime
from getpass import getuser
import io
import os
from tkinter import Image
from flask import Blueprint, current_app, render_template, flash, redirect, send_file, url_for, request, session, jsonify
from flask_login import login_required, current_user
from sympy import ImageSet
from . import get_db_connection
from .models import Notification, Reservation, OwnerCottage, Amenity, CottageAmenity
from typing import List
from datetime import datetime, timedelta
from PIL import Image, ImageDraw


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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_image, name FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['user_image']:
        # Check if the image is stored as base64
        try:
            image_data = base64.b64decode(row['user_image'])
            return send_file(
                io.BytesIO(image_data),
                mimetype='image/png'
            )
        except Exception as e:
            # If already binary or another error occurs
            return send_file(
                io.BytesIO(row['user_image']), 
                mimetype='image/png'
            )
    else:
        # Generate an image with the first letter of the user's name
        if row and row['name']:
            first_letter = row['name'][0].upper()
            
            # Create a colored background with the first letter
            image = Image.new('RGB', (200, 200), color=(73, 109, 137))  # A nice blue-gray color
            
            try:
                # Try to load the font, with fallback options
                try:
                    font = ImageSet.truetype('DejaVuSans-Bold.ttf', 120)
                except IOError:
                    try:
                        font = ImageSet.truetype('Arial.ttf', 120)
                    except IOError:
                        # Use default font as last resort
                        font = ImageSet.load_default()
                
                draw = ImageDraw.Draw(image)
                
                # Calculate text size to center it
                text_width, text_height = draw.textsize(first_letter, font=font)
                position = ((200 - text_width) // 2, (200 - text_height) // 2 - 10)
                
                # Draw the letter in white
                draw.text(position, first_letter, font=font, fill=(255, 255, 255))
                
                img_io = io.BytesIO()
                image.save(img_io, 'PNG')
                img_io.seek(0)
                return send_file(img_io, mimetype='image/png')
            
            except Exception as e:
                print(f"Error generating letter image: {e}")
                return send_file('static/profile.png', mimetype='image/png')
        else:
            # Default image if we can't get the user's name
            return send_file('static/profile.png', mimetype='image/png')
