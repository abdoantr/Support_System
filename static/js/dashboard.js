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

// Note: This file depends on utility functions from utils.js:
// - getCookie()
// - showLoading()
// - hideLoading()
// - showAlert()