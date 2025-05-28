/**
 * Technician Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initTicketActions();
    initAvailabilityToggle();
    initQuickFilters();
    initCharts();
    initNotifications();
    initSortableTables();
    initTooltips();
    
    // Show welcome message (if first login of the day)
    if (localStorage.getItem('lastLoginDate') !== new Date().toDateString()) {
        localStorage.setItem('lastLoginDate', new Date().toDateString());
        showWelcomeMessage();
    }
});

/**
 * Initialize ticket action handlers
 */
function initTicketActions() {
    // Handle ticket status updates
    document.querySelectorAll('[data-action="update-status"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const ticketId = this.getAttribute('data-ticket-id');
            const status = this.getAttribute('data-status');
            updateTicketStatus(ticketId, status);
        });
    });
    
    // Handle ticket assignment
    document.querySelectorAll('[data-action="assign-ticket"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const ticketId = this.getAttribute('data-ticket-id');
            const userId = this.getAttribute('data-user-id');
            assignTicket(ticketId, userId);
        });
    });
}

/**
 * Update ticket status
 */
function updateTicketStatus(ticketId, status) {
    showLoading();
    
    fetch(`/api/tickets/${ticketId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update ticket status');
        }
        return response.json();
    })
    .then(data => {
        showToast('Ticket status updated successfully', 'success');
        // Refresh ticket list or update UI
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('Error updating ticket status:', error);
        showToast('Failed to update ticket status', 'error');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Assign ticket to technician
 */
function assignTicket(ticketId, userId) {
    showLoading();
    
    fetch(`/api/tickets/${ticketId}/assign/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to assign ticket');
        }
        return response.json();
    })
    .then(data => {
        showToast('Ticket assigned successfully', 'success');
        // Refresh ticket list or update UI
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    })
    .catch(error => {
        console.error('Error assigning ticket:', error);
        showToast('Failed to assign ticket', 'error');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Initialize availability toggle
 */
function initAvailabilityToggle() {
    const availabilityToggle = document.querySelector('[data-action="toggle-availability"]');
    if (!availabilityToggle) return;
    
    availabilityToggle.addEventListener('click', function(e) {
        e.preventDefault();
        toggleAvailability();
    });
}

/**
 * Toggle technician availability
 */
function toggleAvailability() {
    showLoading();
    
    fetch('/api/technicians/toggle-availability/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to toggle availability');
        }
        return response.json();
    })
    .then(data => {
        showToast(data.message, 'success');
        
        // Update UI to reflect availability change
        const availabilityBadge = document.querySelector('.availability-badge');
        if (availabilityBadge) {
            if (data.is_available) {
                availabilityBadge.className = 'badge bg-success ms-2 availability-badge';
                availabilityBadge.textContent = 'Available';
            } else {
                availabilityBadge.className = 'badge bg-secondary ms-2 availability-badge';
                availabilityBadge.textContent = 'Unavailable';
            }
        }
    })
    .catch(error => {
        console.error('Error toggling availability:', error);
        showToast('Failed to update availability status', 'error');
    })
    .finally(() => {
        hideLoading();
    });
}

/**
 * Initialize quick filters
 */
function initQuickFilters() {
    document.querySelectorAll('.quick-filter').forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const filterType = this.getAttribute('data-filter');
            applyFilter(filterType);
        });
    });
}

/**
 * Apply filter to ticket list
 */
function applyFilter(filterType) {
    // Add active class to the selected filter
    document.querySelectorAll('.quick-filter').forEach(filter => {
        filter.classList.remove('active');
        if (filter.getAttribute('data-filter') === filterType) {
            filter.classList.add('active');
        }
    });
    
    // Apply filtering logic
    const ticketRows = document.querySelectorAll('.ticket-row');
    
    if (filterType === 'all') {
        ticketRows.forEach(row => row.style.display = '');
        return;
    }
    
    ticketRows.forEach(row => {
        const status = row.getAttribute('data-status');
        const priority = row.getAttribute('data-priority');
        
        if (filterType === status || filterType === priority) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Initialize charts
 */
function initCharts() {
    console.log('Initializing charts...');
    // Check if the performance chart element exists
    const performanceChartElement = document.getElementById('performanceChart');
    if (!performanceChartElement) {
        console.error('Chart element not found on page');
        return;
    }
    
    // Check if chart data is available in global scope (set in the template)
    if (typeof window.chartData === 'undefined' || window.chartData === null) {
        console.error('Chart data not found. Make sure it is properly passed from the backend.');
        performanceChartElement.innerHTML = '<div class="text-center py-5"><p class="text-muted">No performance data available</p></div>';
        return;
    }
    
    console.log('Chart data found:', window.chartData);
    
    try {
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.log('Chart.js not loaded, loading dynamically...');
            // If Chart.js is not loaded, dynamically load it
            loadChartJs().then(() => {
                console.log('Chart.js loaded dynamically, rendering chart...');
                renderPerformanceChart(performanceChartElement, window.chartData);
            });
        } else {
            console.log('Chart.js already loaded, rendering chart...');
            // Chart.js is already loaded, render the chart
            renderPerformanceChart(performanceChartElement, window.chartData);
        }
    } catch (error) {
        console.error('Error initializing charts:', error);
        // Show a message in the chart container
        performanceChartElement.innerHTML = '<div class="text-center py-5"><p class="text-muted">Could not load performance data</p></div>';
    }
}

/**
 * Dynamically load Chart.js if not already loaded
 */
function loadChartJs() {
    return new Promise((resolve, reject) => {
        // Check if it's already loaded
        if (typeof Chart !== 'undefined') {
            resolve();
            return;
        }
        
        // Create script element to load Chart.js from CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js';
        script.integrity = 'sha256-ErZ09KkZnzjpqcane4SCyyHsKAXMvID9/xwbl/Aq1pc=';
        script.crossOrigin = 'anonymous';
        
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Failed to load Chart.js'));
        
        document.head.appendChild(script);
    });
}

/**
 * Render the performance chart
 */
function renderPerformanceChart(chartElement, data) {
    // Create a new chart instance
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0 // Only show whole numbers
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });
}

