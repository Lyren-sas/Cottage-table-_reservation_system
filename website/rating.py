# Create a new file called ratings.py in your project directory
import sqlite3
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from datetime import datetime

from .models import get_db_connection

ratings = Blueprint('ratings', __name__)

@ratings.route('/submit-rating', methods=['POST'])
@login_required
def submit_rating():
    """Process and store user ratings for completed reservations"""
    reservation_id = request.form.get('reservation_id')
    rating_value = request.form.get('rating_value')
    comments = request.form.get('comments', '')
    
    if not reservation_id or not rating_value:
        flash('Rating information incomplete.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    try:
        reservation_id = int(reservation_id)
        rating_value = int(rating_value)
    except ValueError:
        flash('Invalid rating data.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    # Validate rating range
    if rating_value < 1 or rating_value > 5:
        flash('Rating must be between 1 and 5 stars.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check if reservation exists and belongs to the current user
        cursor.execute('''
            SELECT r.id, r.cottage_id, c.cottage_no, c.user_id as owner_id
            FROM reservations r
            JOIN owner_cottages c ON r.cottage_id = c.id
            WHERE r.id = ? AND r.user_id = ? AND r.cottage_status = 'completed'
        ''', (reservation_id, current_user.id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            flash('Reservation not found or cannot be rated at this time.', 'error')
            return redirect(url_for('my_reservation.my_reservations'))
        
        # Check if rating already exists
        cursor.execute('''
            SELECT id FROM ratings
            WHERE reservation_id = ? AND user_id = ?
        ''', (reservation_id, current_user.id))
        
        existing_rating = cursor.fetchone()
        
        if existing_rating:
            # Update existing rating
            cursor.execute('''
                UPDATE ratings
                SET rating_value = ?, comments = ?, updated_at = ?
                WHERE reservation_id = ? AND user_id = ?
            ''', (rating_value, comments, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                 reservation_id, current_user.id))
            
            flash('Your rating has been updated successfully.', 'success')
        else:
            # Create new rating
            cursor.execute('''
                INSERT INTO ratings (
                    reservation_id, user_id, cottage_id, owner_id, rating_value, 
                    comments, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reservation_id, current_user.id, reservation['cottage_id'], 
                reservation['owner_id'], rating_value, comments,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            flash('Thank you! Your rating has been submitted successfully.', 'success')
        
        conn.commit()
        
        # Update the reservation to mark it as rated
        cursor.execute('''
            UPDATE reservations
            SET has_rating = 1
            WHERE id = ?
        ''', (reservation_id,))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        flash(f'Error submitting rating: {str(e)}', 'error')
    
    finally:
        if conn:
            conn.close()
    
    return redirect(url_for('my_reservation.my_reservations'))

@ratings.route('/my-ratings')
@login_required
def my_ratings():
    """Display all ratings submitted by the current user"""
    conn = get_db_connection()
    ratings_list = []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, c.cottage_no, c.owner_name, res.date_stay
            FROM ratings r
            JOIN owner_cottages c ON r.cottage_id = c.id
            JOIN reservations res ON r.reservation_id = res.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        ''', (current_user.id,))
        
        ratings_list = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error retrieving ratings: {str(e)}', 'error')
    
    finally:
        if conn:
            conn.close()
    
    return render_template('my_rating.html', ratings=ratings_list)