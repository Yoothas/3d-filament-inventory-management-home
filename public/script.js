let filaments = [];
let editingFilamentId = null;

// DOM Elements
const filamentsGrid = document.getElementById('filamentsGrid');
const addFilamentBtn = document.getElementById('addFilamentBtn');
const filamentModal = document.getElementById('filamentModal');
const filamentForm = document.getElementById('filamentForm');
const modalTitle = document.getElementById('modalTitle');
const searchInput = document.getElementById('searchInput');
const materialFilter = document.getElementById('materialFilter');

// Event Listeners
document.addEventListener('DOMContentLoaded', loadFilaments);
addFilamentBtn.addEventListener('click', () => openModal());
filamentForm.addEventListener('submit', handleFormSubmit);
searchInput.addEventListener('input', filterFilaments);
materialFilter.addEventListener('change', filterFilaments);

// Modal controls
document.querySelector('.close').addEventListener('click', closeModal);
window.addEventListener('click', (e) => {
    if (e.target === filamentModal) {
        closeModal();
    }
});

// Load filaments from server
async function loadFilaments() {
    try {
        const response = await fetch('/api/filaments');
        filaments = await response.json();
        renderFilaments();
        updateStats();
    } catch (error) {
        console.error('Error loading filaments:', error);
        showError('Failed to load filaments');
    }
}

