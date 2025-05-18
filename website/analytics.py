from flask import Blueprint, flash, jsonify, redirect, render_template, url_for, send_file
from flask_login import current_user, login_required
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import json
from datetime import datetime, timedelta
import calendar
import logging
import io
import base64
from matplotlib.ticker import FuncFormatter
import numpy as np
import seaborn as sns
from website.models import get_db_connection, OwnerCottage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

analytic = Blueprint('dashboard_analytics', __name__)


@analytic.route('/dashboard/analytics')
@login_required
def analytics():
    """Show analytics and insights for cottage owners"""
    if current_user.role != 'owner':
        flash('You do not have permission to view this page', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
        
    # Basic data is now loaded via AJAX from the analytics-data endpoint
    # Pass the current_user to the template to avoid 'user is undefined' error
    return render_template('analytics.html', user=current_user)


@analytic.route('/dashboard/analytics-data')
@login_required
def analytics_data():
    """API endpoint to get analytics data for charts"""
    if current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        # Get the raw analytics data
        analytics_data = get_analytics_data(current_user.id)
        
        # Get advanced metrics
        advanced_metrics = get_advanced_analytics(current_user.id)
        
        # Calculate current month's occupancy rate
        current_month_occupancy = calculate_current_month_occupancy(current_user.id)
        
        # Generate charts with error handling
        charts = generate_all_charts(analytics_data, current_user.id)
        
        # Prepare data for JSON response
        response_data = {
            'summary': {
                'total_reservations': analytics_data['total_reservations'],
                'total_revenue': float(analytics_data['total_revenue']),
                'current_month_occupancy': current_month_occupancy,
                'advanced_metrics': advanced_metrics
            },
            'charts': charts
        }
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in analytics_data route: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An unexpected error occurred while processing analytics data',
            'summary': {
                'total_reservations': 0,
                'total_revenue': 0,
                'current_month_occupancy': 0,
                'advanced_metrics': {
                    'avg_stay_duration': 0,
                    'repeat_customer_rate': 0,
                    'avg_booking_lead_time': 0
                }
            },
            'charts': {}
        }), 500


def generate_all_charts(analytics_data, user_id):
    """Generate all charts with proper error handling"""
    charts = {}
    
    # Function to safely generate each chart
    def safely_generate(chart_function, *args):
        try:
            return chart_function(*args)
        except Exception as e:
            logger.error(f"Error generating chart with {chart_function.__name__}: {str(e)}", exc_info=True)
            return None
    
    # Generate all charts with safe execution
    charts['revenue_chart'] = safely_generate(generate_revenue_chart, analytics_data.get('monthly_revenue', []))
    
    # Convert cottage performance data for chart generation
    cottage_performance_chart_data = []
    for item in analytics_data.get('cottage_performance', []):
        try:
            cottage_performance_chart_data.append({
                'cottage_name': item['cottage'].name if item.get('cottage') else 'Unknown',
                'reservations_count': item.get('reservations_count', 0),
                'revenue': item.get('revenue', 0)
            })
        except Exception as e:
            logger.error(f"Error processing cottage performance data: {str(e)}", exc_info=True)
    
    charts['cottage_chart'] = safely_generate(generate_cottage_performance_chart, cottage_performance_chart_data)
    charts['time_slot_heatmap'] = safely_generate(generate_time_slot_heatmap, analytics_data)
    charts['payment_method_chart'] = safely_generate(generate_payment_method_chart, user_id)
    charts['occupancy_chart'] = safely_generate(generate_occupancy_rate_chart, analytics_data)
    charts['payment_status_chart'] = safely_generate(generate_payment_status_chart, user_id)
    charts['table_performance_chart'] = safely_generate(generate_table_performance_chart, user_id)
    charts['top_cottages_chart'] = safely_generate(generate_top_cottages_chart, user_id)
    
    return charts


