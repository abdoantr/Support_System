document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('serviceRequestForm');
    const fileInput = form.querySelector('input[type="file"]');
    
    // File Upload Validation
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        const maxFileSize = 5 * 1024 * 1024; // 5MB
        let totalSize = 0;
        let invalidFiles = [];
        
        for (let file of files) {
            totalSize += file.size;
            if (file.size > maxFileSize) {
                invalidFiles.push(file.name);
            }
        }
        
        if (invalidFiles.length > 0) {
            alert(`The following files exceed the 5MB limit:\n${invalidFiles.join('\n')}`);
            e.target.value = '';
            return;
        }
        
        if (files.length > 5) {
            alert('You can only upload up to 5 files.');
            e.target.value = '';
            return;
        }
        
        // Update file list display
        updateFileList(files);
    });
    
    // Dynamic Form Validation
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (validateForm()) {
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
            
            // Prepare form data
            const formData = new FormData(form);
            
            // Submit form
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccessMessage(data.message);
                    form.reset();
                } else {
                    showErrorMessage(data.message);
                }
            })
            .catch(error => {
                showErrorMessage('An error occurred. Please try again.');
                console.error('Error:', error);
            })
            .finally(() => {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
        }
    });
    
    // Form Validation
    function validateForm() {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                highlightError(field);
            } else {
                removeError(field);
            }
        });
        
        // Email validation
        const emailField = form.querySelector('input[type="email"]');
        if (emailField.value && !isValidEmail(emailField.value)) {
            isValid = false;
            highlightError(emailField, 'Please enter a valid email address');
        }
        
        // Phone validation (if provided)
        const phoneField = form.querySelector('input[name="phone"]');
        if (phoneField.value && !isValidPhone(phoneField.value)) {
            isValid = false;
            highlightError(phoneField, 'Please enter a valid phone number');
        }
        
        return isValid;
    }
    
    // Helper Functions
    function updateFileList(files) {
        const fileListContainer = document.createElement('div');
        fileListContainer.className = 'file-list mt-2';
        
        for (let file of files) {
            const fileSize = formatFileSize(file.size);
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <i class="fas fa-file me-2"></i>
                <span>${file.name}</span>
                <small class="text-muted">(${fileSize})</small>
            `;
            fileListContainer.appendChild(fileItem);
        }
        
        const existingFileList = fileInput.parentElement.querySelector('.file-list');
        if (existingFileList) {
            existingFileList.remove();
        }
        
        fileInput.parentElement.appendChild(fileListContainer);
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
    
    function isValidPhone(phone) {
        return /^[\d\s\-\+\(\)]{10,}$/.test(phone);
    }
    
    function highlightError(field, message = 'This field is required') {
        field.classList.add('is-invalid');
        
        let feedback = field.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentElement.appendChild(feedback);
        }
        feedback.textContent = message;
    }
    
    function removeError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }
    
    function showSuccessMessage(message) {
        const alert = createAlert('success', message);
        form.prepend(alert);
        scrollToTop();
        setTimeout(() => alert.remove(), 5000);
    }
    
    function showErrorMessage(message) {
        const alert = createAlert('danger', message);
        form.prepend(alert);
        scrollToTop();
        setTimeout(() => alert.remove(), 5000);
    }
    
    function createAlert(type, message) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        return alert;
    }
    
    function scrollToTop() {
        window.scrollTo({
            top: form.offsetTop - 100,
            behavior: 'smooth'
        });
    }
    
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
});
