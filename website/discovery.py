from flask import Blueprint, flash, redirect, render_template, request, jsonify, current_app, url_for, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import uuid
import io
import os
from datetime import datetime
from . import get_db_connection
from .models import  OwnerCottage, CottageDiscovery

discoveries = Blueprint('discoveries', __name__, url_prefix='/discoveries')

def allowed_file(filename):
    """Check if file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@discoveries.route('/cottage/<int:cottage_id>/discoveries')
@login_required
def cottage_discoveries(cottage_id):
    conn = get_db_connection()
    cottage = OwnerCottage.get_by_id(conn, cottage_id)
    discoveries = CottageDiscovery.get_all_for_cottage(conn, cottage_id)
    conn.close()
    
    if not cottage or cottage.user_id != current_user.id:
        flash('Cottage not found or you do not have permission to view its discoveries', 'error')
        return redirect(url_for('cottages.my_cottages'))
    
    return render_template(
        'cottage_discovery.html',
        user=current_user,
        cottage=cottage,
        discoveries=discoveries
    )

@discoveries.route('/cottage/<int:cottage_id>/discoveries/data')
@login_required
def cottage_discoveries_data(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            return jsonify({"error": "Not authorized"}), 403
        
        discoveries = CottageDiscovery.get_all_for_cottage(conn, cottage_id)
        discoveries_data = []
        
        for discovery in discoveries:
            discovery_data = discovery.__dict__.copy()
            discovery_data['image_url'] = url_for('static', filename=f'discovery_images/{discovery.image_filename}') \
                if discovery.image_filename else url_for('static', filename='img/default-discovery.png')
            discovery_data['formatted_date'] = discovery.created_at.strftime('%B %d, %Y') if discovery.created_at else 'N/A'
            discoveries_data.append(discovery_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    
    return jsonify({"discoveries": discoveries_data})

@discoveries.route('/cottage/<int:cottage_id>/add-discovery', methods=['GET', 'POST'])
@login_required
def add_discovery(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            flash('Cottage not found or you do not have permission to add discoveries', 'error')
            return redirect(url_for('cottages.my_cottages'))
        
        if request.method == 'POST':
            description = request.form.get('description', '')
            
            # Handle image upload
            image_filename = None
            if 'discovery_image' in request.files:
                file = request.files['discovery_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{cottage_id}_discovery_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'discovery_images')
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    image_filename = filename
            
            # Create and save discovery
            discovery = CottageDiscovery(
                cottage_id=cottage_id,
                image_filename=image_filename,
                description=description
            )
            
            conn.execute("BEGIN")
            discovery.save_to_db(conn)
            conn.commit()
            
            flash('Discovery added successfully!', 'success')
            return redirect(url_for('discoveries.cottage_discoveries', cottage_id=cottage_id))
        
    except Exception as e:
        conn.rollback() if conn else None
        flash(f'Error adding discovery: {str(e)}', 'error')
    
    finally:
        conn.close() if conn else None
    
    return render_template('add_discovery.html', user=current_user, cottage=cottage)


@discoveries.route('/cottage/<int:cottage_id>/delete-discovery/<int:discovery_id>', methods=['POST'])
@login_required
def delete_discovery(cottage_id, discovery_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            flash('Cottage not found or you do not have permission to delete discoveries', 'error')
            return redirect(url_for('cottages.my_cottages'))
        
        discovery = CottageDiscovery.get_by_id(conn, discovery_id)
        
        if not discovery or discovery.cottage_id != cottage_id:
            flash('Discovery not found or does not belong to this cottage', 'error')
            return redirect(url_for('discoveries.cottage_discoveries', cottage_id=cottage_id))
        
        # Delete image file if exists
        if discovery.image_filename:
            image_path = os.path.join(current_app.static_folder, 'discovery_images', discovery.image_filename)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    flash(f'Warning: Could not delete image file: {str(e)}', 'warning')
        
        conn.execute("BEGIN")
        CottageDiscovery.delete(conn, discovery_id)
        conn.commit()
        
        flash('Discovery deleted successfully!', 'success')
    
    except Exception as e:
        conn.rollback() if conn else None
        flash(f'Error deleting discovery: {str(e)}', 'error')
    
    finally:
        conn.close() if conn else None
    
    return redirect(url_for('discoveries.cottage_discoveries', cottage_id=cottage_id))



@discoveries.route('/cottage/<int:cottage_id>/edit-discovery/<int:discovery_id>', methods=['GET', 'POST'])
@login_required
def edit_discovery(cottage_id, discovery_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            flash('Cottage not found or you do not have permission to edit discoveries', 'error')
            return redirect(url_for('cottages.my_cottages'))
        
        discovery = CottageDiscovery.get_by_id(conn, discovery_id)
        
        if not discovery or discovery.cottage_id != cottage_id:
            flash('Discovery not found or does not belong to this cottage', 'error')
            return redirect(url_for('discoveries.cottage_discoveries', cottage_id=cottage_id))
        
        if request.method == 'POST':
            description = request.form.get('description', '')
            
            # Handle image upload
            image_filename = discovery.image_filename
            if 'discovery_image' in request.files:
                file = request.files['discovery_image']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old image if exists
                    if image_filename:
                        old_image_path = os.path.join(current_app.static_folder, 'discovery_images', image_filename)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                            except Exception as e:
                                flash(f'Warning: Could not delete old image: {str(e)}', 'warning')
                    
                    filename = secure_filename(f"{cottage_id}_discovery_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'discovery_images')
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    image_filename = filename
            
            # Update discovery
            discovery.description = description
            discovery.image_filename = image_filename
            
            conn.execute("BEGIN")
            discovery.save_to_db(conn)
            conn.commit()
            
            flash('Discovery updated successfully!', 'success')
            return redirect(url_for('discoveries.cottage_discoveries', cottage_id=cottage_id))
    
    except Exception as e:
        conn.rollback() if conn else None
        flash(f'Error updating discovery: {str(e)}', 'error')
    
    finally:
        conn.close() if conn else None
    
    return render_template('edit_discovery.html', user=current_user, cottage=cottage, discovery=discovery)


@discoveries.route('/cottage/<int:cottage_id>/add-discovery/ajax', methods=['POST'])
@login_required
def add_discovery_ajax(cottage_id):
    conn = get_db_connection()
    try:
        cottage = OwnerCottage.get_by_id(conn, cottage_id)
        
        # Verify ownership
        if not cottage or cottage.user_id != current_user.id:
            return jsonify({"success": False, "message": "Not authorized"}), 403
        
        # Process form data
        description = request.form.get('description', '')
        
        # Handle image upload
        image_filename = None
        if 'discovery_image' in request.files:
            file = request.files['discovery_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{cottage_id}_discovery_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'discovery_images')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                image_filename = filename
        
        # Create and save discovery
        discovery = CottageDiscovery(
            cottage_id=cottage_id,
            image_filename=image_filename,
            description=description
        )
        
        conn.execute("BEGIN")
        discovery_id = discovery.save_to_db(conn)
        discovery.id = discovery_id
        discovery.created_at = datetime.now()
        conn.commit()
        
        # Prepare response data
        discovery_data = discovery.__dict__.copy()
        discovery_data['image_url'] = url_for('static', filename=f'discovery_images/{discovery.image_filename}') \
            if discovery.image_filename else url_for('static', filename='img/default-discovery.png')
        discovery_data['formatted_date'] = discovery.created_at.strftime('%B %d, %Y') if discovery.created_at else 'N/A'
        
        return jsonify({"success": True, "discovery": discovery_data})
    
    except Exception as e:
        conn.rollback() if conn else None
        return jsonify({"success": False, "message": str(e)}), 500
    
    finally:
        conn.close() if conn else None