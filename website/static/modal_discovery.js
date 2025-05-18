let currentCottageId = null;   
let currentDiscoveries = [];   

// Function to show alerts
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    const alertDiv = document.createElement('div');
    alertDiv.className = type === 'success' 
        ? 'bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4' 
        : 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4';
    alertDiv.innerHTML = `<p>${message}</p>`;
    alertContainer.appendChild(alertDiv);
    
    
    setTimeout(() => {
        alertContainer.removeChild(alertDiv);
    }, 5000);
}


function renderDiscoveries(discoveries) {
    const container = document.getElementById('discoveries-grid');
    container.innerHTML = '';

    if (discoveries.length === 0) {
        container.innerHTML = `
            <div class="col-span-full bg-white rounded-xl shadow-sm p-8 text-center">
                <div class="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <i class="fas fa-camera-retro text-2xl text-gray-400"></i>
                </div>
                <h3 class="text-xl font-medium text-gray-900 mb-2">No Discoveries Yet</h3>
                <p class="text-gray-500 mb-6">Start by adding your first discovery to showcase your cottage.</p>
            </div>`;
        return;
    }

    discoveries.forEach(discovery => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100 hover:shadow-md transition-shadow duration-200';

        card.innerHTML = `
            <div class="relative">
                <img src="${discovery.image_url}" alt="Discovery Image" class="w-full h-48 object-cover">
                <div class="absolute top-4 right-4 flex space-x-2">
                    <button onclick="editDiscovery('${discovery.id}', '${discovery.description?.replace(/'/g, "\\'") || ''}')" 
                            class="inline-flex items-center justify-center px-3 py-1 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors duration-200">
                        <i class="fas fa-edit mr-1"></i> Edit
                    </button>
                    <button onclick="deleteDiscovery('${discovery.id}')" 
                            class="inline-flex items-center justify-center px-3 py-1 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors duration-200">
                        <i class="fas fa-trash-alt mr-1"></i> Delete
                    </button>
                </div>
            </div>
            <div class="p-6">
                <p class="text-gray-700 mb-2" id="description-${discovery.id}">${discovery.description || 'No description'}</p>
                <p class="text-sm text-gray-500 flex items-center">
                    <i class="fas fa-clock mr-2 text-gray-400"></i>
                    ${new Date(discovery.created_at).toLocaleString()}
                </p>
            </div>
        `;

        container.appendChild(card);
    });
}

