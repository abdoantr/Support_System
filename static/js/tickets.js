/**
 * Tickets functionality for Support System
 * Handles ticket filtering, searching, and updates
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeTicketsPage();
    
    // Add floating animation to the tickets card with a slight delay
    setTimeout(() => {
        const ticketsCard = document.querySelector('.tickets-card');
        if (ticketsCard) {
            ticketsCard.classList.add('animate-float');
        }
    }, 300);
});

/**
 * Initialize all ticket page components
 */
function initializeTicketsPage() {
    // Initialize ticket filters
    initializeStatusFilter();
    initializePriorityFilter();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize sorting
    initializeSorting();
    
    // Initialize file uploads
    initializeFileUploads();
    
    // Initialize form submissions
    initializeTicketForms();
    
    // Initialize stats counters
    initializeStatsCounters();
    
    // Initialize view and edit modal functionality
    initializeTicketModals();

    // Apply any URL parameters
    applyUrlFilters();
}

/**
 * Initialize status filter buttons
 */
function initializeStatusFilter() {
    const statusButtons = document.querySelectorAll('.btn-group [data-filter]');
    if (!statusButtons.length) return;
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            statusButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get the filter value
            const filterValue = this.getAttribute('data-filter');
            
            // Filter tickets
            filterTickets();
        });
    });
}

/**
 * Initialize priority filter buttons
 */
function initializePriorityFilter() {
    const priorityButtons = document.querySelectorAll('.btn-group [data-priority]');
    if (!priorityButtons.length) return;
    
    priorityButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            priorityButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Filter tickets
            filterTickets();
        });
    });
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInput = document.getElementById('ticketSearch');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        filterTickets();
    });
}

/**
 * Filter tickets based on status, priority, and search query
 */
function filterTickets() {
    const rows = document.querySelectorAll('.ticket-row');
    if (!rows.length) return;
    
    const statusFilter = document.querySelector('.btn-group [data-filter].active');
    const priorityFilter = document.querySelector('.btn-group [data-priority].active');
    const searchQuery = document.getElementById('ticketSearch').value.toLowerCase();
    
    const statusValue = statusFilter ? statusFilter.getAttribute('data-filter') : 'all';
    const priorityValue = priorityFilter ? priorityFilter.getAttribute('data-priority') : 'all';
    
    rows.forEach(row => {
        const rowStatus = row.getAttribute('data-status');
        const rowPriority = row.getAttribute('data-priority');
        const rowText = row.textContent.toLowerCase();
        
        const statusMatch = statusValue === 'all' || rowStatus === statusValue;
        const priorityMatch = priorityValue === 'all' || rowPriority === priorityValue;
        const searchMatch = searchQuery === '' || rowText.includes(searchQuery);
        
        if (statusMatch && priorityMatch && searchMatch) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
    
    // Show empty state if no tickets are visible
    updateEmptyState();
}

/**
 * Show or hide empty state based on visible tickets
 */
function updateEmptyState() {
    const visibleRows = document.querySelectorAll('.ticket-row[style="display: ;"], .ticket-row:not([style])');
    const ticketsTable = document.querySelector('.tickets-table');
    const emptyState = document.querySelector('.empty-state-container');
    
    if (emptyState && ticketsTable) {
        if (visibleRows.length === 0) {
            ticketsTable.style.display = 'none';
            emptyState.style.display = 'block';
        } else {
            ticketsTable.style.display = '';
            emptyState.style.display = 'none';
        }
    }
}

/**
 * Initialize table sorting
 */
function initializeSorting() {
    const sortableHeaders = document.querySelectorAll('th.sortable');
    if (!sortableHeaders.length) return;
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortBy = this.getAttribute('data-sort');
            const currentDirection = this.getAttribute('data-direction') || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            // Update header attributes
            sortableHeaders.forEach(h => h.removeAttribute('data-direction'));
            this.setAttribute('data-direction', newDirection);
            
            // Update visual indicators
            sortableHeaders.forEach(h => {
                const icon = h.querySelector('i.fas');
                icon.className = 'fas fa-sort ms-2';
            });
            
            const icon = this.querySelector('i.fas');
            icon.className = `fas fa-sort-${newDirection === 'asc' ? 'up' : 'down'} ms-2`;
            
            // Sort the table
            sortTable(sortBy, newDirection);
        });
    });
}

/**
 * Sort table based on column and direction
 */
