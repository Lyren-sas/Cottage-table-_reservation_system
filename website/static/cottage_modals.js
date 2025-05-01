// Global variables
let currentCottageId = null;
let currentCottageTables = [];
let currentDiscoveries = [];

// Delete Cottage Functions
function confirmDelete(cottageId) {
    const deleteForm = document.getElementById('deleteForm');
    deleteForm.action = `/cottage/${cottageId}/delete`;
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
}

// Tables Modal Functions
async function openTablesModal(cottageId, cottageNo) {
    currentCottageId = cottageId;
    document.getElementById('modalCottageNo').textContent = cottageNo;
    
    // Show modal and loading state
    document.getElementById('tablesModal').classList.remove('hidden');
    document.getElementById('tablesLoading').classList.remove('hidden');
    document.getElementById('tablesContent').classList.add('hidden');
    
    // Fetch tables data
    await fetchTables(cottageId);
}

function closeTablesModal() {
    document.getElementById('tablesModal').classList.add('hidden');
    currentCottageId = null;
    currentCottageTables = [];
}

function fetchTables(cottageId) {
    return fetch(`/cottage/${cottageId}/tables/data`)
        .then(response => response.json())
        .then(data => {
            // Store tables in global variable
            currentCottageTables = data.tables || [];
            
            // Update table count indicator
            document.getElementById('modalCottageNo').textContent += ` (${currentCottageTables.length} tables)`;
            
            // Render tables
            renderTables();
            
            // Hide loading and show content
            document.getElementById('tablesLoading').classList.add('hidden');
            document.getElementById('tablesContent').classList.remove('hidden');
        })
        .catch(err => {
            console.error("Error loading tables:", err);
            alert("Error loading tables: " + err);
            document.getElementById('tablesLoading').classList.add('hidden');
        });
}

// Render Tables Function - Updated to include table images and price
function renderTables() {
    const noTablesMessage = document.getElementById('noTablesMessage');
    const tableCardView = document.getElementById('tableCardView');
    const tableTableView = document.getElementById('tableTableView');
    const tablesTableBody = document.getElementById('tablesTableBody');
    
    if (currentCottageTables.length === 0) {
        noTablesMessage.classList.remove('hidden');
        tableCardView.classList.add('hidden');
        tableTableView.classList.add('hidden');
        return;
    }
    
    noTablesMessage.classList.add('hidden');
    
    // Card view is visible by default, table view is hidden
    tableCardView.classList.remove('hidden');
    tableTableView.classList.add('hidden');
    
    // Clear existing card and table views
    tableCardView.innerHTML = '';
    tablesTableBody.innerHTML = '';
    
    // Render card view
    currentCottageTables.forEach(table => {
        const tableCard = document.createElement('div');
        tableCard.className = 'bg-white rounded-lg shadow-md overflow-hidden border-2 border-gray-200';
        
        // Table image display in card view
        const imageUrl = table.image_url || (table.table_image ? 
            `/static/table_images/${table.table_image}` : 
            '/static/img/default-table.png');
        
        tableCard.innerHTML = `
            <div class="relative h-48 bg-gray-100">
                <img src="${imageUrl}" alt="Table ${table.table_no}" class="w-full h-full object-cover">
                <span class="absolute top-2 right-2 px-3 py-1 rounded-full text-sm font-medium ${table.status === 'available' ? 'bg-green-300 text-green-800' : 'bg-red-300 text-red-800'}">
                    ${table.status}
                </span>
            </div>
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-xl font-bold text-gray-800">Table ${table.table_no}</h3>
                </div>
                
                <div class="mb-4">
                    <p class="text-gray-600 mb-2"><strong>Capacity:</strong> ${table.capacity} person(s)</p>
                    <p class="text-green-700 font-bold"><strong>Price:</strong> ${table.formatted_price || ('₱' + table.price.toFixed(2))}</p>
                </div>
                
                <div class="flex justify-between">
                    <button onclick="openEditTableForm('${table.id}')" class="bg-blue-600 hover:bg-black text-white px-4 py-2 rounded-md transition duration-300">
                        Edit
                    </button>
                    <button onclick="confirmDeleteTable('${table.id}')" class="bg-red-600 hover:bg-black text-white px-4 py-2 rounded-md transition duration-300">
                        Delete
                    </button>
                </div>
            </div>
        `;
        
        tableCardView.appendChild(tableCard);
    });
    
    // Render table view with thumbnail images
    currentCottageTables.forEach(table => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        // Table image thumbnail for table view
        const imageUrl = table.image_url || (table.table_image ? 
            `/static/table_images/${table.table_image}` : 
            '/static/img/default-table.png');
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-10 mr-3">
                        <img class="h-10 w-10 rounded-md object-cover" src="${imageUrl}" alt="Table image">
                    </div>
                    ${table.table_no}
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">${table.capacity} person(s)</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-medium rounded-full ${table.status === 'available' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${table.status}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-green-700 font-bold">${table.formatted_price || ('₱' + table.price.toFixed(2))}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex space-x-2">
                    <button onclick="openEditTableForm('${table.id}')" class="bg-blue-600 hover:bg-black text-white px-3 py-1 rounded text-sm transition duration-300">
                        Edit
                    </button>
                    <button onclick="confirmDeleteTable('${table.id}')" class="bg-red-600 hover:bg-black text-white px-3 py-1 rounded text-sm transition duration-300">
                        Delete
                    </button>
                </div>
            </td>
        `;
        
        tablesTableBody.appendChild(row);
    });
}


// Delete Cottage Functions
function confirmDelete(cottageId) {
    const deleteForm = document.getElementById('deleteForm');
    deleteForm.action = `/cottage/${cottageId}/delete`;
    
    // Store the cottage ID for the delete confirmation
    deleteForm.dataset.cottageId = cottageId;
    
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
}

// Add event listener to the delete form
document.addEventListener('DOMContentLoaded', function() {
    // Existing event listeners...
    
    // Handle cottage delete form submission
    document.getElementById('deleteForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const cottageId = this.dataset.cottageId;
        
        try {
            const response = await fetch(`/cottage/${cottageId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete cottage');
            }
            
            // Redirect to my cottages page on success
            window.location.href = '/my-cottages';
            
        } catch (error) {
            console.error('Error deleting cottage:', error);
            showToast('Error deleting cottage. Please try again.', 'error');
            closeDeleteModal();
        }
    });
});

