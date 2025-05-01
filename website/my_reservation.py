import json
import sqlite3
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from .models import get_db_connection
from .models import Reservation


my_reservation = Blueprint('my_reservation', __name__)
scheduler = BackgroundScheduler()

@my_reservation.route('/my-reservations')
@login_required
def my_reservations():
    """Show the user's reservations"""
    conn = get_db_connection()
    current_reservations = []
    approved_reservations = []
    reserved_reservations = []
    past_reservations = []
    completed_reservations = []
    canceled_reservations = []

    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, c.cottage_no, c.flag_color, c.cottage_image, c.payment_qr_code, c.owner_name, t.table_no,
                   rat.rating_value, rat.comments as rating_comment, 
                   CASE WHEN rat.id IS NOT NULL THEN 1 ELSE 0 END as has_rating
            FROM reservations r
            JOIN owner_cottages c ON r.cottage_id = c.id
            LEFT JOIN cottage_tables t ON r.table_id = t.id
            LEFT JOIN ratings rat ON r.id = rat.reservation_id AND r.user_id = rat.user_id
            WHERE r.user_id = ?
            ORDER BY r.date_reserved DESC
        ''', (current_user.id,))
        reservation_rows = cursor.fetchall()

        today = datetime.now().date()
        now = datetime.now()

        for row in reservation_rows:
            reservation = Reservation(
                id=row['id'],
                user_id=row['user_id'],
                cottage_id=row['cottage_id'],
                table_id=row['table_id'],
                max_persons=row['max_persons'],
                date_stay=row['date_stay'],
                start_time=row['start_time'],
                end_time=row['end_time'],
                amenities_id=row['amenities_id'],
                amount=row['amount'],
                date_reserved=row['date_reserved'],
                cottage_status=row['cottage_status']
            )
            reservation.cottage_no = row['cottage_no']
            reservation.flag_color = row['flag_color']
            reservation.cottage_image = row['cottage_image']
            reservation.payment_qr_code = row['payment_qr_code']
            reservation.table_no = row['table_no']
            reservation.owner_name = row['owner_name']
            reservation.has_rating = bool(row['has_rating'])
            reservation.rating_value = row['rating_value'] if row['rating_value'] else 0
            reservation.rating_comment = row['rating_comment'] or ''

            stay_date = datetime.strptime(reservation.date_stay, '%Y-%m-%d')
            reservation.start_date = stay_date
            reservation.end_date = stay_date

            # Amenities
            reservation.amenity_details = []
            if reservation.amenities_id:
                for amenity_id in str(reservation.amenities_id).split(','):
                    try:
                        cursor.execute('SELECT category, ame_price FROM amenities_1 WHERE id = ?', (int(amenity_id),))
                        amenity = cursor.fetchone()
                        if amenity:
                            reservation.amenity_details.append({
                                'category': amenity['category'],
                                'price': amenity['ame_price']
                            })
                    except:
                        continue

            # Set cancel policy (simplified)
            days_until = (stay_date.date() - today).days
            try:
                reservation_date = datetime.strptime(reservation.date_reserved, '%b %d %Y %I:%M %p')
            except:
                reservation_date = now
            reservation.can_cancel = False
            if days_until == 0:
                reservation.can_cancel = now < reservation_date + timedelta(hours=1)
            elif 2 <= days_until <= 7:
                reservation.can_cancel = now < stay_date - timedelta(days=2)
            elif days_until > 7:
                reservation.can_cancel = now < stay_date - timedelta(days=3)

            # Categorize
            if reservation.cottage_status == 'pending':
                current_reservations.append(reservation)
            elif reservation.cottage_status == 'approved':
                approved_reservations.append(reservation)
            elif reservation.cottage_status in ['paid_online', 'pay_onsite']:
                reserved_reservations.append(reservation)
            elif reservation.cottage_status in ['completed', 'done']:
                completed_reservations.append(reservation)
            elif reservation.cottage_status in ['canceled', 'declined']:
                canceled_reservations.append(reservation)
            else:
                past_reservations.append(reservation)

    except Exception as e:
        print(f"Error: {e}")
        flash("Failed to load reservations.", "error")
    finally:
        conn.close()

    return render_template('my_reservation.html',
                           user=current_user,
                           current_reservations=current_reservations,
                           approved_reservations=approved_reservations,
                           reserved_reservations=reserved_reservations,
                           past_reservations=past_reservations,
                           completed_reservations=completed_reservations,
                           canceled_reservations=canceled_reservations)


@my_reservation.route('/cancel-reservation', methods=['POST'])
@login_required
def cancel_reservation():
    """Cancel a reservation"""
    reservation_id = request.form.get('reservation_id')
    if not reservation_id:
        flash('No reservation specified.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    try:
        reservation_id = int(reservation_id)
    except ValueError:
        flash('Invalid reservation ID.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Check if reservation exists and belongs to the current user
        cursor.execute('''
            SELECT r.*, c.cottage_no
            FROM reservations r
            JOIN owner_cottages c ON r.cottage_id = c.id
            WHERE r.id = ? AND r.user_id = ?
        ''', (reservation_id, current_user.id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            flash('Reservation not found or you do not have permission to cancel it.', 'error')
            return redirect(url_for('my_reservation.my_reservations'))
        
        # Check if reservation is in a cancelable state
        if reservation['cottage_status'] not in ['pending', 'reserved', 'approved', 'pay_onsite', 'paid_online']:
            flash('This reservation cannot be canceled.', 'error')
            return redirect(url_for('my_reservation.my_reservations'))
        
        # Calculate cancellation deadline based on reservation date
        # Format matches the data: YYYY-MM-DD for date_stay
        stay_date = datetime.strptime(reservation['date_stay'], '%Y-%m-%d')
        today = datetime.now().date()
        days_until_stay = (stay_date.date() - today).days
        
        can_cancel = True
        now = datetime.now()
        
        if days_until_stay <= 0:  # Same day
            # Can cancel up to 1 hour before start time
            # Format matches the data: hh:mm AM/PM for start_time
            start_time_str = reservation['start_time']
            start_time = datetime.strptime(start_time_str, '%I:%M %p')
            start_datetime = datetime.combine(today, start_time.time())
            
            hours_until_start = (start_datetime - now).total_seconds() / 3600
            can_cancel = hours_until_start > 1
            
            if not can_cancel:
                flash('Same-day reservations can only be canceled up to 1 hour before the start time.', 'error')
        elif days_until_stay <= 7:  # Within a week
            # Can cancel up to 2 days before
            can_cancel = days_until_stay >= 2
            if not can_cancel:
                flash('Reservations within a week can only be canceled up to 2 days before.', 'error')
        else:
            # For reservations more than a week away, can cancel up to 3 days before
            # This matches the can_cancel logic in my_reservations
            can_cancel = now < stay_date - timedelta(days=3)
            if not can_cancel:
                flash('Reservations more than a week away can only be canceled up to 3 days before.', 'error')
        
        if can_cancel:
            cursor.execute('''
                UPDATE reservations
                SET cottage_status = 'canceled'
                WHERE id = ?
            ''', (reservation_id,))
            
            conn.commit()
            flash(f'Reservation for Cottage #{reservation["cottage_no"]} canceled successfully.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error canceling reservation: {str(e)}', 'error')
    
    finally:
        if conn:
            conn.close()
    
    return redirect(url_for('my_reservation.my_reservations'))



@my_reservation.route('/submit-payment', methods=['POST'])
@login_required
def submit_payment():
    """Process payment submission and record in payments table"""
    reservation_id = request.form.get('reservation_id')
    payment_method = request.form.get('payment_method')
    reference_number = request.form.get('reference_number', None)
    
    if not reservation_id:
        flash('No reservation specified.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    try:
        reservation_id = int(reservation_id)
    except ValueError:
        flash('Invalid reservation ID.', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
       
        cursor.execute('''
            SELECT r.*, oc.cottage_no, r.amount AS price
            FROM reservations r
            JOIN owner_cottages oc ON r.cottage_id = oc.id
            WHERE r.id = ? AND r.user_id = ?
        ''', (reservation_id, current_user.id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            flash('Reservation not found or you do not have permission to process this payment.', 'error')
            return redirect(url_for('my_reservation.my_reservations'))
        
        # Check if reservation is in a status that can accept payments
        if reservation['cottage_status'] != 'approved':
            flash('Only approved reservations can receive payments.', 'error')
            return redirect(url_for('my_reservation.my_reservations'))
        
        # Check if payment already exists for this reservation
        cursor.execute('''
            SELECT id FROM payments
            WHERE reservation_id = ? AND payment_status != 'canceled'
        ''', (reservation_id,))
        
        existing_payment = cursor.fetchone()
        if existing_payment:
            flash('A payment for this reservation already exists.', 'error')
            return redirect(url_for('my_reservations.my_reservations'))
        
        # Generate transaction ID (combination of date and reservation ID)
        transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d')}-{reservation_id}-{current_user.id}"
        
        # Generate receipt number
        cursor.execute("SELECT COUNT(*) as count FROM payments")
        payment_count = cursor.fetchone()['count']
        receipt_number = f"RCPT-{datetime.now().strftime('%Y%m%d')}-{payment_count + 1}"
        
        # Get amount from reservation price
        amount = reservation['price']
        
        # Determine payment status based on payment method
        payment_status = 'completed' if payment_method == 'online' else 'pending'
        
        # Update reservation status based on payment method
        new_status = 'paid_online' if payment_method == 'online' else 'pay_onsite'
        
        # Create payment record
        payment_details = {}
        if payment_method == 'online' and reference_number:
            payment_details = {'reference_number': reference_number}
        
        cursor.execute('''
            INSERT INTO payments (
                reservation_id, user_id, amount, payment_method, payment_status,
                transaction_id, payment_date, receipt_number, payment_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reservation_id, current_user.id, amount, payment_method, payment_status,
            transaction_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
            receipt_number, json.dumps(payment_details)
        ))
        
        # Update reservation status
        if payment_method == 'online' and reference_number:
            cursor.execute('''
                UPDATE reservations
                SET cottage_status = ?, payment_reference = ?
                WHERE id = ?
            ''', (new_status, reference_number, reservation_id))
        else:
            cursor.execute('''
                UPDATE reservations
                SET cottage_status = ?
                WHERE id = ?
            ''', (new_status, reservation_id))
        
        conn.commit()
        
        flash(f'Payment for Cottage #{reservation["cottage_no"]} processed successfully. Receipt: {receipt_number}', 'success')
        
        # Redirect to payment success page or payment receipt
        if payment_method == 'online':
            return redirect(url_for('my_reservation.payment_receipt', payment_id=cursor.lastrowid))
        else:
            return redirect(url_for('my_reservation.my_reservations'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Error processing payment: {str(e)}', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
        
    finally:
        if conn:
            conn.close()


@my_reservation.route('/payment-receipt/<int:payment_id>')
@login_required
def payment_receipt(payment_id):
    """Display payment receipt"""
    conn = get_db_connection()
    
    try:
        # Use dictionary cursor to get results as dictionaries
        conn.row_factory = sqlite3.Row  # If using SQLite
        cursor = conn.cursor()
        
        # Get payment details with reservation and cottage information
        cursor.execute('''
            SELECT 
                p.id, p.reservation_id, p.user_id, p.amount, p.payment_method,
                p.payment_status, p.payment_date, p.transaction_id, p.receipt_number,
                p.payment_details,
                r.date_stay, r.start_time, r.end_time, r.amount as price,
                c.cottage_no, c.owner_name as cottage_name
            FROM payments p
            JOIN reservations r ON p.reservation_id = r.id
            JOIN owner_cottages c ON r.cottage_id = c.id
            WHERE p.id = ? AND p.user_id = ?
        ''', (payment_id, current_user.id))
        
        payment = cursor.fetchone()
        
        if not payment:
            flash('Payment not found or you do not have permission to view this receipt.', 'error')
            return redirect(url_for('my_reservation.my_reservations'))
        
        
        payment = dict(payment)
        
        
        payment_details = None
        if payment['payment_details']:
            try:
                payment_details = json.loads(payment['payment_details'])
            except json.JSONDecodeError:
                payment_details = {}
        else:
            payment_details = {}
        
        return render_template('payment_receipt.html',
                              payment=payment,
                              payment_details=payment_details)
    
    except Exception as e:
        flash(f'Error retrieving payment receipt: {str(e)}', 'error')
        return redirect(url_for('my_reservation.my_reservations'))
    
    finally:
        if conn:
            conn.close()


def update_completed_reservations():
    """
    Update reservation status to 'completed' when the date_stay has passed and end_time has reached
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now()
        today = now.date().strftime('%Y-%m-%d')
        current_datetime = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # Find reservations where date_stay is before today and end_time is before now and status is not already completed/canceled
        cursor.execute('''
            UPDATE reservations
            SET cottage_status = 'completed', date_completed = ?
            WHERE date_stay < ?
            AND end_time < ?
            AND cottage_status IN ('paid_online', 'onsite-payment')
        ''', (current_datetime, today, current_datetime))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"Updated {affected_rows} reservations to 'completed' status")
        return affected_rows
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating completed reservations: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()

# Add a route that can be called manually or by a scheduler
@my_reservation.route('/update-completed-reservations', methods=['GET'])
@login_required
def trigger_update_completed_reservations():
    """Admin route to manually trigger the update of completed reservations"""
    # Check if user is admin (you can modify this according to your authentication system)
    if not current_user.is_authenticated or current_user.role == 'owner':
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('my_reservations.my_reservations'))
    
    count = update_completed_reservations()
    flash(f'Successfully updated {count} reservations to completed status.', 'success')
    return redirect(url_for('my_reservation.my_reservations'))

def update_completed_reservations():
    """
    Update reservation status to 'completed' when the date_stay and end_time have passed
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now()
        today = now.date().strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M')
        
        # Find reservations where:
        # 1. date_stay is in the past OR
        # 2. date_stay is today AND end_time has passed
        # AND status is an active reservation status
        cursor.execute('''
            UPDATE reservations
            SET cottage_status = 'completed', date_completed = ?
            WHERE (date_stay < ? OR (date_stay = ? AND end_time < ?))
            AND cottage_status IN ('paid_online', 'pay_onsite', 'reserved', 'approved')
        ''', (now.strftime('%Y-%m-%d %H:%M:%S'), today, today, current_time))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"{now.strftime('%Y-%m-%d %H:%M:%S')} - Updated {affected_rows} reservations to 'completed' status")
        return affected_rows
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating completed reservations: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()

# Schedule the job to run every hour
@my_reservation.record_once
def configure_scheduler(state):
    """Initialize the scheduler when the Flask app starts"""
    if not scheduler.running:
        scheduler.add_job(
            update_completed_reservations,
            'interval',
            minutes=60,  # Run every hour
            id='update_reservations_job',
            replace_existing=True
        )
        scheduler.start()
        print("Scheduler started for automatic reservation completion")

@my_reservation.teardown_app_request
def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()

@my_reservation.route('/get-reservation-details/<int:reservation_id>')
@login_required
def get_reservation_details(reservation_id):
    """Get reservation details including QR code for payment"""
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        # Fetch reservation with cottage details
        cursor.execute('''
            SELECT r.*, c.cottage_no, c.payment_qr_code, c.owner_name, ct.table_no
            FROM reservations r
            JOIN owner_cottages c ON r.cottage_id = c.id 
            LEFT JOIN cottage_tables ct ON r.table_id = ct.id
            WHERE r.id = ? AND r.user_id = ?
        ''', (reservation_id, current_user.id))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            return jsonify({'error': 'Reservation not found'}), 404
        
        # If QR code exists, encode it to base64
        qr_code_base64 = None
        if reservation['payment_qr_code']:
            import base64
            # Make sure we're handling the QR code data correctly based on its type
            if isinstance(reservation['payment_qr_code'], bytes):
                qr_code_base64 = base64.b64encode(reservation['payment_qr_code']).decode('utf-8')
            else:
                # If it's already a string, assume it's properly formatted or a path
                qr_code_base64 = reservation['payment_qr_code']
        
        # Return JSON with reservation details
        return jsonify({
            'id': reservation['id'],
            'cottage_no': reservation['cottage_no'],
            'date_stay': reservation['date_stay'],
            'start_time': reservation['start_time'],
            'end_time': reservation['end_time'],
            'amount': float(reservation['amount']),
            'payment_qr_code': qr_code_base64,
            'table_no': reservation['table_no'],
            'owner_name': reservation['owner_name']

        })
    
    except Exception as e:
        print(f"Error fetching reservation details: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if conn:
            conn.close()
