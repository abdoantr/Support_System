/**
 * Theme functionality for Support System
 * Handles theme switching and preferences
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if user has a theme preference
    const currentTheme = localStorage.getItem('theme') || 'light';
    applyTheme(currentTheme);
    
    // Add theme toggle listener if toggle element exists
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.body.classList.contains('dark-theme') ? 'light' : 'dark';
            applyTheme(currentTheme);
            localStorage.setItem('theme', currentTheme);
        });
    }
});

/**
 * Apply theme to the document
 * @param {string} theme - The theme to apply ('light' or 'dark')
 */
function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
        updateThemeColors('#212529', '#f8f9fa');
    } else {
        document.body.classList.remove('dark-theme');
        updateThemeColors('#f8f9fa', '#212529');
    }
    
    // Update any theme toggle buttons
    const themeToggles = document.querySelectorAll('.theme-toggle-icon');
    themeToggles.forEach(toggle => {
        if (theme === 'dark') {
            toggle.classList.replace('fa-moon', 'fa-sun');
        } else {
            toggle.classList.replace('fa-sun', 'fa-moon');
        }
    });
}

/**
 * Update theme colors for meta tags
 * @param {string} bgColor - Background color
 * @param {string} textColor - Text color
 */
function updateThemeColors(bgColor, textColor) {
    // Update theme-color meta tag if it exists
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        metaThemeColor.setAttribute('content', bgColor);
    }
} 