/**
 * Initialize notifications
 */
function initNotifications() {
    // Check for new notifications periodically
    setInterval(() => {
        checkNotifications();
    }, 60000); // Check every minute
    
    // Initial check
    checkNotifications();
}

/**
 * Check for new notifications
 */
function checkNotifications() {
    fetch('/api/notifications/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.new_notifications > 0) {
            // Update notification badge
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                badge.textContent = data.new_notifications;
                badge.style.display = 'inline-block';
            }
            
            // Show notification for most recent one if we're allowed
            if (data.recent_notification && Notification.permission === 'granted') {
                new Notification('Support System', {
                    body: data.recent_notification.message,
                    icon: '/static/img/logo.png'
                });
            }
        }
    })
    .catch(error => {
        console.error('Error checking notifications:', error);
    });
}

/**
 * Initialize sortable tables
 */
function initSortableTables() {
    document.querySelectorAll('th[data-sort]').forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const columnIndex = Array.from(this.parentNode.children).indexOf(this);
            const sortDirection = this.getAttribute('data-sort-direction') === 'asc' ? 'desc' : 'asc';
            
            // Update sort direction attribute
            document.querySelectorAll('th[data-sort]').forEach(th => {
                th.removeAttribute('data-sort-direction');
                th.querySelector('.sort-icon')?.remove();
            });
            
            this.setAttribute('data-sort-direction', sortDirection);
            
            // Add sort icon
            const sortIcon = document.createElement('span');
            sortIcon.className = 'sort-icon ms-1';
            sortIcon.innerHTML = sortDirection === 'asc' ? '↑' : '↓';
            this.appendChild(sortIcon);
            
            // Sort the table
            sortTable(table, columnIndex, sortDirection);
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, columnIndex, sortDirection) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Parse as numbers if possible
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return sortDirection === 'asc' 
                ? parseFloat(aValue) - parseFloat(bValue)
                : parseFloat(bValue) - parseFloat(aValue);
        }
        
        // Otherwise compare as strings
        return sortDirection === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Reinsert rows in sorted order
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    // Assuming Bootstrap's tooltip functionality
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Show welcome message
 */
function showWelcomeMessage() {
    // Get current hour
    const hour = new Date().getHours();
    let greeting = 'Hello';
    
    if (hour < 12) {
        greeting = 'Good morning';
    } else if (hour < 18) {
        greeting = 'Good afternoon';
    } else {
        greeting = 'Good evening';
    }
    
    // Get user name
    const userName = document.querySelector('.user-name')?.textContent || 'Technician';
    
    showToast(`${greeting}, ${userName}! Welcome to your dashboard.`, 'info', 5000);
}

/**
 * Show loading indicator
 */
function showLoading() {
    // Create loading overlay if it doesn't exist
    if (!document.querySelector('.loading-overlay')) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        document.body.appendChild(overlay);
    } else {
        document.querySelector('.loading-overlay').style.display = 'flex';
    }
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    if (!document.querySelector('.toast-container')) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast show bg-${type} text-white`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <strong class="me-auto">Notification</strong>
            <small>Just now</small>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    // Add toast to container
    document.querySelector('.toast-container').appendChild(toast);
    
    // Remove toast after duration
    setTimeout(() => {
        const toastElement = document.getElementById(toastId);
        if (toastElement) {
            toastElement.remove();
        }
    }, duration);
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    return cookieValue;
} 