function sortTable(sortBy, direction) {
    const table = document.querySelector('.tickets-table');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Sort rows
    rows.sort((a, b) => {
        let aValue, bValue;
        
        switch (sortBy) {
            case 'id':
                aValue = parseInt(a.querySelector('.ticket-id').textContent.replace('#', ''));
                bValue = parseInt(b.querySelector('.ticket-id').textContent.replace('#', ''));
                break;
            case 'priority':
                const priorityOrder = { 'urgent': 1, 'high': 2, 'medium': 3, 'low': 4 };
                aValue = priorityOrder[a.getAttribute('data-priority')] || 999;
                bValue = priorityOrder[b.getAttribute('data-priority')] || 999;
                break;
            case 'status':
                const statusOrder = { 'new': 1, 'in_progress': 2, 'pending': 3, 'resolved': 4, 'closed': 5 };
                aValue = statusOrder[a.getAttribute('data-status')] || 999;
                bValue = statusOrder[b.getAttribute('data-status')] || 999;
                break;
            case 'created':
            case 'updated':
                const aCell = a.querySelector(`td[data-date]`);
                const bCell = b.querySelector(`td[data-date]`);
                aValue = aCell ? aCell.getAttribute('data-date') : '';
                bValue = bCell ? bCell.getAttribute('data-date') : '';
                break;
            default:
                return 0;
        }
        
        // Compare values
        if (aValue < bValue) return direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Reorder rows in DOM
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Initialize custom file upload functionality
 */
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const container = input.closest('.custom-file-upload');
        if (!container) return;
        
        input.addEventListener('change', function() {
            updateFileUploadDisplay(this);
        });
        
        // Drag and drop functionality
        container.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        container.addEventListener('dragleave', function() {
            this.classList.remove('dragover');
        });
        
        container.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            input.files = e.dataTransfer.files;
            updateFileUploadDisplay(input);
        });
    });
}

/**
 * Update file upload display with selected files
 */
function updateFileUploadDisplay(input) {
    const container = input.closest('.custom-file-upload');
    if (!container) return;
    
    const infoElement = container.querySelector('.file-upload-info');
    if (!infoElement) return;
    
    if (input.files.length > 0) {
        let fileNames = '';
        for (let i = 0; i < Math.min(input.files.length, 3); i++) {
            fileNames += `<div class="selected-file"><i class="fas fa-file me-2"></i>${input.files[i].name}</div>`;
        }
        
        if (input.files.length > 3) {
            fileNames += `<div class="selected-file text-muted">+${input.files.length - 3} more files...</div>`;
        }
        
        infoElement.innerHTML = `
            <div class="selected-files-container">
                ${fileNames}
            </div>
            <div class="file-actions mt-2">
                <button type="button" class="btn btn-sm btn-outline-secondary reset-upload">
                    <i class="fas fa-times me-1"></i>Clear
                </button>
            </div>
        `;
        
        // Add event listener to reset button
        const resetButton = infoElement.querySelector('.reset-upload');
        if (resetButton) {
            resetButton.addEventListener('click', function(e) {
                e.preventDefault();
                input.value = '';
                updateFileUploadDisplay(input);
            });
        }
    } else {
        infoElement.innerHTML = `
            <i class="fas fa-cloud-upload-alt me-2"></i>
            <span>Drop files here or click to upload</span>
            <small class="d-block mt-1">You can upload multiple files (max 5MB each)</small>
        `;
    }
}

/**
 * Initialize ticket form submissions
 */
function initializeTicketForms() {
    // New ticket form
    const newTicketForm = document.getElementById('newTicketForm');
    if (newTicketForm) {
        newTicketForm.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';
            }
        });
    }
    
    // Update ticket forms
    const updateTicketForms = document.querySelectorAll('form[id^="updateTicketForm"]');
    updateTicketForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';
            }
        });
    });
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Remove toast from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Get URL parameters
 */
function getUrlParams() {
    const params = {};
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    
    for (const [key, value] of urlParams.entries()) {
        params[key] = value;
    }
    
    return params;
}

/**
 * Apply filters from URL parameters
 */
