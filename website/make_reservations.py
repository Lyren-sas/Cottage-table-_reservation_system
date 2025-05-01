import base64
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import time  # Add this import for sleep function
from . import get_db_connection
from .models import CottageDiscovery, OwnerCottage, Amenity, CottageTable, OwnerNotification, Notification

make_reservation_bp = Blueprint('make-reservation', __name__)

@make_reservation_bp.route('/make-reservation')
@login_required
def make_reservation():
    conn = get_db_connection()
    cottages = []
    amenities = []
    selected_date = request.args.get('date', datetime.now().strftime('%b %d %Y'))

    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM owner_cottages')
        cottage_rows = cursor.fetchall()

        today_date = datetime.now().strftime('%b %d %Y')

        for row in cottage_rows:
            status = row['status'] if 'status' in row.keys() else 'available'

            cottage = OwnerCottage(
                id=row['id'],
                user_id=row['user_id'],
                owner_name=row['owner_name'],
                cottage_no=row['cottage_no'],
                flag_color=row['flag_color'],
                cottage_image=row['cottage_image'],
                cottage_location=row['cottage_location'],
                cottage_description=row['cottage_description'],
                status=status
            )
            
            
            cottage.is_reserved = False
            cottage.reservation_status = "available"
            
            cottages.append(cottage)

    except Exception as e:
        flash(f'Error fetching cottages: {str(e)}', 'error')
    finally:
        conn.close()

    return render_template(
        'make_reservation.html',
        user=current_user,
        cottages=cottages,
        today_date=today_date,
        selected_date=selected_date
    )


@make_reservation_bp.route('/book-cottage/<cottage_id>')
@login_required
def book_cottage(cottage_id):
    conn = get_db_connection()
    
    cottage = None
    amenities = []
    cottage_discoveries = []
    tables = []
    selected_date = request.args.get('date', datetime.now().strftime('%b %d %Y'))
    today_date = datetime.now().strftime('%b %d, %Y')
    
    # First, ensure the cursor returns rows as dictionaries
    conn.row_factory = sqlite3.Row  # If using SQLite
    cursor = conn.cursor()
    
    # Fetch cottage details
    cursor.execute('SELECT * FROM owner_cottages WHERE id = ?', (cottage_id,))
    cottage_row = cursor.fetchone()
    
    if not cottage_row:
        flash('Cottage not found.', 'error')
        return redirect(url_for('make-reservation.make_reservation'))
    
    status = cottage_row['status'] if 'status' in cottage_row else 'available'
    
    # Create cottage object using proper error handling for each field
    cottage = OwnerCottage(
        id=cottage_row['id'],
        user_id=cottage_row['user_id'],
        owner_name=cottage_row['owner_name'],
        cottage_no=cottage_row['cottage_no'],
        flag_color=cottage_row['flag_color'],
        cottage_image=cottage_row['cottage_image'],
        cottage_location=cottage_row['cottage_location'],
        cottage_description=cottage_row['cottage_description'],
        status=status
    )
    
    # Fetch tables for the cottage and check their reservation status
    cursor.execute('SELECT * FROM cottage_tables WHERE cottage_id = ?', (cottage_id,))
    table_rows = cursor.fetchall()
    
    for table_row in table_rows:
        # Check if table is already reserved for the selected date
        # Modified to include "paid_online" and "pay_onsite" in status check
        cursor.execute('''
            SELECT * FROM reservations 
            WHERE table_id = ? 
            AND date_stay = ? 
            AND cottage_status IN ("approved", "pending", "paid_online", "pay_onsite")
        ''', (table_row['id'], selected_date))
        
        table_reservation = cursor.fetchone()
        table_status = "reserved" if table_reservation else "available"
        
        if table_reservation:
            table_reservation_status = table_reservation['cottage_status']
        else:
            table_reservation_status = "available"
        
        table = CottageTable(
            id=table_row['id'],
            cottage_id=table_row['cottage_id'],
            table_no=table_row['table_no'],
            capacity=table_row['capacity'],
            table_image=table_row['table_image'] if 'table_image' in table_row else None,
            price=table_row['price']
        )
        table.status = table_status
        table.reservation_status = table_reservation_status
        tables.append(table)
    
    # Fetch amenities
    cursor.execute('SELECT * FROM amenities_1')
    amenity_rows = cursor.fetchall()
    
    for row in amenity_rows:
        amenity = Amenity(
            id=row['id'],
            category=row['category'],
            ame_price=row['ame_price']
        )
        amenities.append(amenity)
    
    # Fetch cottage discoveries for carousel
    cottage_discoveries = CottageDiscovery.get_all_for_cottage(conn, cottage_id)
    
    conn.close()
    
    return render_template(
        'new_book.html',
        user=current_user,
        cottage=cottage,
        tables=tables,
        amenities=amenities,
        cottage_discoveries=cottage_discoveries,
        today_date=today_date,
        selected_date=selected_date
    )


