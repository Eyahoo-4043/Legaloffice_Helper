/**
 * Main JavaScript file for National Assembly search application
 */

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    setupEventListeners();
});

/**
 * Set up event listeners for the application
 */
function setupEventListeners() {
    // Info icon click for source information (API sources)
    const infoIcon = document.querySelector('.info-icon');
    if (infoIcon) {
        infoIcon.addEventListener('click', function() {
            const apiSources = document.querySelector('.api-sources');
            if (apiSources) {
                if (apiSources.style.display === 'none') {
                    apiSources.style.display = 'block';
                } else {
                    apiSources.style.display = 'none';
                }
            }
        });
    }
    
    // Handle tab clicks
    const tabItems = document.querySelectorAll('.tab-item');
    tabItems.forEach(tab => {
        tab.addEventListener('click', function() {
            navigateToTab(this.dataset.tab);
        });
    });
    
    // Handle pagination clicks
    const paginationLinks = document.querySelectorAll('.pagination-item');
    paginationLinks.forEach(link => {
        if (!link.classList.contains('disabled') && !link.classList.contains('active')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                navigateToPage(this.dataset.page);
            });
        }
    });
}

// 서버 측에서 처리하므로 클라이언트 측 saveSettings 함수 불필요

/**
 * Navigate to specified tab
 * @param {string} tabName - The name of the tab to navigate to
 */
function navigateToTab(tabName) {
    let url = '/';
    
    switch(tabName) {
        case 'bills':
            url = '/bill';
            break;
        case 'members':
            url = '/member';
            break;
        case 'mof':
            url = '/press/mof';
            break;
        case 'fsc':
            url = '/press/fsc';
            break;
        case 'news':
            url = '/news';
            break;
        case 'central_bank':
            url = '/central_bank';
            break;
        case 'settings':
            url = '/settings';
            break;
    }
    
    window.location.href = url;
}

/**
 * Navigate to a specific page for pagination
 * @param {string} page - The page number to navigate to
 */
function navigateToPage(page) {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('page', page);
    window.location.href = currentUrl.toString();
}

/**
 * Apply search with current settings
 * @param {string} formId - The ID of the form to submit
 */
function applySearch(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.submit();
}
