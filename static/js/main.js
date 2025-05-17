// Show loading spinner
function showLoading() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideLoading() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
});

// Handle sidebar toggle on mobile
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
        });
    }
});

// Handle form submissions with AJAX
document.addEventListener('submit', function(e) {
    const form = e.target;
    if (form.hasAttribute('data-ajax')) {
        e.preventDefault();
        showLoading();

        fetch(form.action, {
            method: form.method,
            body: new FormData(form),
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showAlert('success', data.message);
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            } else {
                showAlert('danger', data.message || 'An error occurred');
            }
        })
        .catch(error => {
            hideLoading();
            showAlert('danger', 'An error occurred');
            console.error('Error:', error);
        });
    }
});

// Show alert message
function showAlert(type, message) {
    const alertContainer = document.getElementById('alertContainer');
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        alertContainer.appendChild(alert);
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Get CSRF token from cookies
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

// Live search functionality
function initLiveSearch() {
    const searchInput = document.querySelector('[data-live-search]');
    if (searchInput) {
        let timeout = null;
        searchInput.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const url = new URL(window.location);
                url.searchParams.set('search', this.value);
                history.pushState({}, '', url);
                
                fetch(`${url.pathname}${url.search}`)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newContent = doc.querySelector('[data-content]');
                        const currentContent = document.querySelector('[data-content]');
                        if (newContent && currentContent) {
                            currentContent.innerHTML = newContent.innerHTML;
                        }
                    });
            }, 300);
        });
    }
}

// Infinite scroll
function initInfiniteScroll() {
    const container = document.querySelector('[data-infinite-scroll]');
    if (container) {
        let page = 1;
        let loading = false;

        window.addEventListener('scroll', function() {
            if (loading) return;

            const threshold = 100;
            if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - threshold) {
                loading = true;
                page++;

                const url = new URL(window.location);
                url.searchParams.set('page', page);

                fetch(url)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newItems = doc.querySelector('[data-infinite-scroll]');
                        if (newItems && newItems.children.length) {
                            container.appendChild(newItems);
                            loading = false;
                        }
                    });
            }
        });
    }
}

// Real-time notifications using WebSocket
function initWebSocket() {
    const ws = new WebSocket(`ws://${window.location.host}/ws/notifications/`);
    
    ws.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === 'notification') {
            showNotification(data.message);
        }
    };

    ws.onclose = function() {
        console.log('WebSocket closed, attempting to reconnect...');
        setTimeout(initWebSocket, 1000);
    };
}

// Show browser notification
function showNotification(message) {
    if (Notification.permission === 'granted') {
        new Notification('Support System', { body: message });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification('Support System', { body: message });
            }
        });
    }
}

// Initialize all interactive features
document.addEventListener('DOMContentLoaded', function() {
    initLiveSearch();
    initInfiniteScroll();
    initWebSocket();
});

// Theme switcher
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

// File upload preview
function previewFile(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        const preview = document.querySelector(`[data-preview="${input.id}"]`);
        
        reader.onload = function(e) {
            if (preview) {
                if (input.accept.includes('image')) {
                    preview.innerHTML = `<img src="${e.target.result}" class="img-fluid">`;
                } else {
                    preview.innerHTML = `<i class="fas fa-file"></i> ${input.files[0].name}`;
                }
            }
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Dynamic form validation
function validateForm(form) {
    const inputs = form.querySelectorAll('[data-validate]');
    let isValid = true;

    inputs.forEach(input => {
        const validationType = input.dataset.validate;
        const value = input.value.trim();
        let error = null;

        switch (validationType) {
            case 'required':
                if (!value) error = 'This field is required';
                break;
            case 'email':
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                    error = 'Please enter a valid email address';
                }
                break;
            case 'phone':
                if (!/^\+?[\d\s-]{10,}$/.test(value)) {
                    error = 'Please enter a valid phone number';
                }
                break;
        }

        const errorElement = input.parentElement.querySelector('.invalid-feedback');
        if (error) {
            isValid = false;
            input.classList.add('is-invalid');
            if (errorElement) {
                errorElement.textContent = error;
            } else {
                const div = document.createElement('div');
                div.className = 'invalid-feedback';
                div.textContent = error;
                input.parentElement.appendChild(div);
            }
        } else {
            input.classList.remove('is-invalid');
            if (errorElement) errorElement.remove();
        }
    });

    return isValid;
}