function applyUrlFilters() {
    const params = getUrlParams();
    
    // Apply status filter
    if (params.status) {
        const statusButton = document.querySelector(`.btn-group [data-filter="${params.status}"]`);
        if (statusButton) {
            statusButton.click();
        }
    }
    
    // Apply priority filter
    if (params.priority) {
        const priorityButton = document.querySelector(`.btn-group [data-priority="${params.priority}"]`);
        if (priorityButton) {
            priorityButton.click();
        }
    }
    
    // Apply search query
    if (params.q) {
        const searchInput = document.getElementById('ticketSearch');
        if (searchInput) {
            searchInput.value = params.q;
            filterTickets();
        }
    }
}

/**
 * Initialize animated counters for stats cards
 */
function initializeStatsCounters() {
    const statValues = document.querySelectorAll('.stat-value');
    
    if (!statValues.length) return;
    
    statValues.forEach(stat => {
        const targetValue = parseInt(stat.textContent, 10);
        if (isNaN(targetValue)) return;
        
        // Start from zero
        stat.textContent = '0';
        
        // Animate to target value
        animateCounter(stat, 0, targetValue, 1500);
        
        // Add hover effect for re-animation
        stat.closest('.stat-card').addEventListener('mouseenter', function() {
            const currentValue = parseInt(stat.textContent, 10);
            if (currentValue === targetValue) {
                // Only re-animate if counter has completed
                animateCounter(stat, 0, targetValue, 1200);
            }
        });
    });
}

/**
 * Animate counter from start to end
 */
function animateCounter(element, start, end, duration) {
    if (start === end) return;
    
    // Reset to start
    element.textContent = start.toString();
    
    const range = end - start;
    const minValue = Math.abs(range) > 100 ? 4 : 1;
    const increment = Math.max(Math.floor(range / (duration / 16)), minValue);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            element.textContent = end.toString();
            clearInterval(timer);
            
            // Add a pulse effect when done
            element.classList.add('count-complete');
            setTimeout(() => {
                element.classList.remove('count-complete');
            }, 500);
        } else {
            element.textContent = current.toString();
        }
    }, 16);
}

/**
 * Initialize modal components for ticket viewing and editing
 */