// Render filaments
function renderFilaments(filamentsToRender = filaments) {
    if (filamentsToRender.length === 0) {
        filamentsGrid.innerHTML = `
            <div class="empty-state">
                <h3>No filaments found</h3>
                <p>Add your first filament spool to get started!</p>
            </div>
        `;
        return;
    }

    filamentsGrid.innerHTML = filamentsToRender.map(filament => {
        const usagePercent = ((filament.weight - filament.remainingWeight) / filament.weight) * 100;
        const remainingPercent = (filament.remainingWeight / filament.weight) * 100;
        const isLowStock = remainingPercent < 20;
        
        return `
            <div class="filament-card ${isLowStock ? 'low-stock' : ''}">
                <div class="filament-header">
                    <div class="filament-title">
                        <div class="filament-brand">${escapeHtml(filament.brand)}</div>
                        <span class="filament-material">${filament.material}</span>
                    </div>
                </div>
                
                <div class="filament-color">${escapeHtml(filament.color)}</div>
                
                <div class="filament-details">
                    <div class="detail-item">
                        <span class="detail-label">Diameter:</span>
                        <span class="detail-value">${filament.diameter}mm</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Cost:</span>
                        <span class="detail-value">$${filament.cost ? filament.cost.toFixed(2) : '0.00'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Purchase:</span>
                        <span class="detail-value">${filament.purchaseDate ? new Date(filament.purchaseDate).toLocaleDateString() : 'N/A'}</span>
                    </div>
                </div>
                
                <div class="weight-progress">
                    <div class="progress-label">
                        <span>Remaining: ${filament.remainingWeight}g</span>
                        <span>Original: ${filament.weight}g</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${remainingPercent}%"></div>
                    </div>
                </div>
                
                ${filament.notes ? `<div class="filament-notes">"${escapeHtml(filament.notes)}"</div>` : ''}
                
                <div class="filament-actions">
                    <button class="btn btn-edit" onclick="editFilament('${filament.id}')">Edit</button>
                    <button class="btn btn-danger" onclick="deleteFilament('${filament.id}')">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

// Update statistics
function updateStats() {
    const totalSpools = filaments.length;
    const totalWeight = filaments.reduce((sum, f) => sum + f.weight, 0);
    const remainingWeight = filaments.reduce((sum, f) => sum + f.remainingWeight, 0);
    
    document.getElementById('totalSpools').textContent = totalSpools;
    document.getElementById('totalWeight').textContent = `${totalWeight}g`;
    document.getElementById('remainingWeight').textContent = `${remainingWeight}g`;
}

// Filter filaments
function filterFilaments() {
    const searchTerm = searchInput.value.toLowerCase();
    const materialFilter = document.getElementById('materialFilter').value;
    
    const filtered = filaments.filter(filament => {
        const matchesSearch = !searchTerm || 
            filament.brand.toLowerCase().includes(searchTerm) ||
            filament.material.toLowerCase().includes(searchTerm) ||
            filament.color.toLowerCase().includes(searchTerm);
            
        const matchesMaterial = !materialFilter || filament.material === materialFilter;
        
        return matchesSearch && matchesMaterial;
    });
    
    renderFilaments(filtered);
}

// Modal functions
function openModal(filamentId = null) {
    editingFilamentId = filamentId;
    
    if (filamentId) {
        const filament = filaments.find(f => f.id === filamentId);
        modalTitle.textContent = 'Edit Filament';
        populateForm(filament);
    } else {
        modalTitle.textContent = 'Add New Filament';
        filamentForm.reset();
        // Set default remaining weight to match original weight
        document.getElementById('weight').addEventListener('input', function() {
            const remainingWeightInput = document.getElementById('remainingWeight');
            if (!remainingWeightInput.value) {
                remainingWeightInput.value = this.value;
            }
        });
    }
    
    filamentModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    filamentModal.style.display = 'none';
    document.body.style.overflow = 'auto';
    editingFilamentId = null;
    filamentForm.reset();
}

// Populate form with filament data
function populateForm(filament) {
    document.getElementById('brand').value = filament.brand;
    document.getElementById('material').value = filament.material;
    document.getElementById('color').value = filament.color;
    document.getElementById('weight').value = filament.weight;
    document.getElementById('remainingWeight').value = filament.remainingWeight;
    document.getElementById('diameter').value = filament.diameter;
    document.getElementById('purchaseDate').value = filament.purchaseDate || '';
    document.getElementById('cost').value = filament.cost || '';
    document.getElementById('notes').value = filament.notes || '';
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(filamentForm);
    const filamentData = Object.fromEntries(formData);
    
    // Ensure remaining weight doesn't exceed original weight
    if (parseFloat(filamentData.remainingWeight) > parseFloat(filamentData.weight)) {
        showError('Remaining weight cannot exceed original weight');
        return;
    }
    
    try {
        let response;
        if (editingFilamentId) {
            response = await fetch(`/api/filaments/${editingFilamentId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(filamentData),
            });
        } else {
            // Set remaining weight to original weight if not specified
            if (!filamentData.remainingWeight) {
                filamentData.remainingWeight = filamentData.weight;
            }
            
            response = await fetch('/api/filaments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(filamentData),
            });
        }
        
        if (response.ok) {
            closeModal();
            loadFilaments();
            showSuccess(editingFilamentId ? 'Filament updated successfully' : 'Filament added successfully');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to save filament');
        }
    } catch (error) {
        console.error('Error saving filament:', error);
        showError('Failed to save filament');
    }
}

// Edit filament
function editFilament(id) {
    openModal(id);
}

// Delete filament
async function deleteFilament(id) {
    const filament = filaments.find(f => f.id === id);
    if (!confirm(`Are you sure you want to delete ${filament.brand} ${filament.color} ${filament.material}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/filaments/${id}`, {
            method: 'DELETE',
        });
        
        if (response.ok) {
            loadFilaments();
            showSuccess('Filament deleted successfully');
        } else {
            const error = await response.json();
            showError(error.error || 'Failed to delete filament');
        }
    } catch (error) {
        console.error('Error deleting filament:', error);
        showError('Failed to delete filament');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    // Simple error display - you could enhance this with a proper notification system
    alert('Error: ' + message);
}

function showSuccess(message) {
    // Simple success display - you could enhance this with a proper notification system
    alert('Success: ' + message);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape to close modal
    if (e.key === 'Escape' && filamentModal.style.display === 'block') {
        closeModal();
    }
    
    // Ctrl/Cmd + N to add new filament
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        openModal();
    }
});