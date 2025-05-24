/**
 * Settings functionality for Support System
 * Handles settings updates for notifications, preferences, appearance, privacy, and system settings
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get all settings forms
    const notificationsForm = document.getElementById('notificationsForm');
    const preferencesForm = document.getElementById('preferencesForm');
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

// Note: This file depends on utility functions from utils.js:
// - getCookie()
// - showLoading()
// - hideLoading()
// - showAlert()