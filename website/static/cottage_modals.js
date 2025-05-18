// Global variables
let currentCottageId = null;
let currentCottageTables = [];
let currentDiscoveries = [];

// Delete Cottage Functions
function confirmDelete(cottageId) {
    const deleteForm = document.getElementById('deleteForm');
    if (deleteForm) {
        deleteForm.action = `/delete-cottage/${cottageId}`;
        document.getElementById('deleteModal')?.classList.remove('hidden');
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.add('hidden');
}

// Tables Modal Functions
async function openTablesModal(cottageId, cottageNo) {
    currentCottageId = cottageId;
    const modalCottageNo = document.getElementById('modalCottageNo');
    const tablesModal = document.getElementById('tablesModal');
    const tablesLoading = document.getElementById('tablesLoading');
    const tablesContent = document.getElementById('tablesContent');
    
    if (modalCottageNo) modalCottageNo.textContent = cottageNo;
    if (tablesModal) tablesModal.classList.remove('hidden');
    if (tablesLoading) tablesLoading.classList.remove('hidden');
    if (tablesContent) tablesContent.classList.add('hidden');
    
    await fetchTables(cottageId);
}

function closeTablesModal() {
    const modal = document.getElementById('tablesModal');
    if (modal) {
        modal.classList.add('hidden');
        currentCottageId = null;
        currentCottageTables = [];
    }
}

async function fetchTables(cottageId) {
    try {
        const response = await fetch(`/cottage/${cottageId}/tables/data`);
        if (!response.ok) throw new Error('Failed to fetch tables');
        
        const data = await response.json();
        currentCottageTables = data.tables || [];
        
        const modalCottageNo = document.getElementById('modalCottageNo');
        if (modalCottageNo) {
            modalCottageNo.textContent += ` (${currentCottageTables.length} tables)`;
        }
        
        renderTables();
        
        const tablesLoading = document.getElementById('tablesLoading');
        const tablesContent = document.getElementById('tablesContent');
        if (tablesLoading) tablesLoading.classList.add('hidden');
        if (tablesContent) tablesContent.classList.remove('hidden');
        
    } catch (error) {
        console.error("Error loading tables:", error);
        showToast("Error loading tables. Please try again.", "error");
        
        const tablesLoading = document.getElementById('tablesLoading');
        const tablesContent = document.getElementById('tablesContent');
        const noTablesMessage = document.getElementById('noTablesMessage');
        
        if (tablesLoading) tablesLoading.classList.add('hidden');
        if (tablesContent) tablesContent.classList.remove('hidden');
        if (noTablesMessage) {
            noTablesMessage.classList.remove('hidden');
            noTablesMessage.innerHTML = `
                <h3 class="text-xl font-medium text-red-700 mb-4">Error Loading Tables</h3>
                <p class="text-gray-600 mb-4">There was an error loading the tables. Please try again.</p>
            `;
        }
    }
}

// Render Tables Function
function renderTables() {
    const noTablesMessage = document.getElementById('noTablesMessage');
    const tableCardView = document.getElementById('tableCardView');
    const tableTableView = document.getElementById('tableTableView');
    const tablesTableBody = document.getElementById('tablesTableBody');
    
    if (!currentCottageTables.length) {
        if (noTablesMessage) noTablesMessage.classList.remove('hidden');
        if (tableCardView) tableCardView.classList.add('hidden');
        if (tableTableView) tableTableView.classList.add('hidden');
        return;
    }
    
    if (noTablesMessage) noTablesMessage.classList.add('hidden');
    
    // Clear existing content
    if (tableCardView) tableCardView.innerHTML = '';
    if (tablesTableBody) tablesTableBody.innerHTML = '';
    
    // Render both views
    currentCottageTables.forEach(table => {
        // Render card view
        if (tableCardView) {
            const card = createTableCard(table);
            tableCardView.appendChild(card);
        }
        
        // Render table view
        if (tablesTableBody) {
            const row = createTableRow(table);
            tablesTableBody.appendChild(row);
        }
    });
    
    // Show the active view (default to card view)
    const tableCardViewBtn = document.getElementById('tableCardViewBtn');
    const tableTableViewBtn = document.getElementById('tableTableViewBtn');
    
    if (tableCardViewBtn && tableTableViewBtn) {
        const isTableViewActive = tableTableViewBtn.classList.contains('bg-blue-600');
        if (isTableViewActive) {
            if (tableCardView) tableCardView.classList.add('hidden');
            if (tableTableView) tableTableView.classList.remove('hidden');
        } else {
            if (tableCardView) tableCardView.classList.remove('hidden');
            if (tableTableView) tableTableView.classList.add('hidden');
        }
    }
}

function createTableCard(table) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100 hover:shadow-md transition-shadow duration-200';
    
    const imageUrl = table.image_url || (table.table_image ? 
        `/static/table_images/${table.table_image}` : 
        '/static/img/default-table.png');
    
    card.innerHTML = `
        <div class="relative h-48 bg-gray-100">
            <img src="${imageUrl}" alt="Table ${table.table_no}" class="w-full h-full object-cover">
            <span class="absolute top-2 right-2 px-3 py-1 rounded-full text-sm font-medium ${
                table.status === 'available' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }">
                ${table.status}
            </span>
        </div>
        <div class="p-6">
            <div class="flex justify-between items-start mb-4">
                <h3 class="text-xl font-semibold text-gray-900">Table ${table.table_no}</h3>
            </div>
            
            <div class="mb-4">
                <p class="text-gray-600 mb-2 flex items-center">
                    <i class="fas fa-users mr-2 text-gray-400"></i>
                    <strong>Capacity:</strong> ${table.capacity} person(s)
                </p>
                <p class="text-green-700 font-bold flex items-center">
                    <i class="fas fa-tag mr-2 text-gray-400"></i>
                    <strong>Price:</strong> ${table.formatted_price || ('₱' + table.price.toFixed(2))}
                </p>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <button type="button" onclick="openEditTableForm('${table.id}')" 
                        class="inline-flex items-center justify-center px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors duration-200">
                    <i class="fas fa-edit mr-2"></i> Edit
                </button>
                <button type="button" onclick="confirmDeleteTable('${table.id}')" 
                        class="inline-flex items-center justify-center px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors duration-200">
                    <i class="fas fa-trash-alt mr-2"></i> Delete
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function createTableRow(table) {
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50';
    
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
            <span class="px-2 py-1 text-xs font-medium rounded-full ${
                table.status === 'available' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }">
                ${table.status}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-green-700 font-bold">${table.formatted_price || ('₱' + table.price.toFixed(2))}</td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex space-x-2">
                <button type="button" onclick="openEditTableForm('${table.id}')" 
                        class="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors duration-200">
                    <i class="fas fa-edit mr-1"></i> Edit
                </button>
                <button type="button" onclick="confirmDeleteTable('${table.id}')" 
                        class="inline-flex items-center px-3 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100 transition-colors duration-200">
                    <i class="fas fa-trash-alt mr-1"></i> Delete
                </button>
            </div>
        </td>
    `;
    
    return row;
}

