/**
 * Technician Portal JavaScript
 * Contains common functions used across the technician interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    initializeTooltips();
    
    // Initialize stats counters with animation if they exist
    initializeStatsCounters();
    
    // Handle modal events
    initializeModals();
    
    // Show appropriate fields based on selections
    initializeConditionalFields();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Animate counters in stat cards
 */
function initializeStatsCounters() {
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length > 0) {
        statValues.forEach(function(element) {
            const value = parseInt(element.getAttribute('data-value') || element.textContent);
            animateCounter(element, 0, value, 1500);
            
            // Re-animate counter on hover
            const parentCard = element.closest('.stat-card');
            if (parentCard) {
                parentCard.addEventListener('mouseenter', function() {
                    animateCounter(element, 0, value, 1000);
                });
            }
        });
    }
}

/**
 * Animate a counter from start to end value
 */
function animateCounter(element, start, end, duration) {
    if (start === end) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value;
        
        // Add pulse animation when counter reaches end
        if (progress === 1 && element.closest('.stat-card')) {
            element.classList.add('pulse-animation');
            setTimeout(() => {
                element.classList.remove('pulse-animation');
            }, 1000);
        }
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/**
 * Initialize modal behaviors
 */
function initializeModals() {
    // Reset form when closing modal
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) form.reset();
            
            // Clear any preview content
            const preview = this.querySelector('.file-preview');
            if (preview) preview.innerHTML = '';
        });
    });
    
    // Preview file uploads
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function() {
            const preview = document.getElementById(this.getAttribute('data-preview') || 'filePreview');
            if (!preview) return;
            
            preview.innerHTML = '';
            if (this.files.length > 0) {
                preview.style.display = 'block';
                for (let i = 0; i < this.files.length; i++) {
                    const file = this.files[i];
                    previewFile(file, preview);
                }
            } else {
                preview.style.display = 'none';
            }
        });
    });
    
    // Handle confirmation dialogs
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Create a preview element for a file
 */
function previewFile(file, container) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item d-flex align-items-center p-2 mb-2 bg-light rounded';
    
    // Determine icon based on file type
    let icon = 'fas fa-file';
    if (file.type.startsWith('image/')) icon = 'fas fa-file-image';
    else if (file.type === 'application/pdf') icon = 'fas fa-file-pdf';
    else if (file.type.includes('word')) icon = 'fas fa-file-word';
    else if (file.type.includes('excel') || file.type.includes('sheet')) icon = 'fas fa-file-excel';
    else if (file.type.includes('zip') || file.type.includes('compressed')) icon = 'fas fa-file-archive';
    
    fileItem.innerHTML = `
        <div class="me-2"><i class="${icon} text-primary"></i></div>
        <div class="flex-grow-1">
            <div class="small fw-bold text-truncate" style="max-width: 200px;">${file.name}</div>
            <div class="small text-muted">${formatFileSize(file.size)}</div>
        </div>
    `;
    
    container.appendChild(fileItem);
}

/**
 * Format file size in KB, MB, etc.
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize conditional field visibility
 */
function initializeConditionalFields() {
    // Show/hide fields based on select values
    document.querySelectorAll('select[data-controls]').forEach(select => {
        const targetId = select.getAttribute('data-controls');
        const targetElement = document.getElementById(targetId);
        
        if (!targetElement) return;
        
        const showValues = select.getAttribute('data-show-values')?.split(',') || [];
        
        function updateVisibility() {
            const currentValue = select.value;
            if (showValues.includes(currentValue)) {
                targetElement.style.display = '';
            } else {
                targetElement.style.display = 'none';
            }
        }
        
        // Initialize visibility
        updateVisibility();
        
        // Update on change
        select.addEventListener('change', updateVisibility);
    });
    
    // Handle checkbox toggles
    document.querySelectorAll('input[type="checkbox"][data-toggle-element]').forEach(checkbox => {
        const targetId = checkbox.getAttribute('data-toggle-element');
        const target = document.getElementById(targetId);
        
        if (!target) return;
        
        function updateVisibility() {
            target.style.display = checkbox.checked ? '' : 'none';
        }
        
        // Initialize
        updateVisibility();
        
        // Update on change
        checkbox.addEventListener('change', updateVisibility);
    });
}

/**
 * Handle ticket filtering functionality
 */
function applyTicketFilters() {
    const statusFilter = document.querySelector('.filter-btn-group:nth-child(1) .filter-btn.active')?.getAttribute('data-filter') || 'all';
    const priorityFilter = document.querySelector('.filter-btn-group:nth-child(2) .filter-btn.active')?.getAttribute('data-filter') || 'all';
    const rows = document.querySelectorAll('.tickets-table tbody tr');
    
    rows.forEach(row => {
        const status = row.getAttribute('data-status');
        const priority = row.getAttribute('data-priority');
        
        let statusMatch = statusFilter === 'all' || status === statusFilter;
        let priorityMatch = priorityFilter === 'all' || priority === priorityFilter;
        
        row.style.display = statusMatch && priorityMatch ? '' : 'none';
    });
}

/**
 * Handle table sorting
 */
function sortTable(tableId, column, direction) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Map column names to indices
    const columnMap = {
        'id': 1, // Assuming first column is checkbox
        'subject': 2,
        'customer': 3,
        'status': 4,
        'priority': 5,
        'created': 6,
        'updated': 7
    };
    
    const columnIndex = columnMap[column] || 0;
    
    // Sort the rows
    rows.sort((a, b) => {
        const cellA = a.cells[columnIndex];
        const cellB = b.cells[columnIndex];
        
        if (!cellA || !cellB) return 0;
        
        let valueA = cellA.textContent.trim();
        let valueB = cellB.textContent.trim();
        
        // Parse dates
        if (column === 'created' || column === 'updated') {
            return compareDates(valueA, valueB, direction);
        }
        
        // Parse numbers
        if (!isNaN(valueA) && !isNaN(valueB)) {
            return compareNumbers(parseFloat(valueA), parseFloat(valueB), direction);
        }
        
        // Default string comparison
        return compareStrings(valueA, valueB, direction);
    });
    
    // Reattach rows in new order
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Compare two date strings
 */
function compareDates(a, b, direction) {
    const dateA = new Date(a);
    const dateB = new Date(b);
    
    if (dateA < dateB) return direction === 'asc' ? -1 : 1;
    if (dateA > dateB) return direction === 'asc' ? 1 : -1;
    return 0;
}

/**
 * Compare two numbers
 */
function compareNumbers(a, b, direction) {
    if (a < b) return direction === 'asc' ? -1 : 1;
    if (a > b) return direction === 'asc' ? 1 : -1;
    return 0;
}

/**
 * Compare two strings
 */
function compareStrings(a, b, direction) {
    const comparison = a.localeCompare(b);
    return direction === 'asc' ? comparison : -comparison;
}

/**
 * Search functionality for tables
 */
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    const searchTerm = input.value.toLowerCase();
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const isVisible = row.style.display !== 'none';
        
        // Only search through currently visible rows (respect filters)
        if (isVisible) {
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        }
    });
} 