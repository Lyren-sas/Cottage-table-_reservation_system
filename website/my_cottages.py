from datetime import datetime, time
import os
from flask import Blueprint, jsonify, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import get_db_connection
from .models import OwnerCottage, CottageTable, Amenity, CottageDiscovery
from . import get_db_connection

cottages = Blueprint('cottages', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@cottages.route('/my-cottages')
@login_required
def my_cottages():
    conn = get_db_connection()
    try:
        # Make sure the OwnerCottage.get_cottages_by_user_id method returns proper Python objects
        # not sqlite3.Row objects directly
        cottages_list = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
      
        for cottage in cottages_list:
            if cottage.cottage_image and not cottage.cottage_image.startswith('/static/'):
                cottage.cottage_image = cottage.cottage_image
            
           
            try:
                # Use a cursor to execute a query
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM cottage_discoveries WHERE cottage_id = ?", 
                    (cottage.id,)
                )
                count_result = cursor.fetchone()
                cottage.discovery_count = count_result[0] if count_result else 0
                cursor.execute(
                    "SELECT COUNT(*) FROM cottage_tables WHERE cottage_id = ?", 
                    (cottage.id,)
                )
                count_result = cursor.fetchone()
                cottage.tables_count = count_result[0] if count_result else 0

            except Exception as e:
                cottage.discovery_count = 0
                cottage.tables_count = 0
                print(f"Error counting discoveries: {str(e)}")
    except Exception as e:
        flash(f'Error retrieving cottages: {str(e)}', 'error')
        cottages_list = []
    finally:
        conn.close()
    
    return render_template('my_cottages.html', user=current_user, cottages=cottages_list)


