/**
 * Contact form validation script for Support System
 * Handles form validation and provides visual feedback
 */

document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    (function () {
        'use strict'
        
        // Fetch all forms with the needs-validation class
        var forms = document.querySelectorAll('.needs-validation')
        
        // Loop over each form and apply validation
        Array.prototype.slice.call(forms)
            .forEach(function (form) {
                // Add submit event handler
                form.addEventListener('submit', function (event) {
                    if (!form.checkValidity()) {
                        event.preventDefault()
                        event.stopPropagation()
                    } else {
                        // If form is valid, show loading state
                        const submitBtn = form.querySelector('button[type="submit"]');
                        if (submitBtn) {
                            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Sending...';
                            submitBtn.disabled = true;
                        }
                    }
                    
                    form.classList.add('was-validated')
                }, false)
                
                // Add input event handlers for real-time validation feedback
                Array.from(form.elements).forEach(function (input) {
                    input.addEventListener('input', function () {
                        if (input.checkValidity()) {
                            input.classList.remove('is-invalid');
                            input.classList.add('is-valid');
                        } else {
                            input.classList.remove('is-valid');
                            if (input.value !== '') {
                                input.classList.add('is-invalid');
                            }
                        }
                    });
                });
            })
    })()
}); 