// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.reservation-tab');
    const sections = document.querySelectorAll('.reservation-section');
    
    // Set initial state - ensure only one tab is active initially
    function setInitialActiveTab() {
        // By default, make the first tab active
        const firstTab = tabs[0];
        if (firstTab) {
            tabs.forEach(t => {
                // Remove active classes from all tabs
                t.classList.remove('active');
                t.classList.remove('border-blue-500');
                t.classList.remove('text-blue-600');
                t.classList.add('border-transparent');
                t.classList.add('text-gray-600');
            });
            
            // Set the first tab as active
            firstTab.classList.add('active');
            firstTab.classList.add('border-blue-500');
            firstTab.classList.add('text-blue-600');
            firstTab.classList.remove('border-transparent');
            
            // Hide all sections
            sections.forEach(section => {
                section.classList.add('hidden');
            });
            
            // Show the first section
            const firstSectionId = firstTab.id.replace('tab-', 'section-');
            const firstSection = document.getElementById(firstSectionId);
            if (firstSection) {
                firstSection.classList.remove('hidden');
            }
        }
    }
    
    // Call the function to set initial state
    setInitialActiveTab();
    
    // Add click event listeners
    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs
                tabs.forEach(t => {
                    t.classList.remove('active');
                    t.classList.remove('border-blue-500');
                    t.classList.remove('text-blue-600');
                    t.classList.add('border-transparent');
                    t.classList.add('text-gray-600');
                });
                
                // Add active class to clicked tab
                this.classList.add('active');
                this.classList.add('border-blue-500');
                this.classList.add('text-blue-600');
                this.classList.remove('border-transparent');
                
                // Hide all sections
                sections.forEach(section => {
                    section.classList.add('hidden');
                });
                
                // Show corresponding section
                const targetId = this.id.replace('tab-', 'section-');
                const targetSection = document.getElementById(targetId);
                if (targetSection) {
                    targetSection.classList.remove('hidden');
                }
            });
        });
    }
    
    // Set up form submission handler for online payment
    const onlinePaymentForm = document.getElementById('onlinePaymentForm');
    
    if (onlinePaymentForm) {
        onlinePaymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const referenceNumber = document.getElementById('reference_number').value.trim();
            
            if (!referenceNumber) {
                alert('Please enter a valid reference number');
                return;
            }
            
            // Set the form action dynamically
            this.action = `/submit-payment`;
            
            // Add hidden fields for payment method and reservation ID
            let paymentMethodInput = document.createElement('input');
            paymentMethodInput.type = 'hidden';
            paymentMethodInput.name = 'payment_method';
            paymentMethodInput.value = 'online';
            this.appendChild(paymentMethodInput);
            
            let reservationIdInput = document.getElementById('online_reservation_id');
            if (reservationIdInput) {
                reservationIdInput.value = currentReservationId;
            }
            
            // Show processing state
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Processing...';
                submitButton.disabled = true;
            }
            
            // Submit the form
            this.submit();
        });
    }
    
    // Set up form submission handler for onsite payment
    const onsitePaymentForm = document.getElementById('onsitePaymentForm');
    
    if (onsitePaymentForm) {
        onsitePaymentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Set the form action dynamically
            this.action = `/submit-payment`;
            
            // Add payment method as hidden input
            let paymentMethodInput = document.createElement('input');
            paymentMethodInput.type = 'hidden';
            paymentMethodInput.name = 'payment_method';
            paymentMethodInput.value = 'onsite';
            this.appendChild(paymentMethodInput);
            
            // Show processing state
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Processing...';
                submitButton.disabled = true;
            }
            
            // Submit the form
            this.submit();
        });
    }
    
    // Close modal when clicking outside of it
    document.addEventListener('click', function(event) {
        const cancelModal = document.getElementById('cancelModal');
        const paymentModal = document.getElementById('paymentModal');
        
        // For Cancel Modal
        if (cancelModal && !cancelModal.classList.contains('hidden') && event.target === cancelModal) {
            closeCancelModal();
        }
        
        // For Payment Modal
        if (paymentModal && !paymentModal.classList.contains('hidden') && event.target === paymentModal) {
            closePaymentModal();
        }
    });
});

// Cancel Modal Functions
function openCancelModal(reservationId) {
    const cancelModal = document.getElementById('cancelModal');
    const reservationIdField = document.getElementById('cancel_reservation_id');
    
    if (cancelModal && reservationIdField) {
        reservationIdField.value = reservationId;
        cancelModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    }
}