@cottages.route('/add-cottage', methods=['GET', 'POST'])
@login_required
def add_cottage():
    conn = None

    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            cottage_no = request.form.get('cottage_no')
            flag_color = request.form.get('flag_color')
            cottage_location = request.form.get('cottage_location', '')
            cottage_description = request.form.get('cottage_description', '')

            if flag_color == 'Other':
                new_color = request.form.get('new_color')
                if new_color and new_color.strip():
                    flag_color = new_color.strip()

            
            cottage_image = None
            if 'cottage_image' in request.files:
                file = request.files['cottage_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_{cottage_no}_{file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'cottage_images')
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    cottage_image = filename  

            try:
                conn.execute("BEGIN")
                
                new_cottage = OwnerCottage(
                    user_id=current_user.id,
                    owner_name=current_user.name,
                    cottage_no=cottage_no,
                    flag_color=flag_color,
                    cottage_image=cottage_image,
                    cottage_location=cottage_location,
                    cottage_description=cottage_description,
                    status="available"  
                )
                
                new_cottage_id = new_cottage.save_to_db(conn)
                new_cottage.id = new_cottage_id 
                
                num_tables = int(request.form.get('num_tables', 0))
                total_capacity = 0
                
                for i in range(1, num_tables + 1):
                    table_no_key = f'table_no_{i}'
                    capacity_key = f'table_{i}_capacity'
                    
                    # Skip tables that don't exist in the form (might have been removed by user)
                    if table_no_key not in request.form or capacity_key not in request.form:
                        continue
                    
                    table_no = request.form.get(table_no_key)
                    capacity = request.form.get(capacity_key)
                    # Add price handling - default to 0 if not provided
                    price = float(request.form.get(f'table_{i}_price', 0) or 0)
                    
                    # Handle table image
                    table_image = None
                    if f'table_image_{i}' in request.files:
                        file = request.files[f'table_image_{i}']
                        if file and file.filename and allowed_file(file.filename):
                            filename = secure_filename(f"{current_user.id}_{cottage_no}_table_{table_no}_{file.filename}")
                            upload_folder = os.path.join(current_app.static_folder, 'table_images')
                            os.makedirs(upload_folder, exist_ok=True)
                            file_path = os.path.join(upload_folder, filename)
                            file.save(file_path)
                            table_image = filename
                    
                    if table_no and capacity:
                        try:
                            capacity_int = int(capacity)
                            if capacity_int > 0:
                                table = CottageTable(
                                    cottage_id=new_cottage_id,
                                    table_no=table_no,
                                    capacity=capacity_int,
                                    table_image=table_image,
                                    price=price,  # Include price in the table creation
                                    status="available"
                                )
                                table.save_to_db(conn)
                                total_capacity += capacity_int
                        except ValueError:
                            flash(f'Invalid capacity for table {table_no}. Table was not added.', 'error')
                
                # Update cottage with total capacity
                if total_capacity > 0:
                    new_cottage.max_persons = total_capacity
                    new_cottage.update_in_db(conn)
                
                conn.commit()
                flash('Cottage added successfully!', 'success')
                return redirect(url_for('cottages.my_cottages'))

            except Exception as e:
                conn.rollback()
                flash(f'Error adding cottage: {str(e)}', 'error')

    except Exception as e:
        flash(f'Error initializing form: {str(e)}', 'error')

    finally:
        if conn:
            conn.close()

    return render_template('add_cottage.html', user=current_user)

@cottages.route('/edit-cottage/<int:cottage_id>', methods=['GET', 'POST'])
@login_required
def edit_cottage(cottage_id):
    conn = get_db_connection()
    tables = []
    
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            flash('Cottage not found or you do not have permission to edit it', 'error')
            return redirect(url_for('cottages.my_cottages'))
        
        # Get existing tables
        tables = CottageTable.get_by_cottage_id(conn, cottage_id)
        
        if request.method == 'POST':
            cottage_no = request.form.get('cottage_no')
            flag_color = request.form.get('flag_color')
            cottage_location = request.form.get('cottage_location', '')
            cottage_description = request.form.get('cottage_description', '')
            
            if flag_color == 'Other':
                new_color = request.form.get('new_color')
                if new_color and new_color.strip():
                    flag_color = new_color.strip()
            
            # Handle image upload
            cottage_image = cottage.cottage_image
            if 'cottage_image' in request.files:
                file = request.files['cottage_image']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old image if exists
                    if cottage_image:
                        old_image_path = os.path.join(current_app.static_folder, 'cottage_images', cottage_image)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                            except Exception as e:
                                flash(f'Warning: Could not delete old image: {str(e)}', 'warning')
                    
                    filename = secure_filename(f"{current_user.id}_{cottage_no}_{file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'cottage_images')
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    cottage_image = filename  # Store just the filename in the database
            
            try:
                conn.execute("BEGIN")
                
                # Update cottage details
                cottage.cottage_no = cottage_no
                cottage.flag_color = flag_color
                cottage.cottage_image = cottage_image
                cottage.cottage_location = cottage_location
                cottage.cottage_description = cottage_description
                
                cottage.update_in_db(conn)
                
                # Handle tables to delete
                tables_to_delete = request.form.get('delete_table_ids', '')
                if tables_to_delete:
                    table_ids = [int(id) for id in tables_to_delete.split(',') if id.strip()]
                    for table_id in table_ids:
                        # Get table to delete its image
                        table = CottageTable.get_by_id(conn, table_id)
                        if table and table.table_image:
                            try:
                                image_path = os.path.join(current_app.static_folder, 'table_images', table.table_image)
                                if os.path.exists(image_path):
                                    os.remove(image_path)
                            except Exception as e:
                                flash(f'Warning: Could not delete table image: {str(e)}', 'warning')
                        
                        CottageTable.delete_from_db(conn, table_id)
                
                # Update existing tables
                table_ids = request.form.getlist('table_ids')
                for table_id in table_ids:
                    table_id = int(table_id)
                    table_no = request.form.get(f'table_no_{table_id}')
                    capacity = request.form.get(f'table_capacity_{table_id}')
                    
                    if table_no and capacity:
                        try:
                            capacity_int = int(capacity)
                            if capacity_int > 0:
                                table = CottageTable.get_by_id(conn, table_id)
                                if table and table.cottage_id == cottage_id:
                                    # Handle table image update
                                    table_image = table.table_image
                                    if f'table_image_{table_id}' in request.files:
                                        file = request.files[f'table_image_{table_id}']
                                        if file and file.filename and allowed_file(file.filename):
                                            # Delete old table image if exists
                                            if table_image:
                                                old_image_path = os.path.join(current_app.static_folder, 'table_images', table_image)
                                                if os.path.exists(old_image_path):
                                                    try:
                                                        os.remove(old_image_path)
                                                    except Exception as e:
                                                        flash(f'Warning: Could not delete old table image: {str(e)}', 'warning')
                                            
                                            filename = secure_filename(f"{current_user.id}_{cottage_no}_table_{table_no}_{file.filename}")
                                            upload_folder = os.path.join(current_app.static_folder, 'table_images')
                                            os.makedirs(upload_folder, exist_ok=True)
                                            file_path = os.path.join(upload_folder, filename)
                                            file.save(file_path)
                                            table_image = filename
                                    
                                    table.table_no = table_no
                                    table.capacity = capacity_int
                                    table.table_image = table_image
                                    table.update_in_db(conn)
                        except ValueError:
                            flash(f'Invalid capacity for table {table_no}. Table was not updated.', 'error')
                
                # Add new tables
                new_table_count = int(request.form.get('new_table_count', 0))
                for i in range(new_table_count):
                    table_no = request.form.get(f'new_table_no_{i}')
                    capacity = request.form.get(f'new_table_capacity_{i}')
                    
                    # Handle new table image upload
                    table_image = None
                    if f'new_table_image_{i}' in request.files:
                        file = request.files[f'new_table_image_{i}']
                        if file and file.filename and allowed_file(file.filename):
                            filename = secure_filename(f"{current_user.id}_{cottage_no}_table_{table_no}_{file.filename}")
                            upload_folder = os.path.join(current_app.static_folder, 'table_images')
                            os.makedirs(upload_folder, exist_ok=True)
                            file_path = os.path.join(upload_folder, filename)
                            file.save(file_path)
                            table_image = filename
                    
                    if table_no and capacity:
                        try:
                            capacity_int = int(capacity)
                            if capacity_int > 0:
                                table = CottageTable(
                                    cottage_id=cottage_id,
                                    table_no=table_no,
                                    capacity=capacity_int,
                                    table_image=table_image,
                                    status="available"
                                )
                                table.save_to_db(conn)
                        except ValueError:
                            flash(f'Invalid capacity for new table {table_no}. Table was not added.', 'error')
                
              
                updated_tables = CottageTable.get_by_cottage_id(conn, cottage_id)
                total_capacity = sum(table.capacity for table in updated_tables)
                cottage.max_persons = total_capacity
                cottage.update_in_db(conn)
                
                conn.commit()
                flash('Cottage updated successfully!', 'success')
                return redirect(url_for('cottages.my_cottages'))
            
            except Exception as e:
                conn.rollback()
                flash(f'Error updating cottage: {str(e)}', 'error')
    
    except Exception as e:
        flash(f'Error retrieving cottage: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return render_template('edit_cottage.html', user=current_user, cottage=cottage, tables=tables)

@cottages.route('/delete-cottage/<int:cottage_id>', methods=['POST'])
@login_required
def delete_cottage(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            flash('Cottage not found or you do not have permission to delete it', 'error')
            return redirect(url_for('cottages.my_cottages'))
        
        conn.execute("BEGIN")
        
        # First delete all tables and their images
        tables = CottageTable.get_by_cottage_id(conn, cottage_id)
        for table in tables:
            if table.table_image:
                try:
                    image_path = os.path.join(current_app.static_folder, 'table_images', table.table_image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    flash(f'Warning: Could not delete table image: {str(e)}', 'warning')
        
        # Delete all tables
        CottageTable.delete_by_cottage_id(conn, cottage_id)
        
        # Then delete the cottage
        OwnerCottage.delete_from_db(conn, cottage_id)
        
        # Delete cottage image if exists
        if cottage.cottage_image:
            image_path = os.path.join(current_app.static_folder, 'cottage_images', cottage.cottage_image)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    # Log this error but continue with deletion
                    flash(f'Warning: Could not delete image file: {str(e)}', 'warning')
        
        conn.commit()
        flash('Cottage deleted successfully!', 'success')
    
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting cottage: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('cottages.my_cottages'))

@cottages.route('/cottage/<int:cottage_id>/tables')
@login_required
def cottage_tables(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            flash('Cottage not found or you do not have permission to view its tables', 'error')
            return redirect(url_for('cottages.my_cottages'))
        
        tables = CottageTable.get_by_cottage_id(conn, cottage_id)
    
    except Exception as e:
        flash(f'Error retrieving tables: {str(e)}', 'error')
        tables = []
    
    finally:
        conn.close()
    
    return render_template('cottage_tables.html', user=current_user, cottage=cottage, tables=tables)

@cottages.route('/cottage/<int:cottage_id>/tables/data')
@login_required
def cottage_tables_data(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            return jsonify({"error": "Not authorized"}), 403
        
        tables = CottageTable.get_by_cottage_id(conn, cottage_id)
        tables_data = []
        
        for table in tables:
            table_data = table.__dict__.copy()
            table_data['image_url'] = url_for('static', filename=f'table_images/{table.table_image}') \
                if table.table_image else url_for('static', filename='img/default-table.png')
            table_data['formatted_price'] = f"₱{table_data.get('price', 0):,.2f}"
            tables_data.append(table_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    
    return jsonify({"tables": tables_data})


@cottages.route('/cottage/<int:cottage_id>/add-table/ajax', methods=['POST'])
@login_required
def add_table_ajax(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            return jsonify({"success": False, "message": "Not authorized"}), 403
        
        # Check if it's a multipart form data or JSON request
        table_image = None
        if request.content_type and 'multipart/form-data' in request.content_type:
            table_no = request.form.get('table_no')
            capacity = request.form.get('capacity')
            price = request.form.get("price")
            
            # Handle table image
            if 'table_image' in request.files:
                file = request.files['table_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.id}_{cottage.cottage_no}_table_{table_no}_{file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'table_images')
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    table_image = filename
        else:
            data = request.json
            table_no = data.get('table_no')
            capacity = data.get('capacity')
            price = data.get("price")
        
        if not table_no or not capacity or not price:
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        try:
            capacity = int(capacity)
            if capacity <= 0:
                return jsonify({"success": False, "message": "Capacity must be positive"}), 400
                
            price = float(price)
            if price < 0:
                return jsonify({"success": False, "message": "Price cannot be negative"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Capacity must be a number and price must be a valid amount"}), 400
        
        conn.execute("BEGIN")
        table = CottageTable(
            cottage_id=cottage_id,
            table_no=table_no,
            capacity=capacity,
            price=price,  
            table_image=table_image,
            status="available"
        )
        table_id = table.save_to_db(conn)
        table.id = table_id
        
        # Update cottage max_persons
        tables = CottageTable.get_by_cottage_id(conn, cottage_id)
        total_capacity = sum(table.capacity for table in tables)
        cottage.max_persons = total_capacity
        cottage.update_in_db(conn)
        
        conn.commit()
        
        # Add image URL to response
        table_dict = table.__dict__
        if table.table_image:
            table_dict['image_url'] = url_for('static', filename=f'table_images/{table.table_image}')
        else:
            table_dict['image_url'] = url_for('static', filename='img/default-table.png')
            
        return jsonify({"success": True, "table": table_dict})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
    finally:
        conn.close()






