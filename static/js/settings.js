/**
 * Settings functionality for Support System
 * Handles settings updates for notifications, preferences, appearance, privacy, and system settings
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get all settings forms
    const notificationsForm = document.getElementById('notificationsForm');
    const preferencesForm = document.getElementById('preferencesForm');
    const appearanceForm = document.getElementById('appearanceForm');
    const privacyForm = document.getElementById('privacyForm');
    const systemForm = document.getElementById('systemForm');
    
    // Add event listeners to forms
    if (notificationsForm) {
        notificationsForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            handleSettingsUpdate(e, 'notifications');
        });
    }
    
    if (preferencesForm) {
        preferencesForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            handleSettingsUpdate(e, 'preferences');
        });
    }
    
    if (appearanceForm) {
        appearanceForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            handleSettingsUpdate(e, 'appearance');
        });
    }
    
    if (privacyForm) {
        privacyForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            handleSettingsUpdate(e, 'privacy');
        });
    }
    
    if (systemForm) {
        systemForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            handleSettingsUpdate(e, 'system');
        });
    }
    
    // Handle tab navigation persistence
    const hash = window.location.hash;
    if (hash) {
        const tab = document.querySelector(`a[href="${hash}"]`);
        if (tab) {
            const tabInstance = new bootstrap.Tab(tab);
            tabInstance.show();
        }
    }
    
    // Update URL hash when tab changes
    const tabLinks = document.querySelectorAll('a[data-bs-toggle="list"]');
    tabLinks.forEach(tabLink => {
        tabLink.addEventListener('shown.bs.tab', function(e) {
            window.location.hash = e.target.getAttribute('href');
        });
    });

    // Initialize theme preview when page loads
    const themeSelect = document.querySelector('select[name="theme"]');
    if (themeSelect) {
        updateThemePreview(themeSelect.value);
    }
});

/**
 * Handle settings form submission
 * @param {Event} event - The submit event
 * @param {string} settingType - The type of setting being updated
 */
function handleSettingsUpdate(event, settingType) {
    const form = event.target;
    const formData = new FormData(form);
    
    // Show a loading indicator
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    
    // Convert form data to JSON
    const formJson = {};
    formData.forEach((value, key) => {
        // Handle checkboxes
        if (form.elements[key] && form.elements[key].type === 'checkbox') {
            formJson[key] = form.elements[key].checked;
        } else {
            formJson[key] = value;
        }
    });
    
    // Determine the endpoint based on setting type
    let endpoint;
    switch (settingType) {
        case 'notifications':
            endpoint = '/settings/notifications/';
            break;
        case 'preferences':
            endpoint = '/settings/preferences/';
            break;
        case 'appearance':
            endpoint = '/settings/appearance/';
            break;
        case 'privacy':
            endpoint = '/settings/privacy/';
            break;
        case 'system':
            endpoint = '/settings/system/';
            break;
        default:
            endpoint = '/settings/';
    }
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formJson)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Reset the button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        
        if (data.success) {
            showAlert('success', data.message);
        } else {
            showAlert('danger', data.message || `Failed to update ${settingType} settings`);
        }
    })
    .catch(error => {
        // Reset the button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        
        console.error('Error:', error);
        showAlert('danger', `Failed to update ${settingType} settings`);
    });
}

/**
 * Reset settings to default values
 * @param {string} settingType - The type of setting to reset
 */
