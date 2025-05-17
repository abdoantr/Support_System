/**
 * Header animation script for Support System
 * Controls floating header behavior on scroll
 */

document.addEventListener('DOMContentLoaded', function() {
    let lastScrollTop = 0;
    const header = document.querySelector('.floating-header');
    
    window.addEventListener('scroll', () => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add/remove compact class based on scroll position
        if (scrollTop > 50) {
            header.classList.add('compact');
        } else {
            header.classList.remove('compact');
        }
        
        // Hide/show header based on scroll direction
        if (scrollTop > lastScrollTop && scrollTop > 300) {
            header.classList.add('hidden');
        } else {
            header.classList.remove('hidden');
        }
        
        lastScrollTop = scrollTop;
    });
}); 