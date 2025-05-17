/**
 * Dashboard functionality script for Support System
 * Handles toggle availability and dashboard features
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to availability toggle button if it exists
    const toggleBtn = document.querySelector('button[onclick="toggleAvailability()"]');
    if (toggleBtn) {
        toggleBtn.onclick = null; // Remove inline onclick
        toggleBtn.addEventListener('click', toggleAvailability);
    }
});

/**
 * Toggle technician availability status
 */
function toggleAvailability() {
    showLoading();
    
    // Get the CSRF token URL from a meta tag
    const csrfToken = getCookie('csrftoken');
    const toggleUrl = document.querySelector('meta[name="toggle-availability-url"]')?.getAttribute('content');
    
    if (!toggleUrl) {
        hideLoading();
        showAlert('danger', 'Toggle URL not found');
        return;
    }
    
    fetch(toggleUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        showAlert('success', data.message);
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showAlert('danger', 'Failed to update availability');
    });
}

/**
 * Get cookie value by name
 * @param {string} name - Cookie name
 * @return {string} Cookie value
 */
function getCookie(name) {
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

/**
 * Show loading overlay
 */
function showLoading() {
    // Remove any existing loading overlay first
    hideLoading();
    
    const loadingEl = document.createElement('div');
    loadingEl.id = 'loading-overlay';
    loadingEl.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    loadingEl.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,255,255,0.7);display:flex;justify-content:center;align-items:center;z-index:9999;';
    document.body.appendChild(loadingEl);
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const loadingEl = document.getElementById('loading-overlay');
    if (loadingEl) {
        loadingEl.remove();
    }
}

/**
 * Show alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {string} message - Alert message
 */
function showAlert(type, message) {
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertEl.setAttribute('role', 'alert');
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertEl.style.zIndex = '9999';
    document.body.appendChild(alertEl);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertEl);
        bsAlert.close();
    }, 5000);
} 