function resetSettings(settingType) {
    if (!confirm(`Are you sure you want to reset your ${settingType} settings to default values?`)) {
        return;
    }
    
    // Get the reset button and show loading state
    const resetBtn = document.querySelector(`.reset-settings-btn[onclick="resetSettings('${settingType}')"]`);
    const originalText = resetBtn.textContent;
    resetBtn.disabled = true;
    resetBtn.textContent = "Resetting...";
    
    // Determine the endpoint based on setting type
    let endpoint;
    switch (settingType) {
        case 'notifications':
            endpoint = '/settings/reset-notifications/';
            break;
        case 'preferences':
            endpoint = '/settings/reset-preferences/';
            break;
        case 'appearance':
            endpoint = '/settings/reset-appearance/';
            break;
        case 'privacy':
            endpoint = '/settings/reset-privacy/';
            break;
        case 'system':
            endpoint = '/settings/reset-system/';
            break;
        default:
            endpoint = '/settings/reset-notifications/';
    }
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Reset button state
        resetBtn.disabled = false;
        resetBtn.textContent = originalText;
        
        if (data.success) {
            showAlert('success', data.message);
            // Reload the page to show default settings
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert('danger', data.message || `Failed to reset ${settingType} settings`);
        }
    })
    .catch(error => {
        // Reset button state
        resetBtn.disabled = false;
        resetBtn.textContent = originalText;
        
        console.error('Error:', error);
        showAlert('danger', `Failed to reset ${settingType} settings`);
    });
}

/**
 * Update theme preview based on selected theme
 * @param {string} theme - The selected theme (light, dark, auto)
 */
function updateThemePreview(theme) {
    // Remove theme preview containers if they exist
    const existingPreviews = document.querySelector('.theme-previews');
    if (existingPreviews) {
        existingPreviews.remove();
    }
    
    // Create new theme preview containers
    const previewsContainer = document.createElement('div');
    previewsContainer.className = 'theme-previews d-flex gap-3 mb-4';
    
    // Create light theme preview
    const lightPreview = document.createElement('div');
    lightPreview.className = `theme-preview light ${theme === 'light' ? 'active' : ''}`;
    lightPreview.innerHTML = `
        <div class="header"></div>
        <div class="content">
            <div class="line"></div>
            <div class="line" style="width: 70%"></div>
        </div>
    `;
    
    // Create dark theme preview
    const darkPreview = document.createElement('div');
    darkPreview.className = `theme-preview dark ${theme === 'dark' ? 'active' : ''}`;
    darkPreview.innerHTML = `
        <div class="header"></div>
        <div class="content">
            <div class="line"></div>
            <div class="line" style="width: 70%"></div>
        </div>
    `;
    
    // Add previews to container
    previewsContainer.appendChild(lightPreview);
    previewsContainer.appendChild(darkPreview);
    
    // Insert previews after theme select
    const themeSelect = document.querySelector('select[name="theme"]');
    if (themeSelect) {
        themeSelect.parentNode.insertBefore(previewsContainer, themeSelect.nextSibling);
    }
    
    // Add click handlers to previews
    lightPreview.addEventListener('click', function() {
        themeSelect.value = 'light';
        updateThemePreview('light');
    });
    
    darkPreview.addEventListener('click', function() {
        themeSelect.value = 'dark';
        updateThemePreview('dark');
    });
}

// Add any missing utility functions
if (typeof showLoading !== 'function') {
    function showLoading() {
        const loadingEl = document.createElement('div');
        loadingEl.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-white bg-opacity-75';
        loadingEl.style.zIndex = '9999';
        loadingEl.id = 'loadingIndicator';
        loadingEl.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        document.body.appendChild(loadingEl);
    }
}

if (typeof hideLoading !== 'function') {
    function hideLoading() {
        const loadingEl = document.getElementById('loadingIndicator');
        if (loadingEl) {
            loadingEl.remove();
        }
    }
}

/**
 * Show an alert message
 * @param {string} type - The type of alert (success, danger, warning, info)
 * @param {string} message - The message to display
 */
function showAlert(type, message) {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.settings-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create a new alert
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show settings-alert`;
    alertEl.role = 'alert';
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find the active tab content and insert the alert at the top
    const activeTab = document.querySelector('.tab-pane.active');
    if (activeTab) {
        const card = activeTab.querySelector('.card');
        if (card) {
            card.insertBefore(alertEl, card.firstChild);
            // Scroll to the alert
            card.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    } else {
        // Fallback - add to the body
        document.body.appendChild(alertEl);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertEl.classList.remove('show');
        setTimeout(() => alertEl.remove(), 300);
    }, 5000);
}

if (typeof getCookie !== 'function') {
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
} 