function initializeTicketModals() {
    console.log('Initializing ticket modals');

    // Add event listeners to all modals
    document.querySelectorAll('.modal').forEach(modal => {
        // Prevent clicks inside modal dialog from closing the modal
        const modalDialog = modal.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.addEventListener('mousedown', function(e) {
                e.stopPropagation();
            });
            modalDialog.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }

        // Only close on clicks directly on the modal backdrop
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        });
    });

    // Add event listener for close buttons
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    });
    
    // Attach click handlers to view buttons
    document.querySelectorAll('.btn-view-ticket, .view-ticket-btn, .btn-info[data-ticket-id], a[href="#"][title="View"], [data-action="view"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('View button clicked');
            
            // Get ticket ID from various possible sources
            let ticketId = this.dataset.ticketId || 
                          this.getAttribute('data-id') || 
                          this.closest('tr')?.dataset.ticketId || 
                          this.closest('[data-ticket-id]')?.dataset.ticketId;
                          
            // Try to extract ID from parent row if not found
            if (!ticketId && this.closest('tr')) {
                const row = this.closest('tr');
                const idCell = row.querySelector('td:first-child');
                if (idCell) {
                    // Try to extract the ID from text content of the first cell
                    const idText = idCell.textContent.trim();
                    const idMatch = idText.match(/\d+/);
                    if (idMatch) {
                        ticketId = idMatch[0];
                    }
                }
            }
            
            if (!ticketId) {
                console.error('Could not determine ticket ID');
                return;
            }
            
            console.log('Opening view modal for ticket ID:', ticketId);
            
            // Try different possible modal IDs
            const modalIds = [
                `viewTicketModal${ticketId}`,
                `ticketDetailModal${ticketId}`,
                `viewModal${ticketId}`,
                `ticketModal${ticketId}`,
                `ticketDetails${ticketId}`
            ];
            
            let modal = null;
            
            // Find the modal if it exists
            for (const modalId of modalIds) {
                const modalElement = document.getElementById(modalId);
                if (modalElement) {
                    modal = modalElement;
                    break;
                }
            }
            
            // If we couldn't find a modal, check for a generic one
            if (!modal) {
                const genericModal = document.getElementById('viewTicketModal') || 
                                    document.getElementById('ticketDetailModal') || 
                                    document.getElementById('ticketModal');
                                    
                if (genericModal) {
                    modal = genericModal;
                    // Update modal title to reflect the ticket
                    const title = modal.querySelector('.modal-title');
                    if (title) {
                        title.textContent = `#${ticketId} Details`;
                    }
                }
            }
            
            // Last fallback - try to find any modal with the ticket ID in the title
            if (!modal) {
                document.querySelectorAll('.modal').forEach(m => {
                    const title = m.querySelector('.modal-title');
                    if (title && title.textContent.includes(`#${ticketId}`)) {
                        modal = m;
                    }
                });
            }
            
            if (!modal) {
                console.error(`No modal found for ticket ID: ${ticketId}`);
                alert('Could not open ticket details. Please try again later.');
                return;
            }
            
            // Remove existing event listeners to prevent duplicates
            cleanupModalEventListeners(modal);
            
            // Add new event listeners for closing the modal
            setupModalEventListeners(modal);
            
            // Show the modal using Bootstrap, jQuery, or manually as fallback
            showModal(modal, ticketId);
        });
    });
    
    // Attach click handlers to edit buttons
    document.querySelectorAll('.btn-edit-ticket, .edit-ticket-btn, .btn-primary[data-ticket-id], a[href="#"][title="Edit"], [data-action="edit"], .btn-success[data-ticket-id]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Edit button clicked');
            
            // Get ticket ID similar to view button logic
            let ticketId = this.dataset.ticketId || 
                          this.getAttribute('data-id') || 
                          this.closest('tr')?.dataset.ticketId || 
                          this.closest('[data-ticket-id]')?.dataset.ticketId;
                          
            // Try to extract ID from parent row if not found
            if (!ticketId && this.closest('tr')) {
                const row = this.closest('tr');
                const idCell = row.querySelector('td:first-child');
                if (idCell) {
                    // Try to extract the ID from text content of the first cell
                    const idText = idCell.textContent.trim();
                    const idMatch = idText.match(/\d+/);
                    if (idMatch) {
                        ticketId = idMatch[0];
                    }
                }
            }
            
            if (!ticketId) {
                console.error('Could not determine ticket ID');
                return;
            }
            
            console.log('Opening edit modal for ticket ID:', ticketId);
            
            // Try different possible modal IDs for edit modals
            const modalIds = [
                `editTicketModal${ticketId}`,
                `editModal${ticketId}`,
                `ticketEditModal${ticketId}`,
                `editTicket${ticketId}`
            ];
            
            let modal = null;
            
            // Find the modal if it exists
            for (const modalId of modalIds) {
                const modalElement = document.getElementById(modalId);
                if (modalElement) {
                    modal = modalElement;
                    break;
                }
            }
            
            // If we couldn't find a modal, check for a generic one
            if (!modal) {
                const genericModal = document.getElementById('editTicketModal') || 
                                    document.getElementById('ticketEditModal') || 
                                    document.getElementById('editModal');
                                    
                if (genericModal) {
                    modal = genericModal;
                    // Update modal title to reflect the ticket
                    const title = modal.querySelector('.modal-title');
                    if (title) {
                        title.textContent = `Edit Ticket #${ticketId}`;
                    }
                }
            }
            
            if (!modal) {
                console.error(`No edit modal found for ticket ID: ${ticketId}`);
                alert('Could not open ticket editor. Please try again later.');
                return;
            }
            
            // Remove existing event listeners to prevent duplicates
            cleanupModalEventListeners(modal);
            
            // Add new event listeners for closing the modal
            setupModalEventListeners(modal);
            
            // Show the modal using Bootstrap, jQuery, or manually as fallback
            showModal(modal, ticketId);
        });
    });
    
    // Setup global ESC key handler for any open modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                console.log('ESC key pressed, closing modal');
                hideModal(openModal);
                
                // Remove body lock
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
                
                // Remove backdrop
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
            }
        }
    });
    
    // Also setup global click handler for backdrop
    document.addEventListener('click', function(e) {
        // If clicking on a backdrop
        if (e.target.classList.contains('modal-backdrop') || 
            (e.target.classList.contains('modal') && e.target.classList.contains('show'))) {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                console.log('Backdrop clicked, closing modal');
                hideModal(openModal);
            }
        }
    });
    
    console.log('Ticket modals initialized');
}

/**
 * Clean up any existing event listeners on the modal
 */
function cleanupModalEventListeners(modal) {
    // Clone and replace close buttons to remove event listeners
    modal.querySelectorAll('[data-dismiss="modal"], .close, .btn-close, .btn-secondary').forEach(button => {
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
    });
}

