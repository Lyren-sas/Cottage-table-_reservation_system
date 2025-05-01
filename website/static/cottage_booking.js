// booking.js - JavaScript for cottage booking functionality

// Global variables
let cottageAmount;
let cottageId;
let modal;

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Carousel functionality
    const carouselTrack = document.getElementById('carouselTrack');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const slides = document.querySelectorAll('.carousel-item');
    
    if (slides.length <= 1) {
        prevBtn.classList.add('hidden');
        nextBtn.classList.add('hidden');
    } else {
        let slideWidth = slides[0].getBoundingClientRect().width;
        let slideIndex = 0;
        const totalSlides = slides.length;
        
        // Handle window resize
        window.addEventListener('resize', () => {
            slideWidth = slides[0].getBoundingClientRect().width;
            goToSlide(slideIndex);
        });
        
        // Go to specific slide
        function goToSlide(index) {
            if (index < 0) index = 0;
            if (index >= totalSlides) index = totalSlides - 1;
            
            slideIndex = index;
            carouselTrack.style.transform = `translateX(-${slideIndex * slideWidth}px)`;
            
            // Update button visibility
            prevBtn.classList.toggle('opacity-50', slideIndex === 0);
            nextBtn.classList.toggle('opacity-50', slideIndex === totalSlides - 1);
        }
        
        // Event listeners for buttons
        prevBtn.addEventListener('click', () => {
            if (slideIndex > 0) {
                goToSlide(slideIndex - 1);
            }
        });
        
        nextBtn.addEventListener('click', () => {
            if (slideIndex < totalSlides - 1) {
                goToSlide(slideIndex + 1);
            }
        });
        
        // Initialize carousel
        goToSlide(0);
    }
    
    // Booking form functionality
    const bookingForm = document.getElementById('bookingForm');
    modal = document.getElementById('reservationModal');
    const tableContainer = document.getElementById('tableContainer');
    
    // Store initial cottage amount
    cottageId = document.getElementById('cottage_id').value;
    cottageAmount = parseFloat(document.getElementById('base_amount').value || 0);
    
    // Function to format time for display (12-hour format)
    function formatTime(timeStr) {
        if (!timeStr) return '';
        
        const [hours, minutes] = timeStr.split(':');
        const hour = parseInt(hours, 10);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const formattedHour = hour % 12 || 12;
        
        return `${formattedHour}:${minutes} ${ampm}`;
    }
    
    // Function to format date for display
    function formatDate(dateStr) {
        if (!dateStr) return '';
        
        const date = new Date(dateStr);
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // Helper function to get today's date in YYYY-MM-DD format
    function getTodayDate() {
        const today = new Date();
        const year = today.getFullYear();
        let month = (today.getMonth() + 1).toString().padStart(2, '0');
        let day = today.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Load tables function - modified to work without date and filter by capacity
    function loadTables() {
        const cottageId = document.getElementById('cottage_id').value;
        const dateStay = document.getElementById('date_stay').value || getTodayDate(); // Use today's date if no date selected
        const maxPersons = parseInt(document.getElementById('max_persons').value) || 1;
        const tablesUrl = bookingForm.getAttribute('data-tables-url');
        const imageBasePath = bookingForm.getAttribute('data-image-base-path');
        
        // Show loading state
        tableContainer.innerHTML = `
            <div class="col-span-2 text-center py-4 text-gray-500">
                <svg class="animate-spin h-8 w-8 mx-auto mb-2 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading tables...
            </div>`;
        
        fetch(`${tablesUrl}?cottage_id=${cottageId}&date=${dateStay}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    tableContainer.innerHTML = '';
                    
                    // Filter tables based on capacity
                    const filteredTables = data.tables.filter(table => table.capacity >= maxPersons);
                    
                    if (filteredTables.length === 0) {
                        tableContainer.innerHTML = `
                            <div class="col-span-2 text-center py-4 text-gray-500">
                                No tables available with capacity for ${maxPersons} person(s).
                            </div>`;
                        return;
                    }
                    
                    filteredTables.forEach(table => {
                        const tableCard = document.createElement('div');
                        const isAvailable = table.cottage_status === 'available';
                        const statusColor = isAvailable ? 'green' : (table.cottage_status === 'pending' ? 'yellow' : 'red');
                        const statusText = table.cottage_status.charAt(0).toUpperCase() + table.cottage_status.slice(1);
                        
                        tableCard.className = `border rounded-lg overflow-hidden ${!isAvailable ? 'opacity-50' : 'cursor-pointer hover:border-blue-500 hover:shadow-md transition duration-200'}`;
                        tableCard.innerHTML = `
                            <div class="relative">
                                ${table.table_image ? 
                                    `<img src="${imageBasePath}${table.table_image}" alt="Table ${table.table_no}" class="w-full h-40 object-cover">` : 
                                    `<div class="w-full h-40 bg-gray-200 flex items-center justify-center"><span class="text-gray-500">No Image</span></div>`
                                }
                                <div class="absolute top-0 right-0 bg-${statusColor}-500 text-white px-2 py-1 text-xs rounded-bl-lg">
                                    ${statusText}
                                </div>
                            </div>
                            <div class="p-4">
                                <h3 class="font-medium">Table #${table.table_no}</h3>
                                <p class="text-sm text-gray-600">Capacity: ${table.capacity} persons</p>
                                <p class="text-sm font-semibold mt-1">₱${table.price.toFixed(2)}</p>
                            </div>
                        `;
                        
                        if (isAvailable) {
                            tableCard.setAttribute('data-table-id', table.id);
                            tableCard.setAttribute('data-table-no', table.table_no);
                            tableCard.setAttribute('data-table-price', table.price);
                            tableCard.setAttribute('data-table-capacity', table.capacity);
                            
                            tableCard.addEventListener('click', function() {
                                // Remove selected class from all tables
                                document.querySelectorAll('#tableContainer > div').forEach(el => {
                                    el.classList.remove('border-blue-500', 'ring-2', 'ring-blue-200');
                                });
                                
                                // Add selected class to this table
                                this.classList.add('border-blue-500', 'ring-2', 'ring-blue-200');
                                
                                // Set hidden input value
                                document.getElementById('table_id').value = this.getAttribute('data-table-id');
                                
                                // Update amount
                                const baseAmount = parseFloat(document.getElementById('base_amount').value || 0);
                                const tablePrice = parseFloat(this.getAttribute('data-table-price') || 0);
                                document.getElementById('amount').value = baseAmount + tablePrice;
                                
                                // Show the modal with selected details
                                openReservationModal(this);
                            });
                        }
                        
                        tableContainer.appendChild(tableCard);
                    });
                } else {
                    tableContainer.innerHTML = `
                        <div class="col-span-2 text-center py-4 text-red-500">
                            <svg class="mx-auto mb-2 h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Error loading tables: ${data.message}
                        </div>`;
                }
            })
            .catch(error => {
                tableContainer.innerHTML = `
                    <div class="col-span-2 text-center py-4 text-red-500">
                        <svg class="mx-auto mb-2 h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Error loading tables: ${error.message}
                    </div>`;
            });
    }
    
    // Function to open reservation modal
    function openReservationModal(tableElement) {
        const selectedTableInfo = document.getElementById('selectedTableInfo');
        const selectedDateInfo = document.getElementById('selectedDateInfo');
        const selectedTimeInfo = document.getElementById('selectedTimeInfo');
        const selectedPersonsInfo = document.getElementById('selectedPersonsInfo');
        const tableCapacity = tableElement.getAttribute('data-table-capacity');
        
        // Get form values
        const dateStay = document.getElementById('date_stay').value || getTodayDate();
        const startTime = document.getElementById('start_time').value;
        const endTime = document.getElementById('end_time').value;
        const maxPersons = document.getElementById('max_persons').value;
        
        // Set modal information
        selectedTableInfo.textContent = `Table #${tableElement.getAttribute('data-table-no')} (Capacity: ${tableCapacity} persons)`;
        selectedDateInfo.textContent = formatDate(dateStay);
        selectedTimeInfo.textContent = `${formatTime(startTime)} to ${formatTime(endTime)}`;
        selectedPersonsInfo.textContent = `${maxPersons} person(s)`;
        
        // Reset amenity checkboxes
        document.querySelectorAll('input[name="amenities"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Show current total
        updateTotalAmount();
        
        // Show modal
        modal.classList.remove('hidden');
    }
    
    // Add event listener to max_persons to reload tables when it changes
    document.getElementById('max_persons').addEventListener('change', function() {
        loadTables();
    });
    
    // Initialize - load tables immediately without waiting for date selection
    loadTables();
    
    // Update total amount based on selected amenities
    window.updateTotalAmount = function() {
        // Get cottage base amount and table price
        const baseAmount = parseFloat(document.getElementById('base_amount').value || 0);
        const tableId = document.getElementById('table_id').value;
        let tablePrice = 0;
        
        // Find the selected table element to get its price
        const selectedTable = document.querySelector(`[data-table-id="${tableId}"]`);
        if (selectedTable) {
            tablePrice = parseFloat(selectedTable.getAttribute('data-table-price') || 0);
        }
        
        // Start with base amount + table price
        let total = baseAmount + tablePrice;
        
        // Add prices of selected amenities
        document.querySelectorAll('input[name="amenities"]:checked').forEach(checkbox => {
            total += parseFloat(checkbox.getAttribute('data-price') || 0);
        });
        
        // Update display
        const totalAmountEl = document.getElementById('totalAmount');
        if (totalAmountEl) {
            totalAmountEl.textContent = `₱${total.toFixed(2)}`;
        }
        
        // Update hidden input for form submission
        document.getElementById('amount').value = total;
    };
    
    // Add event listeners to all amenity checkboxes
    document.querySelectorAll('input[name="amenities"]').forEach(checkbox => {
        checkbox.addEventListener('change', updateTotalAmount);
    });
    
    // Check date availability - modified to always load tables
    window.checkDateAvailability = function() {
        const cottageId = document.getElementById('cottage_id').value;
        const dateStay = document.getElementById('date_stay').value || getTodayDate();
        const availabilityUrl = bookingForm.getAttribute('data-availability-url');
        
        fetch(`${availabilityUrl}?cottage_id=${cottageId}&date=${dateStay}`)
            .then(response => response.json())
            .then(data => {
                const messageEl = document.getElementById('date_availability_message');
                
                if (data.success) {
                    // Display availability message if needed
                    if (messageEl) {
                        if (data.available) {
                            messageEl.textContent = "Date available!";
                            messageEl.className = "mt-2 text-sm text-green-600";
                        } else {
                            messageEl.textContent = "This date may not be fully available.";
                            messageEl.className = "mt-2 text-sm text-yellow-600";
                        }
                        messageEl.classList.remove('hidden');
                    }
                }
                
                // Always load tables when date changes, regardless of availability
                loadTables();
            })
            .catch(error => {
                console.error("Error checking availability:", error);
                // Still try to load tables even if availability check fails
                loadTables();
            });
    };
    
    // Update end time minimum value based on start time
    window.updateEndTimeMin = function() {
        const startTime = document.getElementById('start_time').value;
        const endTimeInput = document.getElementById('end_time');
        endTimeInput.min = startTime;
        
        // If end time is now less than start time, update it
        const endTime = endTimeInput.value;
        if (endTime <= startTime) {
            // Add one hour to start time for end time
            const startDate = new Date(`2000-01-01T${startTime}`);
            startDate.setHours(startDate.getHours() + 1);
            const newEndTime = startDate.toTimeString().substring(0, 5);
            endTimeInput.value = newEndTime;
        }
        
        // Check availability with new times
        checkTimeAvailability();
    };
    
    // Check time availability
    window.checkTimeAvailability = function() {
        const cottageId = document.getElementById('cottage_id').value;
        const dateStay = document.getElementById('date_stay').value || getTodayDate();
        const startTime = document.getElementById('start_time').value;
        const endTime = document.getElementById('end_time').value;
        const availabilityUrl = bookingForm.getAttribute('data-availability-url');
        
        if (!cottageId || !startTime || !endTime) return;
        
        fetch(`${availabilityUrl}?cottage_id=${cottageId}&date=${dateStay}&start_time=${startTime}&end_time=${endTime}`)
            .then(response => response.json())
            .then(data => {
                const messageEl = document.getElementById('time_availability_message');
                
                if (data.success) {
                    if (data.available) {
                        messageEl.textContent = "Time slot available!";
                        messageEl.className = "mt-2 text-sm text-green-600";
                    } else {
                        messageEl.textContent = "This time slot conflicts with an existing reservation.";
                        messageEl.className = "mt-2 text-sm text-red-600";
                    }
                    messageEl.classList.remove('hidden');
                }
            })
            .catch(error => {
                console.error("Error checking time availability:", error);
            });
    };
    
    // Close modal event handlers
    document.getElementById('closeModal').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    document.getElementById('cancelButton').addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // Confirm reservation
    document.getElementById('confirmButton').addEventListener('click', () => {
        if (validateForm()) {
            // Get selected amenities
            const selectedAmenities = [];
            document.querySelectorAll('input[name="amenities"]:checked').forEach(checkbox => {
                selectedAmenities.push(checkbox.value);
            });
            
            // Add amenities to form
            if (selectedAmenities.length > 0) {
                // Remove existing hidden inputs for amenities
                document.querySelectorAll('input[name="selected_amenities[]"]').forEach(el => el.remove());
                
                // Add new hidden inputs
                selectedAmenities.forEach(amenityId => {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = 'selected_amenities[]';
                    hiddenInput.value = amenityId;
                    document.getElementById('bookingForm').appendChild(hiddenInput);
                });
            }
            
            document.getElementById('bookingForm').submit();
        }
    });
    
    // Form validation
    function validateForm() {
        const tableId = document.getElementById('table_id').value;
        const dateStay = document.getElementById('date_stay').value;
        const startTime = document.getElementById('start_time').value;
        const endTime = document.getElementById('end_time').value;
        const maxPersons = document.getElementById('max_persons').value;
        
        if (!tableId) {
            alert('Please select a table for your reservation.');
            return false;
        }
        
        if (!dateStay) {
            alert('Please select a date for your reservation.');
            return false;
        }
        
        if (!startTime || !endTime) {
            alert('Please select both start and end time for your reservation.');
            return false;
        }
        
        if (startTime >= endTime) {
            alert('End time must be after start time.');
            return false;
        }
        
        if (!maxPersons || maxPersons < 1) {
            alert('Please enter a valid number of persons.');
            return false;
        }
        
        // Check if number of persons exceeds table capacity
        const selectedTable = document.querySelector(`[data-table-id="${tableId}"]`);
        if (selectedTable) {
            const tableCapacity = parseInt(selectedTable.getAttribute('data-table-capacity') || 0);
            if (parseInt(maxPersons) > tableCapacity) {
                alert(`The selected table only has capacity for ${tableCapacity} persons.`);
                return false;
            }
        }
        
        return true;
    }
    
    // Handle clicking outside the modal to close
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
    
    // Escape key closes modal
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
        }
    });

    // Check availability for a specific date
    window.checkAvailability = function() {
        const checkDate = document.getElementById('check_date').value;
        if (!checkDate) {
            alert('Please select a date to check availability.');
            return;
        }
        
        // Redirect to the same page with date parameter
        window.location.href = window.location.pathname + "?date=" + checkDate;
    };
});


