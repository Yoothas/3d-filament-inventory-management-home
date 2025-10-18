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
const sortBySelect = document.getElementById('sortBy');
const darkModeToggle = document.getElementById('darkModeToggle');
const refreshBtn = document.getElementById('refreshBtn');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadFilaments();
    initializeDarkMode();
    initializeAutoRefresh();
});
addFilamentBtn.addEventListener('click', () => openModal());
filamentForm.addEventListener('submit', handleFormSubmit);
searchInput.addEventListener('input', filterFilaments);
materialFilter.addEventListener('change', filterFilaments);
sortBySelect.addEventListener('change', filterFilaments);
darkModeToggle.addEventListener('click', toggleDarkMode);
if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
        if (filamentModal.style.display !== 'block') {
            loadFilaments();
        }
    });
}

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
                        <div class="filament-brand">${escapeHtml(filament.color)}</div>
                        <span class="filament-material">${filament.material}</span>
                    </div>
                </div>
                
                <div class="filament-color">${escapeHtml(filament.brand)}</div>
                
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
                
                ${filament.printHistory && filament.printHistory.length > 0 ? `
                    <div class="print-history">
                        <strong>Recent Prints:</strong>
                        <div class="history-items">
                            ${filament.printHistory.slice(-3).map(print => `
                                <div class="history-item">
                                    <span class="history-job">${escapeHtml(print.printJob)}</span>
                                    <span class="history-usage">-${print.usedWeight}g</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="filament-actions">
                    <button class="btn btn-edit" onclick="editFilament('${filament.id}')">Edit</button>
                    ${filament.remainingWeight <= 0 ? 
                        `<button class="btn btn-warning" onclick="archiveFilament('${filament.id}', '${escapeHtml(filament.brand)} ${escapeHtml(filament.color)}')">📦 Archive</button>` : ''}
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
    
    // Update archived count
    updateArchivedCount();
}

// Sort filaments based on selected criteria
function sortFilaments(filamentsArray) {
    const sortBy = sortBySelect.value;
    if (!sortBy) return filamentsArray;
    
    const sorted = [...filamentsArray];
    
    switch(sortBy) {
        case 'lastUsed':
            // Recently used first (most recent lastUsed date)
            sorted.sort((a, b) => {
                const dateA = a.lastUsed ? new Date(a.lastUsed) : new Date(0);
                const dateB = b.lastUsed ? new Date(b.lastUsed) : new Date(0);
                return dateB - dateA;
            });
            break;
            
        case 'mostUsed':
            // Most used (by number of prints or total weight used)
            sorted.sort((a, b) => {
                const usedA = a.weight - a.remainingWeight;
                const usedB = b.weight - b.remainingWeight;
                return usedB - usedA;
            });
            break;
            
        case 'leastUsed':
            // Least used
            sorted.sort((a, b) => {
                const usedA = a.weight - a.remainingWeight;
                const usedB = b.weight - b.remainingWeight;
                return usedA - usedB;
            });
            break;
            
        case 'lowStock':
            // Low stock first (by percentage remaining)
            sorted.sort((a, b) => {
                const percentA = (a.remainingWeight / a.weight) * 100;
                const percentB = (b.remainingWeight / b.weight) * 100;
                return percentA - percentB;
            });
            break;
            
        case 'highStock':
            // High stock first
            sorted.sort((a, b) => {
                const percentA = (a.remainingWeight / a.weight) * 100;
                const percentB = (b.remainingWeight / b.weight) * 100;
                return percentB - percentA;
            });
            break;
            
        case 'newest':
            // Newest purchase first
            sorted.sort((a, b) => {
                const dateA = a.purchaseDate ? new Date(a.purchaseDate) : new Date(0);
                const dateB = b.purchaseDate ? new Date(b.purchaseDate) : new Date(0);
                return dateB - dateA;
            });
            break;
            
        case 'oldest':
            // Oldest purchase first
            sorted.sort((a, b) => {
                const dateA = a.purchaseDate ? new Date(a.purchaseDate) : new Date(0);
                const dateB = b.purchaseDate ? new Date(b.purchaseDate) : new Date(0);
                return dateA - dateB;
            });
            break;
            
        case 'brand':
            // Brand A-Z
            sorted.sort((a, b) => a.brand.localeCompare(b.brand));
            break;
            
        case 'brandDesc':
            // Brand Z-A
            sorted.sort((a, b) => b.brand.localeCompare(a.brand));
            break;
            
        case 'material':
            // Material type
            sorted.sort((a, b) => a.material.localeCompare(b.material));
            break;
            
        case 'color':
            // Color A-Z
            sorted.sort((a, b) => a.color.localeCompare(b.color));
            break;
            
        case 'costHigh':
            // Cost high to low
            sorted.sort((a, b) => (b.cost || 0) - (a.cost || 0));
            break;
            
        case 'costLow':
            // Cost low to high
            sorted.sort((a, b) => (a.cost || 0) - (b.cost || 0));
            break;
    }
    
    return sorted;
}