/**
 * Setup event listeners for closing the modal
 */
function setupModalEventListeners(modal) {
    // Add click handlers to close buttons
    modal.querySelectorAll('[data-dismiss="modal"], .close, .btn-close, .btn-secondary').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Close button clicked');
            hideModal(modal);
        });
    });
    
    // Prevent modal content clicks from closing the modal
    const modalContent = modal.querySelector('.modal-content');
    if (modalContent) {
        modalContent.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        // Add specific handling for form elements
        modalContent.querySelectorAll('input, textarea, select, button').forEach(element => {
            element.addEventListener('click', function(e) {
                e.stopPropagation();
            });
            element.addEventListener('mousedown', function(e) {
                e.stopPropagation();
            });
        });
    }

    // Only close on backdrop click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    });

    // Prevent any bubbling from modal dialog
    modal.querySelector('.modal-dialog')?.addEventListener('click', function(e) {
        e.stopPropagation();
    });
}

/**
 * Show modal using appropriate method (Bootstrap, jQuery, or manual fallback)
 */
function showModal(modal, ticketId) {
    console.log('Showing modal for ticket:', ticketId);
    
    // Add click handlers for form elements to prevent modal from closing
    const modalDialog = modal.querySelector('.modal-dialog');
    if (modalDialog) {
        modalDialog.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        // Ensure form elements are fully interactive
        const formElements = modalDialog.querySelectorAll('input, textarea, select, button');
        formElements.forEach(element => {
            element.addEventListener('click', function(e) {
                e.stopPropagation();
                e.stopImmediatePropagation();
            });
            
            // For input fields, prevent Enter key from closing modal
            if (element.tagName.toLowerCase() === 'input' || element.tagName.toLowerCase() === 'textarea') {
                element.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.target.form) {
                        e.preventDefault();
                    }
                });
            }
        });
    }
    
    // Try Bootstrap 5
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        try {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            console.log('Shown using Bootstrap 5');
            
            // Still fix content visibility after a short delay
            setTimeout(() => fixModalContentVisibility(modal), 50);
            return;
        } catch (e) {
            console.warn('Failed to show with Bootstrap 5:', e);
        }
    }
    
    // Try Bootstrap 4 or jQuery
    if (typeof jQuery !== 'undefined' && jQuery.fn.modal) {
        try {
            $(modal).modal('show');
            console.log('Shown using jQuery/Bootstrap');
            
            // Still fix content visibility after a short delay
            setTimeout(() => fixModalContentVisibility(modal), 50);
            return;
        } catch (e) {
            console.warn('Failed to show with jQuery:', e);
        }
    }
    
    // Fallback to manual showing
    console.log('Using manual modal display as fallback');
    showModalManually(modal);
}

/**
 * Hide modal using appropriate method
 */
function hideModal(modal) {
    console.log('Hiding modal');
    if (!modal) return;
    
    // Try Bootstrap 5
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        try {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
                console.log('Hidden using Bootstrap 5');
                return;
            }
        } catch (e) {
            console.warn('Failed to hide with Bootstrap 5:', e);
        }
    }
    
    // Try Bootstrap 4 or jQuery
    if (typeof jQuery !== 'undefined' && jQuery.fn.modal) {
        try {
            $(modal).modal('hide');
            console.log('Hidden using jQuery/Bootstrap');
            return;
        } catch (e) {
            console.warn('Failed to hide with jQuery:', e);
        }
    }
    
    // Fallback to manual hiding
    console.log('Using manual modal hiding as fallback');
    hideModalManually(modal);
}

/**
 * Hide modal manually (without Bootstrap or jQuery)
 */
function hideModalManually(modal) {
    if (!modal) return;
    
    // Hide modal
    modal.classList.remove('show');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    // Remove backdrop
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    
    console.log('Modal hidden manually');
}

// Initialize URL filters on page load
document.addEventListener('DOMContentLoaded', function() {
    applyUrlFilters();
    
    // Check if there's a ticket ID in the URL hash
    const hash = window.location.hash;
    if (hash && hash.startsWith('#ticket-')) {
        const ticketId = hash.replace('#ticket-', '');
        const ticketModal = document.getElementById(`ticketDetailModal${ticketId}`);
        if (ticketModal) {
            const modal = new bootstrap.Modal(ticketModal);
            modal.show();
        }
    }
});
