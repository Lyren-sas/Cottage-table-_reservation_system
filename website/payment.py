from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime
from .models import get_db_connection,Payment, Reservation  #

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/api/payments', methods=['POST'])
@login_required
def process_payment():
    data = request.get_json()
    
    # Extract data from the JSON request
    reservation_id = data.get('reservation_id')
    reference_number = data.get('reference_number')
    amount = data.get('amount')
    payment_method = data.get('payment_method')
    payment_date = data.get('payment_date')
    status = data.get('status')

    # Basic validation
    if not all([reservation_id, reference_number, amount, payment_method, payment_date, status]):
        return jsonify({'success': False, 'message': 'Missing required payment fields'}), 400

    try:
        # Create a new Payment record
        payment = Payment(
            reservation_id=reservation_id,
            reference_number=reference_number,
            amount=float(amount.replace(',', '').replace('₱', '')),  # Sanitize amount if formatted
            payment_method=payment_method,
            payment_date=datetime.strptime(payment_date, '%Y-%m-%d'),
            status=status
        )
        get_db_connection().session.add(payment)

        # Optional: Update reservation status
        reservation = Reservation.query.get(reservation_id)
        if reservation:
            reservation.status = 'paid'  # or 'completed', depending on your flow

        get_db_connection().session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        get_db_connection().session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
