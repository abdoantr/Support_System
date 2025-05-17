/**
 * Profile functionality for Support System
 * Handles profile updates, picture uploads, and other profile-related actions
 */

/**
 * Check password strength and update the strength meter
 * @param {string} password - The password to check
 * @returns {number} - Strength level (0-2)
 */
function checkPasswordStrength(password) {
    // Add password strength meter HTML if it doesn't exist
    const passwordField = document.getElementById('new_password1');
    let meterContainer = document.getElementById('password-strength-container');
    
    if (!meterContainer && passwordField) {
        meterContainer = document.createElement('div');
        meterContainer.id = 'password-strength-container';
        meterContainer.innerHTML = `
            <div class="password-strength-meter">
                <div id="password-strength-bar"></div>
            </div>
            <small id="password-strength-text" class="form-text text-muted"></small>
        `;
        passwordField.parentNode.insertBefore(meterContainer, passwordField.nextSibling);
    }
    
    if (!password || password.length === 0) {
        if (meterContainer) {
            const bar = document.getElementById('password-strength-bar');
            const text = document.getElementById('password-strength-text');
            if (bar) bar.style.width = '0';
            if (text) text.textContent = '';
        }
        return 0;
    }
    
    // Calculate strength
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    
    // Character variety check
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    
    // Calculate final score (0-2)
    let score = 0;
    if (strength >= 3) score = 1;
    if (strength >= 5) score = 2;
    
    // Update UI
    if (meterContainer) {
        const bar = document.getElementById('password-strength-bar');
        const text = document.getElementById('password-strength-text');
        
        if (bar) {
            bar.style.width = `${(score + 1) * 33}%`;
            bar.className = '';
            if (score === 0) bar.classList.add('password-strength-weak');
            if (score === 1) bar.classList.add('password-strength-medium');
            if (score === 2) bar.classList.add('password-strength-strong');
        }
        
        if (text) {
            if (score === 0) text.textContent = 'Weak password';
            if (score === 1) text.textContent = 'Medium strength password';
            if (score === 2) text.textContent = 'Strong password';
        }
    }
    
    return score;
}

document.addEventListener('DOMContentLoaded', function() {
    // Profile picture upload handling
    const profilePictureInput = document.getElementById('profilePicture');
    if (profilePictureInput) {
        profilePictureInput.addEventListener('change', handleProfilePictureUpload);
    }

    // Profile update form handling
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }

    // Password change form handling
    const passwordForm = document.getElementById('passwordChangeForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', handlePasswordChange);
    }

    // Initialize password strength meter
    const passwordField = document.getElementById('new_password1');
    if (passwordField) {
        passwordField.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }
});

/**
 * Handle profile picture upload
 * @param {Event} event - The change event
 */
function handleProfilePictureUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
    if (!validTypes.includes(file.type)) {
        showAlert('danger', 'Please select a valid image file (JPEG, PNG, or GIF)');
        return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showAlert('danger', 'Image file size must be less than 5MB');
        return;
    }

    // Create form data and send request
    const formData = new FormData();
    formData.append('profile_picture', file);
    
    // Show loading indicator
    const loadingEl = document.createElement('div');
    loadingEl.className = 'profile-loading';
    loadingEl.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    
    const imgContainer = document.querySelector('.position-relative.mb-3');
    if (imgContainer) {
        imgContainer.appendChild(loadingEl);
    }
    
    fetch('/profile/update-picture/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Remove loading indicator
        const loadingEl = document.querySelector('.profile-loading');
        if (loadingEl) {
            loadingEl.remove();
        }
        
        if (data.success) {
            showAlert('success', data.message);
            // Refresh the page to show the new profile picture
            window.location.reload();
        } else {
            showAlert('danger', data.message || 'Failed to update profile picture');
        }
    })
    .catch(error => {
        // Remove loading indicator
        const loadingEl = document.querySelector('.profile-loading');
        if (loadingEl) {
            loadingEl.remove();
        }
        
        console.error('Error:', error);
        showAlert('danger', 'Failed to update profile picture');
    });
}

/**
 * Handle profile update form submission
 * @param {Event} event - The submit event
 */