def fig_to_base64(fig):
    """Convert matplotlib figure to base64 encoded string"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)  # Close the figure
    return f"data:image/png;base64,{image_base64}"


def generate_payment_method_chart(user_id):
    """Generate a pie chart for payment methods using matplotlib"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids:
            return None
            
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Query for payment method distribution
        query = f'''
            SELECT 
                payment_method,
                COUNT(*) as count
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str})
            AND payment_method IS NOT NULL
            GROUP BY payment_method
        '''
        
        cursor = conn.execute(query, cottage_ids)
        results = cursor.fetchall()
        
        # Convert to format needed for chart
        payment_data = []
        for row in results:
            payment_data.append({
                'method': row['payment_method'],
                'count': row['count']
            })
        
        # Handle empty results
        if not payment_data:
            payment_data = [
                {'method': 'No data available', 'count': 1}
            ]
        
        # Create dataframe
        df = pd.DataFrame(payment_data)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            df['count'], 
            labels=df['method'],  
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'width': 0.4, 'edgecolor': 'w'},  # Donut style
            textprops={'fontsize': 10}
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        plt.title('Payment Method Distribution', pad=20)
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating payment method chart: {str(e)}", exc_info=True)
        return None
    finally:
        conn.close()


def calculate_current_month_occupancy(user_id):
    """Calculate the occupancy rate for the current month"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids: 
            return 0
        
        # Get current month dates
        now = datetime.now()
        first_day = now.replace(day=1)
        last_day = first_day.replace(
            day=calendar.monthrange(first_day.year, first_day.month)[1]
        )
        
        # For each cottage, calculate days occupied in current month
        total_days = 0
        occupied_days = 0
        
        for cottage_id in cottage_ids:
            # Get total days in the month
            days_in_month = calendar.monthrange(first_day.year, first_day.month)[1]
            total_days += days_in_month
            
            # Get occupied days for this cottage
            query = '''
                SELECT COUNT(DISTINCT date(date_stay)) as occupied_days
                FROM reservations
                WHERE cottage_id = ?
                AND date_stay BETWEEN ? AND ?
                AND cottage_status IN ('reserved', 'completed')
            '''
            
            cursor = conn.execute(query, (cottage_id, first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')))
            result = cursor.fetchone()
            
            if result and result['occupied_days']:
                occupied_days += result['occupied_days']
        
        # Calculate occupancy rate
        occupancy_rate = (occupied_days / total_days * 100) if total_days > 0 else 0
        return round(occupancy_rate, 1)
    except Exception as e:
        logger.error(f"Error calculating current month occupancy: {str(e)}", exc_info=True)
        return 0
    finally:
        conn.close()


def get_analytics_data(user_id):
    """Get analytics data for a specific user"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids:
            return {
                'total_reservations': 0,
                'total_revenue': 0,
                'monthly_revenue': [],
                'reservation_status': [],
                'cottage_performance': []
            }
        
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Get total reservations and revenue
        query = f'''
            SELECT COUNT(*) as total_reservations, COALESCE(SUM(amount), 0) as total_revenue
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str}) AND cottage_status IN ('reserved', 'completed')
        '''
        cursor = conn.execute(query, cottage_ids)
        result = cursor.fetchone()
        
        total_reservations = result['total_reservations'] if result else 0
        total_revenue = result['total_revenue'] if result and result['total_revenue'] else 0
        
        # Get monthly revenue for the past 12 months
        monthly_revenue = get_monthly_revenue(conn, cottage_ids)
        
        # Get reservation status breakdown
        reservation_status = get_reservation_status(conn, cottage_ids)
        
        # Get individual cottage performance
        cottage_performance = get_cottage_performance(conn, cottages)
        
        return {
            'total_reservations': total_reservations,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'reservation_status': reservation_status,
            'cottage_performance': cottage_performance,
            'monthly_occupancy': get_monthly_occupancy_data(conn, cottage_ids),
            'time_slot_data': get_time_slot_data(conn, cottage_ids)
        }
    except Exception as e:
        logger.error(f"Error getting analytics data: {str(e)}", exc_info=True)
        return {
            'total_reservations': 0,
            'total_revenue': 0,
            'monthly_revenue': [],
            'reservation_status': [],
            'cottage_performance': [],
            'monthly_occupancy': [],
            'time_slot_data': []
        }
    finally:
        conn.close()