// Helper function to get CSRF token
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}
// Function to handle removal of individual images from the preview
function removeImage(button) {
    // Get the parent preview container
    const previewElement = button.closest('.relative');
    const previewContainer = document.getElementById('image-previews');
    const previewSection = document.getElementById('preview-container');
    
    // Remove this specific preview
    if (previewElement) {
        previewElement.remove();
    }
    
    // If no more previews remain, hide the preview section
    if (previewContainer.children.length === 0) {
        previewSection.classList.add('hidden');
    }
}

// Preview selected images
function previewImages(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('image-previews');
    const previewSection = document.getElementById('preview-container');
    
    // Clear previous previews
    previewContainer.innerHTML = '';
    
    if (files.length === 0) {
        previewSection.classList.add('hidden');
        return;
    }
    
    previewSection.classList.remove('hidden');
    
    // Create previews for each file
    Array.from(files).forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.createElement('div');
            preview.className = 'relative';
            preview.dataset.fileIndex = index;
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview" class="w-full h-32 object-cover rounded-lg">
                <div class="absolute top-1 right-1">
                    <button type="button" class="bg-red-600 hover:bg-red-700 text-white rounded-full w-6 h-6 flex items-center justify-center" onclick="removeImage(this)">
                        &times;
                    </button>
                </div>
            `;
            previewContainer.appendChild(preview);
        };
        reader.readAsDataURL(file);
    });
}

// Table Form Functions
function openAddTableForm() {
    // Reset form
    document.getElementById('tableForm').reset();
    document.getElementById('editTableId').value = '';
    document.getElementById('tableFormTitle').textContent = 'Add Table';
    document.getElementById('tableFormSubmitBtn').textContent = 'Add Table';
    
    // Show modal
    document.getElementById('tableFormModal').classList.remove('hidden');
}

function openEditTableForm(tableId) {
    // Find table data
    const table = currentCottageTables.find(t => t.id == tableId);
    if (!table) return;
    
    // Fill form with table data
    document.getElementById('table_no').value = table.table_no;
    document.getElementById('capacity').value = table.capacity;
    document.getElementById('price').value = table.price;
    document.getElementById('editTableId').value = tableId;
    
    // Update form title and button
    document.getElementById('tableFormTitle').textContent = 'Edit Table';
    document.getElementById('tableFormSubmitBtn').textContent = 'Update Table';
    
    // Show modal
    document.getElementById('tableFormModal').classList.remove('hidden');
}

function closeTableFormModal() {
    document.getElementById('tableFormModal').classList.add('hidden');
}

// Table Delete Functions
function confirmDeleteTable(tableId) {
    // Create delete table modal if it doesn't exist
    if (!document.getElementById('deleteTableModal')) {
        const modal = document.createElement('div');
        modal.id = 'deleteTableModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden';
        modal.innerHTML = `
            <div class="bg-white p-8 rounded-lg shadow-md w-96 border-2 border-gray-300 relative">
                <h2 class="text-2xl font-bold mb-4 text-gray-800">Confirm Table Deletion</h2>
                <p class="text-gray-600 mb-6">Are you sure you want to delete this table? This action cannot be undone.</p>

                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="closeDeleteTableModal()" class="bg-gray-400 hover:bg-black text-white px-4 py-2 rounded-md">
                        Cancel
                    </button>
                    <button type="button" id="confirmDeleteTableBtn" class="bg-red-600 hover:bg-black text-white px-4 py-2 rounded-md">
                        Delete
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Set up delete button
    const deleteBtn = document.getElementById('confirmDeleteTableBtn');
    deleteBtn.onclick = async () => {
        await deleteTable(tableId);
    };
    
    // Show modal
    document.getElementById('deleteTableModal').classList.remove('hidden');
}