// Function to open the edit discovery modal
function editDiscovery(discoveryId, currentDescription) {
    let editModal = document.getElementById('editDiscoveryModal');
    
    if (!editModal) {
        editModal = document.createElement('div');
        editModal.id = 'editDiscoveryModal';
        editModal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden';
        editModal.innerHTML = `
            <div class="bg-white rounded-xl shadow-lg max-w-md w-full mx-4">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-2xl font-bold text-gray-900">Edit Discovery</h2>
                        <button type="button" onclick="document.getElementById('editDiscoveryModal').classList.add('hidden')" 
                                class="text-gray-400 hover:text-gray-600 transition-colors duration-200">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <form id="edit-discovery-form">
                        <input type="hidden" id="edit-discovery-id">
                        <div class="mb-6">
                            <label for="edit-description" class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                            <textarea id="edit-description" name="description" rows="4" 
                                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"></textarea>
                        </div>
                        <div class="flex justify-end space-x-4 pt-4 border-t border-gray-200">
                            <button type="button" id="cancel-edit" 
                                    class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200">
                                Cancel
                            </button>
                            <button type="submit" 
                                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200">
                                Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(editModal);
        
        // Add event listeners
        document.getElementById('cancel-edit').addEventListener('click', () => {
            editModal.classList.add('hidden');
        });
        
        document.getElementById('edit-discovery-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const discoveryId = document.getElementById('edit-discovery-id').value;
            const description = document.getElementById('edit-description').value;
            
            try {
                const formData = new FormData();
                formData.append('description', description);
                
                const response = await fetch(`/discoveries/cottage/edit-discovery/${discoveryId}`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Update the description in the UI
                    const descriptionElement = document.getElementById(`description-${discoveryId}`);
                    if (descriptionElement) {
                        descriptionElement.textContent = description || 'No description';
                    }
                    
                    // Update in our current discoveries array
                    const discoveryIndex = currentDiscoveries.findIndex(d => d.id === discoveryId);
                    if (discoveryIndex !== -1) {
                        currentDiscoveries[discoveryIndex].description = description;
                    }
                    
                    showAlert('success', 'Description updated successfully');
                    editModal.classList.add('hidden');
                } else {
                    showAlert('error', data.message || 'Failed to update description');
                }
            } catch (error) {
                console.error('Error updating discovery:', error);
                showAlert('error', 'Error updating discovery: ' + error.message);
            }
        });
    }
    
    // Set values and show modal
    document.getElementById('edit-discovery-id').value = discoveryId;
    document.getElementById('edit-description').value = currentDescription || '';
    editModal.classList.remove('hidden');
}

// Function to initialize the file input preview
function initFilePreview() {
    const fileInput = document.getElementById('discovery-images');
    const fileInputParent = fileInput.parentElement;
    
    // Create file preview container if it doesn't exist
    let filePreview = document.getElementById('file-preview');
    if (!filePreview) {
        filePreview = document.createElement('div');
        filePreview.id = 'file-preview';
        filePreview.className = 'flex flex-wrap gap-2 mt-2';
        
        // Insert after the file input
        fileInputParent.after(filePreview);
    }
    
    fileInput.addEventListener('change', function() {
        filePreview.innerHTML = '';
        
        if (this.files.length > 0) {
            Array.from(this.files).forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewDiv = document.createElement('div');
                    previewDiv.className = 'relative w-24 h-24 border rounded overflow-hidden';
                    
                    // Create image preview
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.className = 'w-full h-full object-cover';
                    img.alt = `Preview ${index + 1}`;
                    
                    // Create remove button
                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'absolute top-0 right-0 bg-white rounded-full p-1 shadow-sm text-red-600 hover:text-red-800';
                    removeBtn.innerHTML = '<i class="fas fa-times"></i>';
                    
                    // Add elements to preview div
                    previewDiv.appendChild(img);
                    previewDiv.appendChild(removeBtn);
                    filePreview.appendChild(previewDiv);
                    
                    // Handle remove button click
                    // Note: this only removes the preview, not from the file input
                    removeBtn.addEventListener('click', function() {
                        previewDiv.remove();
                    });
                }
                reader.readAsDataURL(file);
            });
        }
    });
}

// Function to load cottage discoveries
function loadDiscoveries(cottageId) {
    const grid = document.getElementById("discoveries-grid");
    const loading = document.getElementById("discoveries-loading") || document.createElement("div");
    
    if (!document.getElementById("discoveries-loading")) {
        loading.id = "discoveries-loading";
        loading.className = "text-center py-4";
        loading.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Loading discoveries...';
        grid.parentNode.insertBefore(loading, grid);
    }

    grid.innerHTML = "";
    loading.classList.remove("hidden");

    fetch(`/discoveries/cottage/${cottageId}/discoveries/data`)
        .then(res => res.json())
        .then(data => {
            loading.classList.add("hidden");
            currentDiscoveries = data.discoveries || [];

            if (data.success && data.discoveries.length > 0) {
                renderDiscoveries(data.discoveries);
            } else {
                grid.innerHTML = `<p class="text-gray-500 text-center col-span-3">No discoveries found.</p>`;
            }
        })
        .catch(error => {
            console.error("Error loading discoveries:", error);
            loading.classList.add("hidden");
            grid.innerHTML = `<p class="text-red-500 text-center">Failed to load discoveries.</p>`;
        });
}

// Function to open the discovery modal
function openDiscoveryModal(cottageId) {
    console.log("Opening discovery modal for cottage:", cottageId);
    currentCottageId = cottageId;

    // Set cottage ID in form
    const input = document.getElementById('cottage-id');
    if (input) {
        input.value = cottageId;
    } else {
        console.error("Cottage ID input not found!");
    }

    // Show the discoveries section
    const discoveriesSection = document.getElementById('discoveries-section');
    if (discoveriesSection) {
        discoveriesSection.classList.remove('hidden');
    } else {
        console.error("Discoveries section element not found!");
    }

    // Load discoveries for this cottage
    loadDiscoveries(cottageId);
}
// Function to close the discovery modal
function closeDiscoveryModal() {
    const modal = document.getElementById('discoveryModal');
    if (modal) {
        modal.classList.add('hidden');
    }
    
    // Reset form
    const form = document.getElementById('discoveries-form');
    if (form) {
        form.reset();
    }
    
    // Clear file preview
    const filePreview = document.getElementById('file-preview');
    if (filePreview) {
        filePreview.innerHTML = '';
    }
    
    // Hide edit modal if it exists
    const editModal = document.getElementById('editDiscoveryModal');
    if (editModal) {
        editModal.classList.add('hidden');
    }
}

// Initialize the discovery functionality
document.addEventListener("DOMContentLoaded", function() {
    // Initialize file preview
    initFilePreview();
    
    // Add event listener to manage discoveries buttons
    document.querySelectorAll('.discovery-modal-trigger').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const cottageId = this.getAttribute('data-cottage-id');
            openDiscoveryModal(cottageId);
        });
    });
    
    // Close modal when clicking the close button
    const closeButton = document.getElementById('close-discovery-modal');
    if (closeButton) {
        closeButton.addEventListener('click', closeDiscoveryModal);
    }
    
    // Close modal when clicking cancel button
    const cancelButton = document.getElementById('cancel-discovery-upload');
    if (cancelButton) {
        cancelButton.addEventListener('click', closeDiscoveryModal);
    }
    
    // Setup the discovery form submission
    const discoveryForm = document.getElementById('discoveries-form');
    if (discoveryForm) {
        discoveryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const fileInput = document.getElementById('discovery-images');
            
            // Check if files are selected
            if (fileInput && fileInput.files.length > 0) {
                try {
                    // Show loading indicator
                    const submitBtn = this.querySelector('button[type="submit"]');
                    const originalBtnText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Uploading...';
                    
                    // Add each file to formData
                    for (let i = 0; i < fileInput.files.length; i++) {
                        formData.append('discovery_images[]', fileInput.files[i]);
                    }
                    
                    const response = await fetch('/discoveries/cottage/add-discoveries', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    // Restore button
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                    
                    if (data.success) {
                        showAlert('success', data.message || 'Discoveries uploaded successfully');
                        
                        loadDiscoveries(currentCottageId);
                        
                        discoveryForm.reset();
                        
                        document.getElementById('file-preview').innerHTML = '';
                    } else {
                        showAlert('error', data.message || 'Failed to upload discoveries');
                    }
                } catch (error) {
                    console.error('Error uploading discoveries:', error);
                    showAlert('error', 'Error uploading discoveries: ' + error.message);
                }
            } else {
                showAlert('error', 'Please select at least one image');
            }
        });
    }
    
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDiscoveryModal();
        }
    });
});

// Add a delete confirmation modal
function deleteDiscovery(discoveryId) {
    let deleteModal = document.getElementById('deleteDiscoveryModal');
    
    if (!deleteModal) {
        deleteModal = document.createElement('div');
        deleteModal.id = 'deleteDiscoveryModal';
        deleteModal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center hidden';
        deleteModal.innerHTML = `
            <div class="bg-white rounded-xl shadow-lg max-w-md w-full mx-4">
                <div class="p-6">
                    <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                        <i class="fas fa-exclamation-triangle text-xl text-red-600"></i>
                    </div>
                    <h2 class="text-2xl font-bold text-center text-gray-900 mb-2">Confirm Deletion</h2>
                    <p class="text-gray-600 text-center mb-6">Are you sure you want to delete this discovery? This action cannot be undone.</p>

                    <div class="flex justify-end space-x-4">
                        <button type="button" onclick="document.getElementById('deleteDiscoveryModal').classList.add('hidden')" 
                                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200">
                            Cancel
                        </button>
                        <button type="button" id="confirmDeleteDiscoveryBtn" 
                                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200">
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(deleteModal);
        
        // Add event listener for delete confirmation
        document.getElementById('confirmDeleteDiscoveryBtn').addEventListener('click', async () => {
            try {
                const response = await fetch(`/discoveries/cottage/delete-discovery/${discoveryId}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Remove from current discoveries array
                    currentDiscoveries = currentDiscoveries.filter(d => d.id !== discoveryId);
                    // Re-render discoveries
                    renderDiscoveries(currentDiscoveries);
                    showAlert('success', 'Discovery deleted successfully');
                    deleteModal.classList.add('hidden');
                } else {
                    showAlert('error', data.message || 'Failed to delete discovery');
                }
            } catch (error) {
                console.error('Error deleting discovery:', error);
                showAlert('error', 'Error deleting discovery: ' + error.message);
            }
        });
    }
    
    deleteModal.classList.remove('hidden');
}

window.openDiscoveryModal = openDiscoveryModal;
window.closeDiscoveryModal = closeDiscoveryModal;
window.deleteDiscovery = deleteDiscovery;
window.editDiscovery = editDiscovery;