def get_monthly_revenue(conn, cottage_ids):
    """Get monthly revenue for the past 12 months"""
    try:
        # Generate a list of the past 12 months in YYYY-MM format
        months = []
        now = datetime.now()
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=30 * i)
            months.append(month_date.strftime('%Y-%m'))
        
        if not cottage_ids:
            return [{'month': month, 'revenue': 0} for month in months]
        
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Query for monthly revenue
        query = f'''
            SELECT 
                strftime('%Y-%m', date_stay) as month,
                COALESCE(SUM(amount), 0) as revenue
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str})
            AND date_stay >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', date_stay)
            ORDER BY month
        '''
        
        cursor = conn.execute(query, cottage_ids)
        revenue_by_month = {row['month']: row['revenue'] for row in cursor.fetchall()}
        
        # Fill in months with no revenue
        result = []
        for month in months:
            result.append({
                'month': month,
                'revenue': revenue_by_month.get(month, 0)
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting monthly revenue: {str(e)}", exc_info=True)
        return [{'month': month, 'revenue': 0} for month in months]


def get_reservation_status(conn, cottage_ids):
    """Get breakdown of reservation statuses"""
    try:
        if not cottage_ids:
            return []
            
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        query = f'''
            SELECT 
                CASE 
                    WHEN cottage_status = 'pay_onsite' THEN 'May on Cash'
                    ELSE cottage_status 
                END as status,
                COUNT(*) as count
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str})
            GROUP BY cottage_status
        '''
        
        cursor = conn.execute(query, cottage_ids)
        result = cursor.fetchall()
        
        # Convert to list of dictionaries
        status_counts = []
        for row in result:
            status_counts.append({
                'status': row['status'] or 'unknown',
                'count': row['count']
            })
        
        return status_counts
    except Exception as e:
        logger.error(f"Error getting reservation status: {str(e)}", exc_info=True)
        return []


def get_cottage_performance(conn, cottages):
    """Get performance metrics for each cottage"""
    result = []
    
    try:
        for cottage in cottages:
            try:
                query = '''
                    SELECT 
                        COUNT(*) as reservations_count,
                        COALESCE(SUM(amount), 0) as revenue
                    FROM reservations
                    WHERE cottage_id = ?
                '''
                
                cursor = conn.execute(query, (cottage.id,))
                performance = cursor.fetchone()
                
                result.append({
                    'cottage': cottage,
                    'reservations_count': performance['reservations_count'] if performance else 0,
                    'revenue': performance['revenue'] if performance else 0
                })    
            except Exception as e:
                logger.error(f"Error getting cottage performance for cottage {cottage.id}: {str(e)}", exc_info=True)
                result.append({
                    'cottage': cottage,
                    'reservations_count': 0,
                    'revenue': 0    
                })
                
        return result
    except Exception as e:
        logger.error(f"Error getting cottage performance: {str(e)}", exc_info=True)
        return []


def get_advanced_analytics(user_id):
    """Get advanced analytics metrics"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids:
            return {
                'avg_stay_duration': 0,
                'repeat_customer_rate': 0,
                'avg_booking_lead_time': 0
            }
        
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Calculate average stay duration
        query_stay = f'''
            SELECT AVG(julianday(checkout) - julianday(date_stay)) as avg_stay
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str})
            AND date_stay IS NOT NULL
            AND checkout IS NOT NULL
        '''
        cursor = conn.execute(query_stay, cottage_ids)
        avg_stay = cursor.fetchone()
        avg_stay_duration = round(avg_stay['avg_stay'], 1) if avg_stay and avg_stay['avg_stay'] else 0
        
        # Calculate repeat customer rate
        query_repeat = f'''
            SELECT 
                COUNT(DISTINCT customer_id) as total_customers,
                COUNT(DISTINCT customer_id) - COUNT(DISTINCT CASE WHEN reservation_count = 1 THEN customer_id ELSE NULL END) as repeat_customers
            FROM (
                SELECT 
                    customer_id,
                    COUNT(*) as reservation_count
                FROM reservations
                WHERE cottage_id IN ({cottage_ids_str})
                GROUP BY customer_id
            )
        '''
        cursor = conn.execute(query_repeat, cottage_ids)
        repeat_data = cursor.fetchone()
        
        total_customers = repeat_data['total_customers'] if repeat_data else 0
        repeat_customers = repeat_data['repeat_customers'] if repeat_data else 0
        repeat_rate = round((repeat_customers / total_customers * 100), 1) if total_customers > 0 else 0
        
        # Calculate average booking lead time (days between booking date and stay date)
        query_lead = f'''
            SELECT AVG(julianday(date_stay) - julianday(created_at)) as avg_lead_time
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str})
            AND date_stay IS NOT NULL
            AND created_at IS NOT NULL
        '''
        cursor = conn.execute(query_lead, cottage_ids)
        lead_time = cursor.fetchone()
        avg_lead_time = round(lead_time['avg_lead_time'], 1) if lead_time and lead_time['avg_lead_time'] else 0
        
        return {
            'avg_stay_duration': avg_stay_duration,
            'repeat_customer_rate': repeat_rate,
            'avg_booking_lead_time': avg_lead_time
        }
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {str(e)}", exc_info=True)
        return {
            'avg_stay_duration': 0,
            'repeat_customer_rate': 0,
            'avg_booking_lead_time': 0
        }
    finally:
        conn.close()


def get_monthly_occupancy_data(conn, cottage_ids):
    """Get monthly occupancy rates for the past 12 months"""
    try:
        if not cottage_ids:
            return []
            
        # Generate a list of the past 12 months in YYYY-MM format
        months = []
        now = datetime.now()
        for i in range(11, -1, -1):
            month_date = now - timedelta(days=30 * i)
            months.append({
                'year': month_date.year,
                'month': month_date.month,
                'month_str': month_date.strftime('%Y-%m')
            })
        
        result = []
        
        # For each month, calculate the occupancy rate
        for month_data in months:
            year = month_data['year']
            month = month_data['month']
            days_in_month = calendar.monthrange(year, month)[1]
            
            # Total possible days across all cottages
            total_days = days_in_month * len(cottage_ids)
            
            # Format cottage IDs for SQL query
            cottage_ids_str = ','.join(['?' for _ in cottage_ids])
            
            # Query for occupied days in this month
            query = f'''
                SELECT COUNT(DISTINCT cottage_id || '-' || date(date_stay)) as occupied_days
                FROM reservations
                WHERE cottage_id IN ({cottage_ids_str})
                AND strftime('%Y-%m', date_stay) = ?
                AND cottage_status IN ('reserved', 'completed')
            '''
            
            cursor = conn.execute(query, cottage_ids + [month_data['month_str']])
            occupied_result = cursor.fetchone()
            
            occupied_days = occupied_result['occupied_days'] if occupied_result else 0
            occupancy_rate = (occupied_days / total_days * 100) if total_days > 0 else 0
            
            result.append({
                'month': month_data['month_str'],
                'occupancy_rate': round(occupancy_rate, 1)
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting monthly occupancy data: {str(e)}", exc_info=True)
        return []


def get_time_slot_data(conn, cottage_ids):
    """Get data for time slot heatmap (days of week vs. months)"""
    try:
        if not cottage_ids:
            return []
            
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Query for reservation counts by day of week and month
        query = f'''
            SELECT 
                strftime('%w', date_stay) as day_of_week,
                strftime('%m', date_stay) as month,
                COUNT(*) as reservation_count
            FROM reservations
            WHERE cottage_id IN ({cottage_ids_str})
            AND date_stay >= date('now', '-12 months')
            GROUP BY day_of_week, month
        '''
        
        cursor = conn.execute(query, cottage_ids)
        results = cursor.fetchall()
        
        # Convert to format needed for heatmap
        heatmap_data = []
        for row in results:
            # Convert day of week from 0-6 (Sunday-Saturday) to name
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            day_name = days[int(row['day_of_week'])]
            
            # Convert month number to name
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            month_name = month_names[int(row['month']) - 1]
            
            heatmap_data.append({
                'day': day_name,
                'month': month_name,
                'value': row['reservation_count']
            })
        
        return heatmap_data
    except Exception as e:
        logger.error(f"Error getting time slot data: {str(e)}", exc_info=True)
        return []


def generate_status_chart(status_data):
    """Generate a pie chart for reservation status using matplotlib"""
    if not status_data:
        return None
        
    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(status_data)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            df['count'], 
            labels=df['status'],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'width': 0.4, 'edgecolor': 'w'},  # Donut style
            textprops={'fontsize': 10}
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        plt.title('Reservation Status Distribution', pad=20)
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating status chart: {str(e)}", exc_info=True)
        return None


def generate_revenue_chart(revenue_data):
    """Generate a line chart for monthly revenue using matplotlib"""
    if not revenue_data:
        return None
        
    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(revenue_data)
        
        # Extract month labels (show only the month part)
        month_labels = [m.split('-')[1] for m in df['month']]
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot line chart
        ax.plot(month_labels, df['revenue'], marker='o', linewidth=2, color='#3B82F6')
        
        # Fill area under the line
        ax.fill_between(month_labels, df['revenue'], alpha=0.2, color='#3B82F6')
        
        # Format y-axis as currency
        def currency_formatter(x, pos):
            return f'₱{x:,.0f}'
        ax.yaxis.set_major_formatter(FuncFormatter(currency_formatter))
        
        # Add grid and styling
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_title('Monthly Revenue', fontsize=16, pad=20)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Revenue (PHP)', fontsize=12)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating revenue chart: {str(e)}", exc_info=True)
        return None


def generate_cottage_performance_chart(performance_data):
    """Generate a bar chart for cottage performance using matplotlib"""
    if not performance_data:
        return None
        
    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(performance_data)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Determine number of cottages for spacing
        num_cottages = len(df)
        y_pos = np.arange(num_cottages)
        
        # Plot horizontal bar chart for reservations
        ax.barh(y_pos, df['reservations_count'], height=0.4, color='#3B82F6', label='Reservations')
        
        # Get secondary axis for revenue
        ax2 = ax.twiny()
        ax2.barh(y_pos + 0.4, df['revenue'], height=0.4, color='#10B981', label='Revenue (PHP)')
        
        # Format axes
        ax.set_yticks(y_pos + 0.2)
        ax.set_yticklabels(df['cottage_name'])
        ax.set_xlabel('Number of Reservations', fontsize=12)
        ax2.set_xlabel('Revenue (PHP)', fontsize=12)
        
        # Add title and legend
        ax.set_title('Cottage Performance', fontsize=16, pad=20)
        ax.legend(loc='upper right')
        ax2.legend(loc='upper center')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating cottage performance chart: {str(e)}", exc_info=True)
        return None
    

def generate_time_slot_heatmap(analytics_data):
    """Generate a heatmap for popular booking times using matplotlib"""
    time_slot_data = analytics_data.get('time_slot_data', [])
    if not time_slot_data:
        return None
        
    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(time_slot_data)
        
        # Define correct order for days and months
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Make sure all days and months are in the dataset (with zeros for missing combinations)
        complete_data = []
        for day in days_order:
            for month in months_order:
                # Find matching entry or use 0
                found = False
                for entry in time_slot_data:
                    if entry['day'] == day and entry['month'] == month:
                        complete_data.append({
                            'day': day,
                            'month': month,
                            'value': entry['value']
                        })
                        found = True
                        break
                
                if not found:
                    complete_data.append({
                        'day': day,
                        'month': month,
                        'value': 0
                    })
        
        # Create new dataframe with complete data
        complete_df = pd.DataFrame(complete_data)
        
        # Pivot data for heatmap format
        pivot_df = complete_df.pivot(index='day', columns='month', values='value')
        
        # Reorder the indices and columns
        pivot_df = pivot_df.reindex(index=days_order)
        pivot_df = pivot_df.reindex(columns=months_order)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create heatmap using seaborn
        sns.heatmap(
            pivot_df, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            linewidths=.5, 
            ax=ax
        )
        
        # Add title and labels
        ax.set_title('Popular Booking Times', fontsize=16, pad=20)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Day of Week', fontsize=12)
        
        # Rotate x-axis labels
        plt.xticks(rotation=0)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating time slot heatmap: {str(e)}", exc_info=True)
        return None


def generate_occupancy_rate_chart(analytics_data):
    """Generate a line chart for monthly occupancy rates using matplotlib"""
    occupancy_data = analytics_data.get('monthly_occupancy', [])
    if not occupancy_data:
        return None
        
    try:
        # Convert data to pandas DataFrame
        df = pd.DataFrame(occupancy_data)
        
        # Extract month labels (show only the month part)
        month_labels = [m.split('-')[1] for m in df['month']]
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot line chart
        ax.plot(month_labels, df['occupancy_rate'], marker='o', linewidth=2, color='#8B5CF6')
        
        # Fill area under the line
        ax.fill_between(month_labels, df['occupancy_rate'], alpha=0.2, color='#8B5CF6')
        
        # Format y-axis as percentage
        def percentage_formatter(x, pos):
            return f'{x:.1f}%'
        ax.yaxis.set_major_formatter(FuncFormatter(percentage_formatter))
        
        # Set y-axis limits
        ax.set_ylim(0, 100)
        
        # Add grid and styling
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_title('Monthly Occupancy Rate', fontsize=16, pad=20)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Occupancy Rate', fontsize=12)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating occupancy rate chart: {str(e)}", exc_info=True)
        return None


def generate_payment_status_chart(user_id):
    """Generate a pie chart for payment status distribution"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids:
            return None
            
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Query for payment status distribution
        query = f'''
            SELECT 
                p.payment_status,
                COUNT(*) as count
            FROM payments p
            JOIN reservations r ON p.reservation_id = r.id
            WHERE r.cottage_id IN ({cottage_ids_str})
            GROUP BY p.payment_status
        '''
        
        cursor = conn.execute(query, cottage_ids)
        results = cursor.fetchall()
        
        # Convert to format needed for chart
        status_data = []
        for row in results:
            status_data.append({
                'status': row['payment_status'],
                'count': row['count']
            })
        
        # Handle empty results
        if not status_data:
            status_data = [
                {'status': 'No data available', 'count': 1}
            ]
        
        # Create dataframe
        df = pd.DataFrame(status_data)
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            df['count'], 
            labels=df['status'],
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'width': 0.4, 'edgecolor': 'w'},  # Donut style
            textprops={'fontsize': 10}
        )
        
        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')
        plt.title('Payment Status Distribution', pad=20)
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating payment status chart: {str(e)}", exc_info=True)
        return None
    finally:
        conn.close()