function closeDeleteTableModal() {
    const modal = document.getElementById('deleteTableModal');
    if (modal) modal.classList.add('hidden');
}

async function deleteTable(tableId) {
    try {
        const response = await fetch(`/cottage/${currentCottageId}/delete-table/${tableId}/ajax`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete table');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Refresh tables list
            fetchTables(currentCottageId);
            closeDeleteTableModal();
            showToast('Table deleted successfully!', 'success');
        } else {
            showToast(result.message || 'Error deleting table', 'error');
        }
    } catch (error) {
        console.error('Error deleting table:', error);
        showToast('Error deleting table. Please try again.', 'error');
    }
}

// Helper function to get CSRF token
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

// Toast notification function
function showToast(message, type = 'success') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 p-4 rounded-md shadow-md z-50 ${type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
    toast.innerHTML = message;
    
    // Add to body
    document.body.appendChild(toast);
    
    // Remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    document.getElementById('addTableBtn')?.addEventListener('click', openAddTableForm);

    // Table view toggle functionality
    document.getElementById('tableCardViewBtn')?.addEventListener('click', function() {
        document.getElementById('tableCardView').classList.remove('hidden');
        document.getElementById('tableTableView').classList.add('hidden');
        document.getElementById('tableCardViewBtn').classList.remove('bg-gray-600');
        document.getElementById('tableCardViewBtn').classList.add('bg-blue-600');
        document.getElementById('tableTableViewBtn').classList.remove('bg-blue-600');
        document.getElementById('tableTableViewBtn').classList.add('bg-gray-600');
    });

    document.getElementById('tableTableViewBtn')?.addEventListener('click', function() {
        document.getElementById('tableCardView').classList.add('hidden');
        document.getElementById('tableTableView').classList.remove('hidden');
        document.getElementById('tableTableViewBtn').classList.remove('bg-gray-600');
        document.getElementById('tableTableViewBtn').classList.add('bg-blue-600');
        document.getElementById('tableCardViewBtn').classList.remove('bg-blue-600');
        document.getElementById('tableCardViewBtn').classList.add('bg-gray-600');
    });

    // Cottage view toggle functionality
    document.getElementById('cardViewBtn')?.addEventListener('click', function() {
        document.getElementById('cardView').classList.remove('hidden');
        document.getElementById('tableView').classList.add('hidden');
        document.getElementById('cardViewBtn').classList.remove('bg-gray-600');
        document.getElementById('cardViewBtn').classList.add('bg-blue-600');
        document.getElementById('tableViewBtn').classList.remove('bg-blue-600');
        document.getElementById('tableViewBtn').classList.add('bg-gray-600');
    });

    document.getElementById('tableViewBtn')?.addEventListener('click', function() {
        document.getElementById('cardView').classList.add('hidden');
        document.getElementById('tableView').classList.remove('hidden');
        document.getElementById('tableViewBtn').classList.remove('bg-gray-600');
        document.getElementById('tableViewBtn').classList.add('bg-blue-600');
        document.getElementById('cardViewBtn').classList.remove('bg-blue-600');
        document.getElementById('cardViewBtn').classList.add('bg-gray-600');
    });

    // Handle image file selection for discoveries
    document.getElementById('discovery-images')?.addEventListener('change', previewImages);
    
    // Handle discoveries form submission
    document.getElementById('discoveries-form')?.addEventListener('submit', uploadDiscoveries);

    // Close modals when clicking outside
    window.addEventListener('click', function(e) {
        const deleteModal = document.getElementById('deleteModal');
        if (e.target === deleteModal) {
            closeDeleteModal();
        }
        
        const tablesModal = document.getElementById('tablesModal');
        if (e.target === tablesModal) {
            closeTablesModal();
        }
        
        const tableFormModal = document.getElementById('tableFormModal');
        if (e.target === tableFormModal) {
            closeTableFormModal();
        }
        
        const deleteTableModal = document.getElementById('deleteTableModal');
        if (e.target === deleteTableModal) {
            closeDeleteTableModal();
        }
        
        const discoveriesModal = document.getElementById('discoveriesModal');
        if (e.target === discoveriesModal) {
            closeDiscoveriesModal();
        }
    });

    // Close modals with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDeleteModal();
            closeTablesModal();
            closeTableFormModal();
            closeDeleteTableModal();
            closeDiscoveriesModal();
        }
    });

    // Handle table form submission with price field
    document.getElementById('tableForm')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const tableNo = document.getElementById('table_no').value;
        const capacity = document.getElementById('capacity').value;
        const price = document.getElementById('price').value;
        const tableId = document.getElementById('editTableId').value;
        const tableImage = document.getElementById('table_image').files[0];
        
        const isEdit = tableId !== '';
        const url = isEdit 
            ? `/cottage/${currentCottageId}/edit-table/${tableId}/ajax`
            : `/cottage/${currentCottageId}/add-table/ajax`;
        
        try {
            // Use FormData for file uploads
            const formData = new FormData();
            formData.append('table_no', tableNo);
            formData.append('capacity', capacity);
            formData.append('price', price);
            
            if (tableImage) {
                formData.append('table_image', tableImage);
            }
            
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Failed to save table');
            }
            
            const result = await response.json();
            
            if (result.success) {
                fetchTables(currentCottageId);
                closeTableFormModal();
                showToast(isEdit ? 'Table updated successfully!' : 'Table added successfully!', 'success');
            } else {
                showToast(result.message || 'Error saving table', 'error');
            }
        } catch (error) {
            console.error('Error saving table:', error);
            showToast('Error saving table. Please try again.', 'error');
        }
    });

    // Make sure this code runs after the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get the add table button
    const addTableBtn = document.getElementById('addTableBtn');
    
    if (addTableBtn) {
        addTableBtn.addEventListener('click', function() {
            // Reset form
            document.getElementById('tableForm').reset();
            document.getElementById('editTableId').value = '';
            document.getElementById('tableFormTitle').textContent = 'Add Table';
            
            // Show form modal
            document.getElementById('tableFormModal').classList.remove('hidden');
        });
    }
    
    // Close button functionality
    const closeModalBtn = document.querySelector('#tableFormModal button[onclick="closeTableFormModal()"]');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            document.getElementById('tableFormModal').classList.add('hidden');
        });
    }
});

});