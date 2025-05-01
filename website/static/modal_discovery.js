
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
        container.innerHTML = '<p class="text-gray-500 text-center p-4 col-span-full">No discoveries yet. Add some!</p>';
        return;
    }

    discoveries.forEach(discovery => {
        const card = document.createElement('div');
        card.className = 'border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200';

        card.innerHTML = `
            <div class="relative">
                <img src="${discovery.image_url}" alt="Discovery Image" class="w-full h-48 object-cover">
                <div class="absolute top-0 right-0 p-2">
                    <button onclick="editDiscovery('${discovery.id}', '${discovery.description?.replace(/'/g, "\\'") || ''}')" class="bg-white p-1 rounded-full text-gray-600 hover:text-blue-600 mr-1">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteDiscovery('${discovery.id}')" class="bg-white p-1 rounded-full text-gray-600 hover:text-red-600">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="p-3">
                <p class="text-sm text-gray-700" id="description-${discovery.id}">${discovery.description || 'No description'}</p>
                <p class="text-xs text-gray-400 mt-1">${new Date(discovery.created_at).toLocaleString()}</p>
            </div>
        `;

        container.appendChild(card);
    });
}

// Function to open the edit discovery modal
function editDiscovery(discoveryId, currentDescription) {
    // Create edit modal if it doesn't exist
    let editModal = document.getElementById('editDiscoveryModal');
    
    if (!editModal) {
        editModal = document.createElement('div');
        editModal.id = 'editDiscoveryModal';
        editModal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50';
        editModal.innerHTML = `
            <div class="bg-white rounded-lg p-6 w-11/12 max-w-md">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Edit Discovery Description</h3>
                <form id="edit-discovery-form">
                    <input type="hidden" id="edit-discovery-id">
                    <div class="mb-4">
                        <label for="edit-description" class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea id="edit-description" name="description" rows="3" class="w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"></textarea>
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button type="button" id="cancel-edit" class="py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                        <button type="submit" class="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700">Save Changes</button>
                    </div>
                </form>
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


window.openDiscoveryModal = openDiscoveryModal;
window.closeDiscoveryModal = closeDiscoveryModal;
window.deleteDiscovery = deleteDiscovery;
window.editDiscovery = editDiscovery;