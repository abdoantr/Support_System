document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const password1 = document.getElementById('password1');
    const password2 = document.getElementById('password2');
    const togglePassword1 = document.getElementById('togglePassword1');
    const togglePassword2 = document.getElementById('togglePassword2');
    const submitBtn = document.getElementById('submitBtn');
    const acceptTermsBtn = document.getElementById('acceptTerms');
    const termsCheckbox = document.getElementById('terms');
    
    // Password validation criteria
    const criteria = {
        length: { regex: /.{8,}/, text: 'At least 8 characters' },
        letter: { regex: /[A-Za-z]/, text: 'At least one letter' },
        number: { regex: /[0-9]/, text: 'At least one number' }
    };
    
    // Create password feedback elements
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'password-feedback';
    password1.parentNode.parentNode.appendChild(feedbackDiv);
    
    Object.keys(criteria).forEach(key => {
        const item = document.createElement('div');
        item.className = 'feedback-item';
        item.innerHTML = `<i class="fas fa-times-circle"></i> ${criteria[key].text}`;
        item.id = `feedback-${key}`;
        feedbackDiv.appendChild(item);
    });
    
    // Password toggle functionality
    function togglePasswordVisibility(inputField, toggleBtn) {
        const type = inputField.type === 'password' ? 'text' : 'password';
        inputField.type = type;
        toggleBtn.innerHTML = `<i class="fas fa-eye${type === 'password' ? '' : '-slash'}"></i>`;
    }
    
    togglePassword1.addEventListener('click', () => togglePasswordVisibility(password1, togglePassword1));
    togglePassword2.addEventListener('click', () => togglePasswordVisibility(password2, togglePassword2));
    
    // Password strength meter
    function updatePasswordStrength(password) {
        const meter = document.querySelector('.password-strength-meter .meter');
        const container = meter.parentNode;
        let strength = 0;
        
        // Remove previous strength classes
        container.classList.remove('strength-weak', 'strength-medium', 'strength-strong');
        
        if (password.length >= 8) strength++;
        if (/[A-Za-z]/.test(password) && /[0-9]/.test(password)) strength++;
        if (/[!@#$%^&*]/.test(password)) strength++;
        
        // Update strength meter
        if (password.length === 0) {
            container.classList.remove('strength-weak', 'strength-medium', 'strength-strong');
        } else if (strength === 1) {
            container.classList.add('strength-weak');
        } else if (strength === 2) {
            container.classList.add('strength-medium');
        } else {
            container.classList.add('strength-strong');
        }
    }
    
    // Real-time password validation
    password1.addEventListener('input', function() {
        const value = this.value;
        let isValid = true;
        
        // Update criteria feedback
        Object.keys(criteria).forEach(key => {
            const item = document.getElementById(`feedback-${key}`);
            const meets = criteria[key].regex.test(value);
            item.innerHTML = `<i class="fas fa-${meets ? 'check-circle' : 'times-circle'}"></i> ${criteria[key].text}`;
            item.className = `feedback-item ${meets ? 'valid' : 'invalid'}`;
            if (!meets) isValid = false;
        });
        
        // Update password strength meter
        updatePasswordStrength(value);
        
        // Update password field validity
        this.setCustomValidity(isValid ? '' : 'Please meet all password requirements');
        
        // Update confirm password validation
        if (password2.value) {
            password2.dispatchEvent(new Event('input'));
        }
    });
    
    // Confirm password validation
    password2.addEventListener('input', function() {
        const isMatch = this.value === password1.value;
        this.setCustomValidity(isMatch ? '' : 'Passwords do not match');
        this.classList.toggle('is-invalid', !isMatch && this.value.length > 0);
    });
    
    // Terms and conditions acceptance
    if (acceptTermsBtn) {
        acceptTermsBtn.addEventListener('click', function() {
            termsCheckbox.checked = true;
            termsCheckbox.dispatchEvent(new Event('change'));
            bootstrap.Modal.getInstance(document.getElementById('termsModal')).hide();
        });
    }
    
    // Form validation
    form.addEventListener('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        this.classList.add('was-validated');
        
        // Additional password validation
        if (password1.value !== password2.value) {
            e.preventDefault();
            password2.setCustomValidity('Passwords do not match');
            password2.reportValidity();
            return;
        }
        
        // Check password criteria
        let isValid = true;
        Object.keys(criteria).forEach(key => {
            if (!criteria[key].regex.test(password1.value)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            password1.setCustomValidity('Please meet all password requirements');
            password1.reportValidity();
        }
    });
});
