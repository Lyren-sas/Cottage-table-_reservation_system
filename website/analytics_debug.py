from flask import Blueprint, jsonify
from flask_login import login_required, current_user
import logging
import traceback

from website import get_db_connection

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

debug = Blueprint('analytics_debug', __name__)

@debug.route('/dashboard/analytics-debug')
@login_required
def analytics_debug():
    """Debug endpoint to identify the source of 500 errors in analytics"""
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    error_details = {
        'stages': [],
        'specific_error': None,
        'traceback': None
    }
    
    try:
        # Stage 1: Test database connection
        error_details['stages'].append('Testing database connection')
        conn = get_db_connection()
        error_details['stages'].append('Database connection successful')
        
        # Stage 2: Check if user has cottages
        error_details['stages'].append('Checking for user cottages')
        from website.models import OwnerCottage
        cottages = OwnerCottage.get_cottages_by_user_id(conn, current_user.id)
        cottage_ids = [c.id for c in cottages]
        error_details['stages'].append(f'Found {len(cottage_ids)} cottages')
        
        # Stage 3: Test simple query execution
        error_details['stages'].append('Testing simple query execution')
        if cottage_ids:
            cottage_ids_str = ','.join(['?' for _ in cottage_ids])
            query = f'''
                SELECT COUNT(*) as total_reservations
                FROM reservations
                WHERE cottage_id IN ({cottage_ids_str})
            '''
            cursor = conn.execute(query, cottage_ids)
            result = cursor.fetchone()
            count = result['total_reservations'] if result else 0
            error_details['stages'].append(f'Basic query returned {count} reservations')
        else:
            error_details['stages'].append('No cottages to query')
        
        # Stage 4: Check if payment_method_chart function exists
        error_details['stages'].append('Checking for payment_method_chart function')
        try:
            from website.analytics import generate_payment_method_chart
            error_details['stages'].append('Payment method chart function exists')
        except (ImportError, AttributeError) as e:
            error_details['stages'].append(f'Payment method chart function missing: {str(e)}')
            
        # Stage 5: Test chart generation functions individually
        error_details['stages'].append('Testing chart generation functions')
        
        # Test status chart
        try:
            from website.analytics import generate_status_chart, get_reservation_status
            status_data = get_reservation_status(conn, cottage_ids)
            generate_status_chart(status_data)
            error_details['stages'].append('Status chart generation successful')
        except Exception as e:
            error_details['stages'].append(f'Status chart generation failed: {str(e)}')
        
        # Test revenue chart
        try:
            from website.analytics import generate_revenue_chart, get_monthly_revenue
            revenue_data = get_monthly_revenue(conn, cottage_ids)
            generate_revenue_chart(revenue_data)
            error_details['stages'].append('Revenue chart generation successful')
        except Exception as e:
            error_details['stages'].append(f'Revenue chart generation failed: {str(e)}')
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'All tests completed',
            'debug_info': error_details
        })
        
    except Exception as e:
        error_details['specific_error'] = str(e)
        error_details['traceback'] = traceback.format_exc()
        logger.error(f"Debug endpoint error: {str(e)}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': f'Error encountered: {str(e)}',
            'debug_info': error_details
        })

# Instructions to integrate this:
# 1. Save this file as analytics_debug.py in your website package
# 2. Import and register the blueprint in your __init__.py file:
#    from .analytics_debug import debug as debug_blueprint
#    app.register_blueprint(debug_blueprint)
# 3. Access the endpoint at /dashboard/analytics-debug