// Table Form Functions
function openAddTableForm() {
    const form = document.getElementById('tableForm');
    const title = document.getElementById('tableFormTitle');
    const submitBtn = document.getElementById('tableFormSubmitBtn');
    const modal = document.getElementById('tableFormModal');
    
    if (form && title && submitBtn && modal) {
        form.reset();
        document.getElementById('editTableId').value = '';
        title.textContent = 'Add Table';
        submitBtn.textContent = 'Add Table';
        modal.classList.remove('hidden');
    }
}

function openEditTableForm(tableId) {
    const table = currentCottageTables.find(t => t.id == tableId);
    if (!table) return;
    
    const form = document.getElementById('tableForm');
    const title = document.getElementById('tableFormTitle');
    const submitBtn = document.getElementById('tableFormSubmitBtn');
    const modal = document.getElementById('tableFormModal');
    
    if (form && title && submitBtn && modal) {
        document.getElementById('table_no').value = table.table_no;
        document.getElementById('capacity').value = table.capacity;
        document.getElementById('price').value = table.price;
        document.getElementById('editTableId').value = tableId;
        
        title.textContent = 'Edit Table';
        submitBtn.textContent = 'Update Table';
        
        modal.classList.remove('hidden');
    }
}

function closeTableFormModal() {
    const modal = document.getElementById('tableFormModal');
    const form = document.getElementById('tableForm');
    
    if (modal) modal.classList.add('hidden');
    if (form) form.reset();
}

// Table Delete Functions
function confirmDeleteTable(tableId) {
    const modal = document.getElementById('deleteTableModal') || createDeleteTableModal();
    const deleteBtn = document.getElementById('confirmDeleteTableBtn');
    
    if (deleteBtn) {
        deleteBtn.onclick = async () => {
            await deleteTable(tableId);
        };
    }
    
    modal.classList.remove('hidden');
}

function createDeleteTableModal() {
    const modal = document.createElement('div');
    modal.id = 'deleteTableModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden';
    modal.innerHTML = `
        <div class="bg-white rounded-xl shadow-lg max-w-md w-full mx-4">
            <div class="p-6">
                <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                    <i class="fas fa-exclamation-triangle text-xl text-red-600"></i>
                </div>
                <h2 class="text-2xl font-bold text-center text-gray-900 mb-2">Confirm Deletion</h2>
                <p class="text-gray-600 text-center mb-6">Are you sure you want to delete this table? This action cannot be undone.</p>

                <div class="flex justify-end space-x-4">
                    <button type="button" onclick="closeDeleteTableModal()" 
                            class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200">
                        Cancel
                    </button>
                    <button type="button" id="confirmDeleteTableBtn" 
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                        Delete
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    return modal;
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
        
        if (!response.ok) throw new Error('Failed to delete table');
        
        const result = await response.json();
        
        if (result.success) {
            await fetchTables(currentCottageId);
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

// Helper Functions
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 p-4 rounded-md shadow-md z-50 ${
        type === 'error' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
    }`;
    toast.innerHTML = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize view toggles for both cottage and table views
    initializeViewToggles();
    
    // Initialize table form
    const tableForm = document.getElementById('tableForm');
    if (tableForm) {
        tableForm.addEventListener('submit', handleTableFormSubmit);
    }
    
    // Initialize add table button
    const addTableBtn = document.getElementById('addTableBtn');
    if (addTableBtn) {
        addTableBtn.addEventListener('click', openAddTableForm);
    }
    
    // Close modals when clicking outside
    initializeModalCloseHandlers();
});

