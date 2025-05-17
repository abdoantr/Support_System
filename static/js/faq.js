document.addEventListener('DOMContentLoaded', function() {
    // FAQ Search Functionality
    const searchInput = document.getElementById('faqSearch');
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        
        accordionItems.forEach(item => {
            const question = item.querySelector('.accordion-button').textContent.toLowerCase();
            const answer = item.querySelector('.accordion-body').textContent.toLowerCase();
            
            if (question.includes(searchTerm) || answer.includes(searchTerm)) {
                item.style.display = '';
                // Highlight matching text
                if (searchTerm) {
                    highlightText(item, searchTerm);
                } else {
                    removeHighlight(item);
                }
            } else {
                item.style.display = 'none';
            }
        });
        
        // Show/hide sections based on search results
        document.querySelectorAll('.faq-section').forEach(section => {
            const visibleItems = section.querySelectorAll('.accordion-item[style=""]').length;
            section.style.display = visibleItems ? '' : 'none';
        });
    });
    
    // Category Navigation
    const categoryCards = document.querySelectorAll('.category-card');
    categoryCards.forEach(card => {
        card.addEventListener('click', function() {
            const category = this.dataset.category;
            const section = document.getElementById(category);
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });
    
    // Text Highlighting
    function highlightText(element, searchTerm) {
        const question = element.querySelector('.accordion-button');
        const answer = element.querySelector('.accordion-body');
        
        question.innerHTML = question.textContent.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<mark>${match}</mark>`
        );
        
        answer.innerHTML = answer.textContent.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<mark>${match}</mark>`
        );
    }
    
    function removeHighlight(element) {
        const question = element.querySelector('.accordion-button');
        const answer = element.querySelector('.accordion-body');
        
        question.innerHTML = question.textContent;
        answer.innerHTML = answer.textContent;
    }
    
    // Track FAQ interactions
    const accordions = document.querySelectorAll('.accordion-button');
    accordions.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('collapsed')) {
                const question = this.textContent.trim();
                trackFAQInteraction(question);
            }
        });
    });
    
    function trackFAQInteraction(question) {
        // Send interaction data to backend
        fetch('/api/faq/track/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                question: question,
                interaction_type: 'view'
            })
        });
    }
    
    // Helper function to get CSRF token
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