function handleProfileUpdate(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Show a loading indicator on the button
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    
    fetch('/profile/update/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
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
            // Show success message
            showAlert('success', data.message);
            
            // Close the modal
            const modalElement = document.getElementById('editProfileModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
            
            // Get values from response if available, otherwise use form data
            const updatedFields = data.updated_fields || {};
            const firstName = updatedFields.first_name || formData.get('first_name');
            const lastName = updatedFields.last_name || formData.get('last_name');
            const phoneNumber = updatedFields.phone_number || formData.get('phone_number');
            const department = updatedFields.department || formData.get('department');
            
            // Update display names without page reload
            const displayName = document.querySelector('.profile-info h5');
            if (displayName) {
                displayName.textContent = `${firstName} ${lastName}`;
            }
            
            // Update phone and department information using straightforward DOM traversal
            console.log("Updating profile display with new data");
            
            // Find all elements with 'text-muted' class that contain the labels we're looking for
            const labelElements = document.querySelectorAll('.small.text-muted');
            let phoneDiv = null;
            let departmentDiv = null;
            
            // Iterate through all label elements to find our target fields
            labelElements.forEach(label => {
                const text = label.textContent.trim();
                console.log("Found label:", text);
                
                // Get the parent element (should be .mb-3) and then find the value div
                const parent = label.closest('.mb-3');
                if (!parent) return;
                
                const valueDiv = parent.querySelector('div:not(.small)');
                if (!valueDiv) return;
                
                if (text === 'Phone') {
                    phoneDiv = valueDiv;
                } else if (text === 'Department') {
                    departmentDiv = valueDiv;
                }
            });
            
            // Update the phone display - now correctly mapped to user.phone
            if (phoneDiv) {
                phoneDiv.textContent = phoneNumber ? phoneNumber : 'Not provided';
                console.log("Updated phone display to:", phoneDiv.textContent);
            } else {
                console.warn("Could not find phone display element");
            }
            
            // Update the department display - now correctly mapped to profile.department
            if (departmentDiv) {
                if (department) {
                    // Remove any nested elements and just set text directly
                    departmentDiv.innerHTML = '';
                    departmentDiv.textContent = department;
                } else {
                    departmentDiv.innerHTML = 'Not specified';
                }
                console.log("Updated department display to:", departmentDiv.textContent);
            } else {
                console.warn("Could not find department display element");
            }
        } else {
            showAlert('danger', data.message || 'Failed to update profile');
        }
    })
    .catch(error => {
        // Reset the button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        
        console.error('Error:', error);
        showAlert('danger', 'Failed to update profile');
    });
}

/**
 * Handle password change form submission
 * @param {Event} event - The submit event
 */
function handlePasswordChange(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Get form values
    const currentPassword = formData.get('current_password');
    const newPassword = formData.get('new_password1');
    const confirmPassword = formData.get('new_password2');
    
    // Validate input
    if (!currentPassword || !newPassword || !confirmPassword) {
        showAlert('danger', 'All password fields are required');
        return;
    }
    
    // Validate password match
    if (newPassword !== confirmPassword) {
        showAlert('danger', 'New passwords do not match');
        return;
    }
    
    // Check password strength
    const strengthLevel = checkPasswordStrength(newPassword);
    if (strengthLevel === 0) {
        if (!confirm('Your password is weak. It should be at least 8 characters and include uppercase, lowercase, numbers, and special characters. Do you want to continue anyway?')) {
            return;
        }
    }
    
    // Show a loading indicator on the button
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Changing...';
    
    fetch('/profile/change-password/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
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
            // Clear the form
            form.reset();
            
            // Close the modal
            const modalElement = document.getElementById('changePasswordModal');
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
        } else {
            showAlert('danger', data.message || 'Failed to change password');
        }
    })
    .catch(error => {
        // Reset the button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
        
        console.error('Error:', error);
        showAlert('danger', 'Failed to change password');
    });
}

/**
 * Show an alert message
 * @param {string} type - The type of alert (success, danger, warning, info)
 * @param {string} message - The message to display
 */
function showAlert(type, message) {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.profile-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create a new alert
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show profile-alert`;
    alertEl.role = 'alert';
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert the alert at the top of the profile section
    const profileSection = document.querySelector('.container-fluid.py-4');
    if (profileSection) {
        profileSection.insertBefore(alertEl, profileSection.firstChild);
        // Scroll to the alert
        profileSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

/**
 * Get the CSRF token from cookies
 * @returns {string} The CSRF token
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Update profile picture when file is selected
 * @param {HTMLInputElement} input - The file input element
 */
function updateProfilePicture(input) {
    if (input.files && input.files[0]) {
        handleProfilePictureUpload({target: input});
    }
} 