// Initialize view toggles for both cottage and table views
function initializeViewToggles() {
    // Cottage view toggles
    const cardViewBtn = document.getElementById('cardViewBtn');
    const tableViewBtn = document.getElementById('tableViewBtn');
    const cardView = document.getElementById('cardView');
    const tableView = document.getElementById('tableView');

    if (cardViewBtn && tableViewBtn) {
        function setActiveCottageView(view) {
            if (view === 'card') {
                cardView.classList.remove('hidden');
                tableView.classList.add('hidden');
                cardViewBtn.classList.remove('bg-gray-100', 'text-gray-700');
                cardViewBtn.classList.add('bg-blue-600', 'text-white');
                tableViewBtn.classList.remove('bg-blue-600', 'text-white');
                tableViewBtn.classList.add('bg-gray-100', 'text-gray-700');
            } else {
                cardView.classList.add('hidden');
                tableView.classList.remove('hidden');
                tableViewBtn.classList.remove('bg-gray-100', 'text-gray-700');
                tableViewBtn.classList.add('bg-blue-600', 'text-white');
                cardViewBtn.classList.remove('bg-blue-600', 'text-white');
                cardViewBtn.classList.add('bg-gray-100', 'text-gray-700');
            }
        }

        // Set initial cottage view
        setActiveCottageView('card');

        cardViewBtn.addEventListener('click', () => setActiveCottageView('card'));
        tableViewBtn.addEventListener('click', () => setActiveCottageView('table'));
    }

    // Table view toggles
    const tableCardViewBtn = document.getElementById('tableCardViewBtn');
    const tableTableViewBtn = document.getElementById('tableTableViewBtn');
    const tableCardView = document.getElementById('tableCardView');
    const tableTableView = document.getElementById('tableTableView');

    if (tableCardViewBtn && tableTableViewBtn) {
        function setActiveTableView(view) {
            if (view === 'card') {
                tableCardView.classList.remove('hidden');
                tableTableView.classList.add('hidden');
                tableCardViewBtn.classList.remove('bg-gray-100', 'text-gray-700');
                tableCardViewBtn.classList.add('bg-blue-600', 'text-white');
                tableTableViewBtn.classList.remove('bg-blue-600', 'text-white');
                tableTableViewBtn.classList.add('bg-gray-100', 'text-gray-700');
            } else {
                tableCardView.classList.add('hidden');
                tableTableView.classList.remove('hidden');
                tableTableViewBtn.classList.remove('bg-gray-100', 'text-gray-700');
                tableTableViewBtn.classList.add('bg-blue-600', 'text-white');
                tableCardViewBtn.classList.remove('bg-blue-600', 'text-white');
                tableCardViewBtn.classList.add('bg-gray-100', 'text-gray-700');
            }
        }

        // Set initial table view
        setActiveTableView('card');

        tableCardViewBtn.addEventListener('click', () => setActiveTableView('card'));
        tableTableViewBtn.addEventListener('click', () => setActiveTableView('table'));
    }
}

// Initialize modal close handlers
function initializeModalCloseHandlers() {
    // Close modals when clicking outside
    window.addEventListener('click', function(e) {
        const modals = {
            'deleteModal': closeDeleteModal,
            'tablesModal': closeTablesModal,
            'tableFormModal': closeTableFormModal,
            'deleteTableModal': closeDeleteTableModal
        };
        
        for (const [modalId, closeFunction] of Object.entries(modals)) {
            const modal = document.getElementById(modalId);
            if (modal && e.target === modal) {
                closeFunction();
            }
        }
    });
    
    // Close modals with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDeleteModal();
            closeTablesModal();
            closeTableFormModal();
            closeDeleteTableModal();
        }
    });
}

// Handle table form submission
async function handleTableFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const tableId = document.getElementById('editTableId').value;
    const isEdit = tableId !== '';
    
    try {
        const url = isEdit 
            ? `/cottage/${currentCottageId}/edit-table/${tableId}/ajax`
            : `/cottage/${currentCottageId}/add-table/ajax`;
        
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Failed to save table');
        
        const result = await response.json();
        
        if (result.success) {
            await fetchTables(currentCottageId);
            closeTableFormModal();
            showToast(isEdit ? 'Table updated successfully!' : 'Table added successfully!', 'success');
        } else {
            showToast(result.message || 'Error saving table', 'error');
        }
    } catch (error) {
        console.error('Error saving table:', error);
        showToast('Error saving table. Please try again.', 'error');
    }
}