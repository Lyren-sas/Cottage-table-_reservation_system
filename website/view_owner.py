import base64
from datetime import datetime
import io
from flask import Blueprint, render_template, flash, redirect, send_file, url_for, request, session, jsonify
from flask_login import login_required, current_user
from . import get_db_connection
from .models import Notification, Reservation, OwnerCottage, Amenity, CottageAmenity
from typing import List
from datetime import datetime, timedelta


view_owner = Blueprint('owner_views', __name__)

@view_owner.route('/')
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

@view_owner.route('/user-notifications')
@login_required
def user_notifications():
    """Display all notifications for the current user"""
    conn = get_db_connection()
    try:
        
        notifications = Notification.get_user_notifications(conn, current_user.id)
        
        # Format timestamps for display
        for notification in notifications:
            # Check if created_at is a string and parse it if needed
            if isinstance(notification.created_at, str):
                notification.created_at = datetime.strptime(notification.created_at, '%Y-%m-%d %H:%M:%S')
            
            # Format the datetime for display
            notification.created_at = notification.created_at.strftime('%b %d, %Y at %I:%M %p')
            
            # Add is_read attribute for template compatibility
            notification.is_read = notification.read
            
    except Exception as e:
        flash(f'Error fetching notifications: {str(e)}', 'error')
        notifications = []
    finally:
        conn.close()
    
    return render_template('notifications.html', notifications=notifications, user=current_user)


@view_owner.route('/user_image/<int:user_id>')
def user_image(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_image FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['user_image']:
        # Check if the image is stored as base64
        try:
            # Decode base64 image
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
        # Serve a default image if user has no image
        return send_file('static/default_profile.png', mimetype='image/png')