def generate_table_performance_chart(user_id):
    """Generate a bar chart for best performing tables"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids:
            return None
            
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Query for table performance
        query = f'''
            SELECT 
                ct.table_no,
                oc.cottage_no,
                COUNT(r.id) as reservation_count,
                COALESCE(SUM(r.amount), 0) as total_revenue
            FROM cottage_tables ct
            JOIN owner_cottages oc ON ct.cottage_id = oc.id
            LEFT JOIN reservations r ON r.table_id = ct.id
            WHERE oc.id IN ({cottage_ids_str})
            GROUP BY ct.id
            ORDER BY reservation_count DESC
            LIMIT 10
        '''
        
        cursor = conn.execute(query, cottage_ids)
        results = cursor.fetchall()
        
        # Convert to format needed for chart
        table_data = []
        for row in results:
            table_data.append({
                'table_name': f'Cottage {row["cottage_no"]} - Table {row["table_no"]}',
                'reservations': row['reservation_count'],
                'revenue': row['total_revenue']
            })
        
        # Create dataframe
        df = pd.DataFrame(table_data)
        
        if df.empty:
            return None
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bar chart
        y_pos = np.arange(len(df))
        bars = ax.barh(y_pos, df['reservations'], color='#3B82F6')
        
        # Add revenue labels
        for i, bar in enumerate(bars):
            revenue = df['revenue'].iloc[i]
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                   f'₱{revenue:,.0f}', va='center')
        
        # Customize the chart
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['table_name'])
        ax.set_xlabel('Number of Reservations')
        ax.set_title('Best Performing Tables', pad=20)
        
        # Add grid
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating table performance chart: {str(e)}", exc_info=True)
        return None
    finally:
        conn.close()


def generate_top_cottages_chart(user_id):
    """Generate a bar chart for most reserved cottages"""
    conn = get_db_connection()
    try:
        # Get cottage IDs owned by the user
        cottages = OwnerCottage.get_cottages_by_user_id(conn, user_id)
        cottage_ids = [c.id for c in cottages]
        
        if not cottage_ids:
            return None
            
        # Format cottage IDs for SQL query
        cottage_ids_str = ','.join(['?' for _ in cottage_ids])
        
        # Query for top cottages
        query = f'''
            SELECT 
                oc.cottage_no,
                COUNT(r.id) as reservation_count,
                COALESCE(SUM(r.amount), 0) as total_revenue,
                COUNT(DISTINCT r.user_id) as unique_customers
            FROM owner_cottages oc
            LEFT JOIN reservations r ON r.cottage_id = oc.id
            WHERE oc.id IN ({cottage_ids_str})
            GROUP BY oc.id
            ORDER BY reservation_count DESC
            LIMIT 10
        '''
        
        cursor = conn.execute(query, cottage_ids)
        results = cursor.fetchall()
        
        # Convert to format needed for chart
        cottage_data = []
        for row in results:
            cottage_data.append({
                'cottage_name': f'Cottage {row["cottage_no"]}',
                'reservations': row['reservation_count'],
                'revenue': row['total_revenue'],
                'unique_customers': row['unique_customers']
            })
        
        # Create dataframe
        df = pd.DataFrame(cottage_data)
        
        if df.empty:
            return None
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bar chart
        y_pos = np.arange(len(df))
        bars = ax.barh(y_pos, df['reservations'], color='#10B981')
        
        # Add revenue and customer labels
        for i, bar in enumerate(bars):
            revenue = df['revenue'].iloc[i]
            customers = df['unique_customers'].iloc[i]
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                   f'₱{revenue:,.0f} ({customers} customers)', va='center')
        
        # Customize the chart
        ax.set_yticks(y_pos)
        ax.set_yticklabels(df['cottage_name'])
        ax.set_xlabel('Number of Reservations')
        ax.set_title('Most Reserved Cottages', pad=20)
        
        # Add grid
        ax.grid(axis='x', linestyle='--', alpha=0.7)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert figure to base64 image
        img_data = fig_to_base64(fig)
        
        return {'image': img_data}
    except Exception as e:
        logger.error(f"Error generating top cottages chart: {str(e)}", exc_info=True)
        return None
    finally:
        conn.close()


@analytic.route('/download-analytics-report')
@login_required
def download_analytics_report():
    """Generate and download a comprehensive analytics report in CSV format"""
    if current_user.role != 'owner':
        flash('You do not have permission to download this report', 'danger')
        return redirect(url_for('dashboard.dashboard_view'))
    
    try:
        # Get the raw analytics data
        analytics_data = get_analytics_data(current_user.id)
        
        # Get advanced metrics
        advanced_metrics = get_advanced_analytics(current_user.id)
        
        # Create a DataFrame for the summary data
        summary_data = pd.DataFrame([{
            'Total Reservations': analytics_data['total_reservations'],
            'Total Revenue (PHP)': float(analytics_data['total_revenue']),
            'Average Stay Duration (days)': advanced_metrics['avg_stay_duration'],
            'Repeat Customer Rate (%)': advanced_metrics['repeat_customer_rate'],
            'Average Booking Lead Time (days)': advanced_metrics['avg_booking_lead_time']
        }])
        
        # Create a DataFrame for monthly revenue
        monthly_revenue_df = pd.DataFrame(analytics_data.get('monthly_revenue', []))
        
        # Create a DataFrame for reservation status
        status_df = pd.DataFrame(analytics_data.get('reservation_status', []))
        
        # Create a DataFrame for cottage performance
        cottage_performance = []
        for item in analytics_data.get('cottage_performance', []):
            cottage_performance.append({
                'Cottage Name': item['cottage'].name if item.get('cottage') else 'Unknown',
                'Reservations Count': item.get('reservations_count', 0),
                'Revenue (PHP)': item.get('revenue', 0)
            })
        cottage_df = pd.DataFrame(cottage_performance)
        
        # Create a DataFrame for monthly occupancy
        occupancy_df = pd.DataFrame(analytics_data.get('monthly_occupancy', []))
        
        # Create a buffer to write the CSV data
        output = io.StringIO()
        
        # Write each DataFrame to the buffer with headers
        output.write("# ANALYTICS REPORT SUMMARY\n")
        summary_data.to_csv(output, index=False)
        
        output.write("\n\n# MONTHLY REVENUE\n")
        monthly_revenue_df.to_csv(output, index=False)
        
        output.write("\n\n# RESERVATION STATUS\n")
        status_df.to_csv(output, index=False)
        
        output.write("\n\n# COTTAGE PERFORMANCE\n")
        cottage_df.to_csv(output, index=False)
        
        output.write("\n\n# MONTHLY OCCUPANCY RATE\n")
        occupancy_df.to_csv(output, index=False)
        
        # Reset the buffer position to the beginning
        output.seek(0)
        
        # Create a response with the CSV data
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            download_name=f'analytics_report_{now}.csv',
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Error generating analytics report: {str(e)}", exc_info=True)
        flash('An error occurred while generating the report', 'danger')
        return redirect(url_for('dashboard_analytics.analytics'))