function closeCancelModal() {
    const cancelModal = document.getElementById('cancelModal');
    
    if (cancelModal) {
        cancelModal.classList.add('hidden');
        document.body.style.overflow = ''; // Re-enable scrolling
    }
}

// Payment Modal Functions
let currentReservationId = null;
let currentReservationDetails = null;

function openPaymentModal(reservationId) {
    currentReservationId = reservationId;
    document.getElementById('paymentModal').classList.remove('hidden');
    document.getElementById('onsite_reservation_id').value = reservationId;
    document.getElementById('online_reservation_id').value = reservationId;
    document.getElementById('paymentOptions').classList.remove('hidden');
    document.getElementById('onlinePaymentFormContainer').classList.add('hidden');
    document.body.style.overflow = 'hidden'; // Prevent scrolling
}

function closePaymentModal() {
    document.getElementById('paymentModal').classList.add('hidden');
    document.body.style.overflow = ''; // Re-enable scrolling
    // Reset the view back to payment options
    document.getElementById('onlinePaymentFormContainer').classList.add('hidden');
    document.getElementById('paymentOptions').classList.remove('hidden');
}

function showOnlinePaymentForm() {
    // Hide payment options
    document.getElementById('paymentOptions').classList.add('hidden');
    
    // Show online payment form
    document.getElementById('onlinePaymentFormContainer').classList.remove('hidden');
    
    // Get the reservation ID
    const reservationId = document.getElementById('online_reservation_id').value;
    
    // Fetch reservation details including QR code
    fetchReservationDetails(reservationId);
}

function backToPaymentOptions() {
    document.getElementById('onlinePaymentFormContainer').classList.add('hidden');
    document.getElementById('paymentOptions').classList.remove('hidden');
}

function fetchReservationDetails(reservationId) {
    // Show loading state
    document.getElementById('reservationDetails').innerHTML = `
        <div class="skeleton-loader h-4 w-full bg-gray-200 rounded mb-2"></div>
        <div class="skeleton-loader h-4 w-3/4 bg-gray-200 rounded mb-2"></div>
        <div class="skeleton-loader h-4 w-1/2 bg-gray-200 rounded"></div>
    `;
    
    document.getElementById('qrCodeImage').innerHTML = `
        <div class="flex items-center justify-center h-48 w-48">
            <p class="text-gray-500 text-sm">Loading QR code...</p>
        </div>
    `;
    
    // Make API call to get reservation details
    fetch(`/get-reservation-details/${reservationId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch reservation details');
            }
            return response.json();
        })
        .then(data => {
            // Format the date
            const dateStay = new Date(data.date_stay);
            const formattedDate = dateStay.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            // Format times
            const startTime = data.start_time;
            const endTime = data.end_time;
            const timeRange = `${startTime} - ${endTime}`;
            
            // Update reservation details in the payment modal
            document.getElementById('reservationDetails').innerHTML = `
                <h3 class="text-xl font-bold text-gray-800 mb-2">Cottage Owner: ${data.owner_name}</h3>
                <h4 class="text-lg font-semibold text-gray-800 mb-2">Cottage ${data.cottage_no} Table #${data.table_no}</h4>
                <p class="text-gray-700 mb-1">Date: ${formattedDate}</p>
                <p class="text-gray-700 mb-1">Time: ${timeRange}</p>
                <div class="mt-3 pt-3 border-t border-gray-200">
                    <p class="text-lg font-bold text-green-600">Total Amount: ₱${data.amount.toFixed(2)}</p>
                </div>
            `;
            
            // Display QR code if available
            if (data.payment_qr_code) {
                document.getElementById('qrCodeImage').innerHTML = `
                    <img src="data:image/png;base64,${data.payment_qr_code}" alt="Payment QR Code" class="h-48 w-48">
                `;
            } else {
                document.getElementById('qrCodeImage').innerHTML = `
                    <div class="h-48 w-48 bg-gray-100 rounded flex items-center justify-center">
                        <p class="text-gray-500 text-sm">QR Code not available</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading reservation details:', error);
            
            document.getElementById('reservationDetails').innerHTML = `
                <div class="text-red-500 p-3">
                    Unable to load reservation details. Please try again.
                </div>
            `;
            
            document.getElementById('qrCodeImage').innerHTML = `
                <div class="h-48 w-48 bg-gray-100 rounded flex items-center justify-center">
                    <p class="text-red-500 text-sm">Failed to load QR code</p>
                </div>
            `;
        });
}