// Filter filaments
function filterFilaments() {
    const searchTerm = searchInput.value.toLowerCase();
    const materialFilter = document.getElementById('materialFilter').value;
    
    let filtered = filaments.filter(filament => {
        const matchesSearch = !searchTerm || 
            filament.brand.toLowerCase().includes(searchTerm) ||
            filament.material.toLowerCase().includes(searchTerm) ||
            filament.color.toLowerCase().includes(searchTerm);
            
        const matchesMaterial = !materialFilter || filament.material === materialFilter;
        
        return matchesSearch && matchesMaterial;
    });
    
    // Apply sorting
    filtered = sortFilaments(filtered);
    
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

// Auto-refresh Functions
let autoRefreshTimer = null;
function initializeAutoRefresh() {
    const INTERVAL_MS = 15000; // 15 seconds
    function tick() {
        if (document.hidden) return; // pause in background
        if (filamentModal.style.display === 'block') return; // don't refresh during edit
        loadFilaments();
    }
    autoRefreshTimer = setInterval(tick, INTERVAL_MS);
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            // immediate refresh when returning to the tab
            tick();
        }
    });
}

// Dark Mode Functions
function initializeDarkMode() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        updateDarkModeButton(true);
    }
}

function toggleDarkMode() {
    const isDarkMode = document.body.classList.contains('dark-mode');
    
    if (isDarkMode) {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'false');
        updateDarkModeButton(false);
    } else {
        document.body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'true');
        updateDarkModeButton(true);
    }
}

function updateDarkModeButton(isDarkMode) {
    if (isDarkMode) {
        darkModeToggle.textContent = '☀️ Light Mode';
        darkModeToggle.title = 'Switch to Light Mode';
    } else {
        darkModeToggle.textContent = '🌙 Dark Mode';
        darkModeToggle.title = 'Switch to Dark Mode';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape to close modal
    if (e.key === 'Escape' && filamentModal.style.display === 'block') {
        closeModal();
    }
    
    // Escape to close archive modal
    if (e.key === 'Escape' && archiveModal.style.display === 'block') {
        closeArchiveModal();
    }
    
    // Ctrl/Cmd + N to add new filament
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        openModal();
    }
    
    // Ctrl/Cmd + D to toggle dark mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleDarkMode();
    }
});

// Archive/History Functions

const archiveModal = document.getElementById('archiveModal');
const viewArchiveBtn = document.getElementById('viewArchiveBtn');
const autoArchiveBtn = document.getElementById('autoArchiveBtn');

if (viewArchiveBtn) {
    viewArchiveBtn.addEventListener('click', viewArchivedSpools);
}

if (autoArchiveBtn) {
    autoArchiveBtn.addEventListener('click', autoArchiveEmpty);
}

// Archive a filament
async function archiveFilament(id, name) {
    if (!confirm(`Archive ${name}? This will remove it from active inventory but keep its history.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/filaments/${id}/archive`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            loadFilaments();
        } else {
            showError(data.error || 'Failed to archive filament');
        }
    } catch (error) {
        console.error('Error archiving filament:', error);
        showError('Failed to archive filament');
    }
}