# Add route to get table details
@make_reservation_bp.route('/get-table-details/<table_id>')
@login_required
def get_table_details(table_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cottage_tables WHERE id = ?', (table_id,))
        table = cursor.fetchone()
        
        if not table:
            return jsonify({
                'success': False,
                'message': 'Table not found'
            })
        
        return jsonify({
            'success': True,
            'table': {
                'id': table['id'],
                'table_no': table['table_no'],
                'capacity': table['capacity'],
                'price': table['price']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    finally:
        conn.close()


@make_reservation_bp.route('/check-availability')
@login_required
def check_availability():
    cottage_id = request.args.get('cottage_id')
    date_stay = request.args.get('date')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not cottage_id or not date_stay:
        return jsonify({'success': False, 'message': 'Missing required parameters'})
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if cottage is available for the selected date
        # Modified to include "paid_online" and "pay_onsite" in status check
        cursor.execute('''
            SELECT * FROM reservations 
            WHERE cottage_id = ? 
            AND date_stay = ? 
            AND cottage_status IN ("approved", "pending", "paid_online", "pay_onsite")
        ''', (cottage_id, date_stay))
        
        existing_reservations = cursor.fetchall()
        
        # If no time provided, just check date availability
        if not start_time or not end_time:
            return jsonify({
                'success': True,
                'available': len(existing_reservations) == 0
            })
        
        # Check for time conflicts
        if existing_reservations:
            cursor.execute('''
                SELECT * FROM reservations 
                WHERE cottage_id = ? 
                AND date_stay = ? 
                AND cottage_status IN ("approved", "pending", "paid_online", "pay_onsite")
                AND NOT (
                    (start_time >= ?) OR (end_time <= ?)
                )
            ''', (cottage_id, date_stay, end_time, start_time))
            
            time_conflicts = cursor.fetchall()
            return jsonify({
                'success': True,
                'available': len(time_conflicts) == 0
            })
        
        return jsonify({
            'success': True,
            'available': True
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@make_reservation_bp.route('/get-cottage-tables')
@login_required
def get_cottage_tables():
    cottage_id = request.args.get('cottage_id')
    date_stay = request.args.get('date')
    
    if not cottage_id:
        return jsonify({'success': False, 'message': 'Missing cottage ID'})
    
    conn = get_db_connection()
    tables = []
    
    try:
        cursor = conn.cursor()
        
        # Get all tables for the cottage using the CottageTable model
        cottage_tables = CottageTable.get_by_cottage_id(conn, cottage_id)
        
        for table in cottage_tables:
            # Check if table is already reserved
            # Modified to include "paid_online" and "pay_onsite" in status check
            cursor.execute('''
                SELECT * FROM reservations 
                WHERE table_id = ? 
                AND date_stay = ? 
                AND cottage_status IN ("approved", "pending", "paid_online", "pay_onsite")
            ''', (table.id, date_stay))
            
            reservation = cursor.fetchone()
            
            table_data = {
                'id': table.id,
                'table_no': table.table_no,
                'capacity': table.capacity,
                'table_image': table.table_image,
                'price': table.price,
                'cottage_status': reservation['cottage_status'] if reservation else 'available'
            }
            
            tables.append(table_data)
        
        return jsonify({
            'success': True,
            'tables': tables
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()
        
@make_reservation_bp.route('/process-reservation', methods=['POST'])
@login_required
def process_reservation():
    try:
        # Get form data
        cottage_id = request.form.get('cottage_id')
        date_stay = request.form.get('date_stay')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        max_persons = request.form.get('max_persons')
        table_id = request.form.get('table_id')
        amount = request.form.get('amount')
        selected_amenities = request.form.getlist('selected_amenities[]')
        
        # Validate inputs
        if not all([cottage_id, date_stay, start_time, end_time, max_persons, table_id, amount]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('make-reservation.book_cottage', cottage_id=cottage_id))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Format the date_stay to match expected format if needed
            try:
                # First, try parsing as YYYY-MM-DD (standard HTML date input format)
                date_obj = datetime.strptime(date_stay, '%b %d %Y')
                # Format it to the expected format for database operations
                formatted_date = date_obj.strftime('%b %d %Y')
                date_stay = formatted_date
            except ValueError:
                try:
                    # If that fails, try parsing as 'May 02 2025' format
                    date_obj = datetime.strptime(date_stay, '%b %d %Y')
                    # It's already in the correct format, so no need to convert
                    date_stay = date_stay
                except ValueError:
                    # If both parsing attempts fail, log the issue but continue
                    print(f"Warning: Could not parse date '{date_stay}' - using as is")
                    pass  # Use the date string as-is
            
            # Format the time to ensure it's in the correct 12-hour format (HH:MM AM/PM)
            try:
                # Check if time is already in 12-hour format with AM/PM
                if 'AM' in start_time or 'PM' in start_time:
                    # Time is already in 12-hour format, ensure consistent formatting
                    try:
                        start_time_obj = datetime.strptime(start_time, '%I:%M %p')
                        start_time = start_time_obj.strftime('%I:%M %p')
                    except ValueError:
                        # Try alternative 12-hour formats that might be in use
                        try:
                            start_time_obj = datetime.strptime(start_time, '%I:%M%p')
                            start_time = start_time_obj.strftime('%I:%M %p')
                        except ValueError:
                            pass  # Keep original format if we can't parse it
                
                if 'AM' in end_time or 'PM' in end_time:
                    try:
                        end_time_obj = datetime.strptime(end_time, '%I:%M %p')
                        end_time = end_time_obj.strftime('%I:%M %p')
                    except ValueError:
                        try:
                            end_time_obj = datetime.strptime(end_time, '%I:%M%p')
                            end_time = end_time_obj.strftime('%I:%M %p')
                        except ValueError:
                            pass  # Keep original format if we can't parse it
                else:
                    # Time is in 24-hour format, convert to 12-hour
                    try:
                        # Try to parse with seconds format first (HH:MM:SS)
                        try:
                            start_time_obj = datetime.strptime(start_time, '%H:%M:%S')
                            end_time_obj = datetime.strptime(end_time, '%H:%M:%S')
                        except ValueError:
                            # If that fails, try without seconds (HH:MM)
                            start_time_obj = datetime.strptime(start_time, '%H:%M')
                            end_time_obj = datetime.strptime(end_time, '%H:%M')
                        
                        # Format them to 12-hour format with AM/PM
                        start_time = start_time_obj.strftime('%I:%M %p')
                        end_time = end_time_obj.strftime('%I:%M %p')
                    except ValueError as e:
                        print(f"Time format error: {e}. start_time: {start_time}, end_time: {end_time}")
                
                # For debugging
                print(f"Final time formats - start_time: {start_time}, end_time: {end_time}")
                
            except Exception as e:
                # Catch any other errors in time processing
                print(f"Time processing error: {e}. start_time: {start_time}, end_time: {end_time}")
                pass  # Continue with the reservation process with whatever time format we have
            
            # Get cottage and table details
            cursor.execute('SELECT cottage_no FROM owner_cottages WHERE id = ?', (cottage_id,))
            cottage = cursor.fetchone()
            
            cursor.execute('SELECT table_no FROM cottage_tables WHERE id = ?', (table_id,))
            table = cursor.fetchone()
            
            # Check if table capacity matches max_persons
            cursor.execute('SELECT capacity FROM cottage_tables WHERE id = ?', (table_id,))
            table_capacity = cursor.fetchone()
            if not table_capacity or int(max_persons) > table_capacity['capacity']:
                flash('Selected table does not have enough capacity for the number of persons.', 'error')
                return redirect(url_for('make-reservation.book_cottage', cottage_id=cottage_id))
            
            # Check for conflicts - UPDATED to include "paid_online" and "pay_onsite" in status check
            cursor.execute('''
                SELECT * FROM reservations 
                WHERE cottage_id = ? AND table_id = ?
                AND date_stay = ?
                AND cottage_status IN ("approved", "pending", "paid_online", "pay_onsite")
                AND (
                    (? BETWEEN start_time AND end_time) OR
                    (? BETWEEN start_time AND end_time) OR
                    (start_time BETWEEN ? AND ?) OR
                    (end_time BETWEEN ? AND ?)
                )
            ''', (cottage_id, table_id, date_stay, start_time, end_time, start_time, end_time, start_time, end_time))
            
            conflict = cursor.fetchone()
            if conflict:
                flash('This Cottage Table or time slot is already reserved.', 'error')
                return redirect(url_for('make-reservation.book_cottage', cottage_id=cottage_id))
            
            # Create reservation
            reservation_id = create_reservation(
                conn,
                cottage_id=cottage_id,
                table_id=table_id,
                date_stay=date_stay,
                start_time=start_time,
                end_time=end_time,
                max_persons=max_persons,
                user_id=current_user.id,
                amount=amount,
                amenities_ids=','.join(selected_amenities) if selected_amenities else ''
            )

            # Create notification for the user
            Notification.create_reservation_notification(conn, reservation_id)
            
            # Create notification for the owner
            OwnerNotification.create_reservation_notification(conn, reservation_id)
            
            # Insert selected amenities
            for amenity_id in selected_amenities:
                cursor.execute('''
                    INSERT INTO cottage_amenities (cottage_id, reservation_id, amenity_id, user_id)
                    VALUES (?, ?, ?, ?)
                ''', (cottage_id, reservation_id, amenity_id, current_user.id))
            
            conn.commit()
            flash('Reservation created successfully! Waiting for owner approval.', 'success')
            return redirect(url_for('make-reservation.book_cottage', cottage_id=cottage_id))
        
        except Exception as e:
            conn.rollback()
            flash(f'Error creating reservation: {str(e)}', 'error')
            return redirect(url_for('make-reservation.book_cottage', cottage_id=cottage_id))
        finally:
            conn.close()
    
    except Exception as e:
        flash(f'Error processing reservation: {str(e)}', 'error')
        return redirect(url_for('make-reservation.make_reservation'))

# Helper function to create reservation
def create_reservation(conn, cottage_id, table_id, date_stay, start_time, end_time, max_persons, user_id, amount, amenities_ids):
    cursor = conn.cursor()
    
    # Parse the date correctly - try multiple formats
    try:
        # First try YYYY-MM-DD format (what's in the database)
        parsed_date = datetime.strptime(date_stay, '%Y-%m-%d')
        date_stay_str = parsed_date.strftime('%Y-%m-%d')  # Keep in YYYY-MM-DD format for database
    except ValueError:
        try:
            # Then try Month Day Year format
            parsed_date = datetime.strptime(date_stay, '%b %d %Y')
            date_stay_str = parsed_date.strftime('%Y-%m-%d')  # Convert to YYYY-MM-DD format
        except ValueError:
            # If all parsing fails, use the original string
            date_stay_str = date_stay
    
    # Parse the times correctly - they should be in '%I:%M %p' format (e.g. '02:30 PM')
    try:
        parsed_start_time = datetime.strptime(start_time, '%I:%M %p')
        # Format as a string for the database
        start_time_str = parsed_start_time.strftime('%I:%M %p')
    except ValueError:
        # Fallback to the original string
        start_time_str = start_time
    
    try:
        parsed_end_time = datetime.strptime(end_time, '%I:%M %p')
        # Format as a string for the database
        end_time_str = parsed_end_time.strftime('%I:%M %p')
    except ValueError:
        # Fallback to the original string
        end_time_str = end_time
    
    # Use formatted string values for SQLite TEXT columns
    cursor.execute('''
        INSERT INTO reservations (
            cottage_id, table_id, amenities_id, date_stay, start_time, end_time, max_persons, 
            user_id, amount, cottage_status, date_reserved
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        cottage_id, table_id, amenities_ids, date_stay_str, start_time_str, end_time_str, max_persons,
        user_id, amount, 'pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    return cursor.lastrowid

@make_reservation_bp.route('/cottage-reviews/<int:cottage_id>')
@login_required
def cottage_reviews(cottage_id):
    """Return JSON list of reviews (with user profile) for a given cottage."""
    # Log access to this endpoint
    print(f"Accessing cottage reviews for cottage ID: {cottage_id}")
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    
    try:
        cur = conn.cursor()
        print("Executing SQL query for reviews...")
        
        cur.execute('''
            SELECT
              r.rating_value,
              r.comments,
              r.created_at,
              u.name       AS reviewer_name,
              u.user_image AS reviewer_image
            FROM ratings r
            JOIN users u ON r.user_id = u.id
            WHERE r.cottage_id = ?
            ORDER BY r.created_at DESC
        ''', (cottage_id,))
        
        rows = cur.fetchall()
        print(f"Found {len(rows)} reviews for cottage ID {cottage_id}")
        
        reviews = []
        for row in rows:
            # Handle the user_image encoding properly
            img_data = None
            if row['reviewer_image']:
                # Check if reviewer_image is already bytes, otherwise convert it
                if isinstance(row['reviewer_image'], bytes):
                    img_bytes = row['reviewer_image']
                else:
                    # If it's a string path to an image, we'll skip base64 encoding
                    img_data = row['reviewer_image']
                    img_bytes = None
                
                # Only base64 encode if we have actual image bytes
                if img_bytes:
                    try:
                        img_data = base64.b64encode(img_bytes).decode('ascii')
                    except TypeError as e:
                        print(f"Error encoding image: {e}")
                        img_data = None

            review_data = {
                'rating_value': row['rating_value'],
                'comments':     row['comments'],
                'created_at':   row['created_at'],
                'name':         row['reviewer_name'],
                'image_b64':    img_data
            }
            reviews.append(review_data)
            print(f"Processed review: {review_data['name']}, Rating: {review_data['rating_value']}")

        print(f"Returning {len(reviews)} reviews as JSON")
        return jsonify(success=True, reviews=reviews)

    except Exception as e:
        print(f"ERROR in cottage_reviews: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=str(e))
    
    finally:
        conn.close()