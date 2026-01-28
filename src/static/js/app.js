/**
 * IP2A Database - Main Application JavaScript
 * Handles HTMX events, Alpine.js integrations, and utility functions
 */

// HTMX Configuration
document.body.addEventListener('htmx:configRequest', function(evt) {
    // Add CSRF token if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        evt.detail.headers['X-CSRFToken'] = csrfToken.content;
    }
});

// Handle HTMX errors globally
document.body.addEventListener('htmx:responseError', function(evt) {
    console.error('HTMX Error:', evt.detail);
    showToast('An error occurred. Please try again.', 'error');
});

// Handle HTMX after swap for flash messages
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Check for flash messages in response headers
    const flashHeader = evt.detail.xhr.getResponseHeader('HX-Trigger');
    if (flashHeader) {
        try {
            const trigger = JSON.parse(flashHeader);
            if (trigger.showMessage) {
                showToast(trigger.showMessage.message, trigger.showMessage.type);
            }
        } catch (e) {
            // Not JSON, ignore
        }
    }
});

// Toast notification function
function showToast(message, type = 'info') {
    const container = document.getElementById('flash-container');
    if (!container) return;

    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-error',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const icons = {
        'success': `<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`,
        'error': `<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`,
        'warning': `<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>`,
        'info': `<svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`
    };

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} shadow-lg`;
    alertDiv.innerHTML = `
        <div>
            ${icons[type] || icons['info']}
            <span>${message}</span>
        </div>
        <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(alertDiv);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transform = 'translateY(-10px)';
        alertDiv.style.transition = 'all 0.3s ease-out';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

// Confirm dialog for dangerous actions
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    }).format(date);
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Add loading indicator class for HTMX requests
    document.body.classList.add('htmx-ready');

    // Initialize any tooltips
    const tooltips = document.querySelectorAll('[data-tip]');
    tooltips.forEach(el => {
        el.classList.add('tooltip');
    });

    console.log('IP2A Database initialized');
});