// Unarchive a filament
async function unarchiveFilament(id, name) {
    if (!confirm(`Restore ${name} to active inventory?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/filaments/${id}/unarchive`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            viewArchivedSpools(); // Refresh archived list
            loadFilaments(); // Refresh active list
        } else {
            showError(data.error || 'Failed to unarchive filament');
        }
    } catch (error) {
        console.error('Error unarchiving filament:', error);
        showError('Failed to unarchive filament');
    }
}

// View archived spools
async function viewArchivedSpools() {
    try {
        const response = await fetch('/api/filaments/archived');
        const data = await response.json();
        const archived = data.filaments || [];
        
        const archivedGrid = document.getElementById('archivedFilamentsGrid');
        
        if (archived.length === 0) {
            archivedGrid.innerHTML = `
                <div class="empty-state">
                    <h3>No archived spools</h3>
                    <p>Empty spools will be automatically archived when they reach 0g.</p>
                </div>
            `;
        } else {
            archivedGrid.innerHTML = archived.map(filament => {
                const usagePercent = ((filament.weight - filament.remainingWeight) / filament.weight) * 100;
                const totalUsed = filament.weight - filament.remainingWeight;
                const archivedDate = filament.archivedAt ? new Date(filament.archivedAt).toLocaleDateString() : 'Unknown';
                
                return `
                    <div class="filament-card archived">
                        <div class="filament-header">
                            <div class="filament-title">
                                <div class="filament-brand">${escapeHtml(filament.color)}</div>
                                <span class="filament-material">${filament.material}</span>
                            </div>
                            <div class="archive-badge">📦 Archived</div>
                        </div>
                        
                        <div class="filament-color">${escapeHtml(filament.brand)}</div>
                        
                        <div class="filament-details">
                            <div class="detail-item">
                                <span class="detail-label">Original Weight:</span>
                                <span class="detail-value">${filament.weight}g</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Total Used:</span>
                                <span class="detail-value">${totalUsed.toFixed(1)}g (${usagePercent.toFixed(1)}%)</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Archived:</span>
                                <span class="detail-value">${archivedDate}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Cost:</span>
                                <span class="detail-value">$${filament.cost ? filament.cost.toFixed(2) : '0.00'}</span>
                            </div>
                        </div>
                        
                        ${filament.printHistory && filament.printHistory.length > 0 ? `
                            <div class="print-history">
                                <strong>Print History (${filament.printHistory.length} prints)</strong>
                                ${filament.printHistory.slice(-3).reverse().map(print => `
                                    <div class="print-entry">
                                        <span class="print-job">${escapeHtml(print.printJob)}</span>
                                        <span class="print-used">${print.usedWeight}g</span>
                                        <span class="print-date">${new Date(print.date).toLocaleDateString()}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        
                        <div class="filament-actions">
                            <button class="btn btn-secondary" onclick="unarchiveFilament('${filament.id}', '${escapeHtml(filament.brand)} ${escapeHtml(filament.color)}')">
                                ↻ Restore
                            </button>
                            <button class="btn btn-danger" onclick="deleteFilament('${filament.id}', '${escapeHtml(filament.brand)} ${escapeHtml(filament.color)}')">
                                🗑️ Delete Permanently
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        archiveModal.style.display = 'block';
    } catch (error) {
        console.error('Error loading archived filaments:', error);
        showError('Failed to load archived filaments');
    }
}

// Close archive modal
function closeArchiveModal() {
    archiveModal.style.display = 'none';
}

// Auto-archive empty spools
async function autoArchiveEmpty() {
    if (!confirm('Automatically archive all empty spools (0g remaining)?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/filaments/auto-archive', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.archived_count > 0) {
                showSuccess(`${data.message}: ${data.archived_spools.join(', ')}`);
            } else {
                showSuccess(data.message);
            }
            loadFilaments();
        } else {
            showError(data.error || 'Failed to auto-archive');
        }
    } catch (error) {
        console.error('Error auto-archiving:', error);
        showError('Failed to auto-archive empty spools');
    }
}

// Update stats to include archived count
async function updateArchivedCount() {
    try {
        const response = await fetch('/api/filaments/archived');
        const data = await response.json();
        const archivedCountEl = document.getElementById('archivedCount');
        if (archivedCountEl) {
            archivedCountEl.textContent = data.count || 0;
        }
    } catch (error) {
        console.error('Error loading archived count:', error);
    }
}