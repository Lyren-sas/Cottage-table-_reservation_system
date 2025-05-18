// Enhanced analytics.js file for analytics dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Fetch analytics data from the server
    fetchAnalyticsData();

    // Add refresh button functionality
    const refreshButton = document.createElement('button');
    refreshButton.innerHTML = `
      <span class="flex items-center gap-2">
        <i class="fas fa-sync"></i>
        <span>Refresh Data</span>
      </span>
    `;
    refreshButton.className = 'inline-flex items-center bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold px-6 py-2 rounded-lg shadow transition-all duration-200 mb-6 focus:outline-none focus:ring-2 focus:ring-blue-400';
    refreshButton.addEventListener('click', fetchAnalyticsData);
    
    const container = document.querySelector('.container');
    container.insertBefore(refreshButton, container.firstChild.nextSibling);
});

/**
 * Fetch analytics data from the server endpoint
 */
function fetchAnalyticsData() {
    // Show loading state
    setLoadingState(true);
    
    fetch('/dashboard/analytics-data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update dashboard with the received data
            updateDashboard(data);
        })
        .catch(error => {
            console.error('Error fetching analytics data:', error);
            showErrorMessage('Failed to load analytics data: ' + error.message);
        })
        .finally(() => {
            setLoadingState(false);
        });
}

/**
 * Update the dashboard with analytics data
 * @param {Object} data - The analytics data received from the server
 */
function updateDashboard(data) {
    try {
        // Update summary cards
        updateSummaryCards(data.summary);
        
        // Update advanced metrics
        updateAdvancedMetrics(data.summary.advanced_metrics);
        
        // Render charts if data is available
        renderCharts(data.charts);

        // Show success message that disappears after 3 seconds
        
    } catch (error) {
        console.error('Error updating dashboard:', error);
        showErrorMessage('Error updating dashboard: ' + error.message);
    }
}

/**
 * Show a success message that fades out
 * @param {string} message - Success message to display
 */
function showSuccessMessage(message) {
    const alertElement = document.createElement('div');
    alertElement.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg transition-opacity duration-500 z-50';
    alertElement.textContent = message;
    document.body.appendChild(alertElement);
    
    // Fade out and remove after 3 seconds
    setTimeout(() => {
        alertElement.style.opacity = '0';
        setTimeout(() => alertElement.remove(), 500);
    }, 3000);
}

/**
 * Update the summary cards with data
 * @param {Object} summary - Summary data
 */
function updateSummaryCards(summary) {
    if (!summary) return;
    
    // Format total revenue as currency
    const formattedRevenue = new Intl.NumberFormat('en-PH', {
        style: 'currency',
        currency: 'PHP',
        maximumFractionDigits: 0
    }).format(summary.total_revenue || 0);
    
    // Update the summary cards
    document.getElementById('total-reservations').textContent = summary.total_reservations || 0;
    document.getElementById('total-revenue').textContent = formattedRevenue;
    document.getElementById('occupancy-rate').textContent = (summary.current_month_occupancy || 0) + '%';
}

/**
 * Update advanced metrics section
 * @param {Object} metrics - Advanced metrics data
 */
function updateAdvancedMetrics(metrics) {
    if (!metrics) return;
    
    document.getElementById('avg-stay-duration').textContent = (metrics.avg_stay_duration || 0) + ' days';
    document.getElementById('repeat-customer-rate').textContent = (metrics.repeat_customer_rate || 0) + '%';
    document.getElementById('avg-booking-lead-time').textContent = (metrics.avg_booking_lead_time || 0) + ' days';
}

/**
 * Render all charts with the provided data
 * @param {Object} charts - Chart data from the server
 */
function renderCharts(charts) {
    if (!charts) return;
    
    // Function to safely render each chart
    const safeRender = (elementId, chartData) => {
        const container = document.getElementById(elementId);
        if (!container) {
            console.warn(`Container not found for chart: ${elementId}`);
            return;
        }

        if (!chartData || !chartData.image) {
            container.innerHTML = `
                <div class="flex h-full items-center justify-center">
                    <p class="text-gray-500">No data available</p>
                </div>`;
            return;
        }
        
        try {
            // Create an image element with the base64 data
            const img = document.createElement('img');
            img.src = chartData.image;
            img.alt = elementId.replace('-', ' ');
            img.className = 'w-full h-full object-contain';
            
            // Add loading state
            img.onload = () => {
                container.innerHTML = '';
                container.appendChild(img);
            };
            
            img.onerror = () => {
                container.innerHTML = `
                    <div class="flex h-full items-center justify-center">
                        <p class="text-red-500">Failed to load chart</p>
                    </div>`;
            };
        } catch (err) {
            console.error(`Error rendering ${elementId}:`, err);
            container.innerHTML = `
                <div class="flex h-full items-center justify-center">
                    <p class="text-red-500">Chart rendering failed</p>
                </div>`;
        }
    };
    
    // Render each chart
    safeRender('revenue-chart', charts.revenue_chart);
    safeRender('cottage-chart', charts.cottage_chart);
    safeRender('time-slot-heatmap', charts.time_slot_heatmap);
    safeRender('payment-method-chart', charts.payment_method_chart);
    safeRender('occupancy-chart', charts.occupancy_chart);
    safeRender('payment-status-chart', charts.payment_status_chart);
    safeRender('table-performance-chart', charts.table_performance_chart);
    safeRender('top-cottages-chart', charts.top_cottages_chart);
}

/**
 * Set loading state for the dashboard
 * @param {boolean} isLoading - Whether the dashboard is loading
 */
function setLoadingState(isLoading) {
    const chartContainers = document.querySelectorAll('[id$="-chart"], [id$="-heatmap"]');
    
    if (isLoading) {
        // Show loading indicator for each chart
        chartContainers.forEach(container => {
            container.innerHTML = `
                <div class="flex items-center justify-center h-full">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                </div>`;
        });
        
        // Set summary cards to loading state
        document.getElementById('total-reservations').textContent = '...';
        document.getElementById('total-revenue').textContent = '...';
        document.getElementById('occupancy-rate').textContent = '...';
        
        // Set advanced metrics to loading state
        document.getElementById('avg-stay-duration').textContent = '...';
        document.getElementById('repeat-customer-rate').textContent = '...';
        document.getElementById('avg-booking-lead-time').textContent = '...';
    }
}

/**
 * Show error message on the dashboard
 * @param {string} message - Error message to display
 */
function showErrorMessage(message) {
    const alertElement = document.createElement('div');
    alertElement.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50';
    alertElement.textContent = message;
    document.body.appendChild(alertElement);
    
    // Remove after 5 seconds
    setTimeout(() => alertElement.remove(), 5000);
    
    // Show error message in each chart container
    const chartContainers = document.querySelectorAll('[id$="-chart"], [id$="-heatmap"]');
    chartContainers.forEach(container => {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full text-red-500">
                <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                <p>${message}</p>
                <button class="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm" 
                        onclick="fetchAnalyticsData()">
                    Try Again
                </button>
            </div>`;
    });
}