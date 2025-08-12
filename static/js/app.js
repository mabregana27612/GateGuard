// Security Access Control - JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize modals
    var modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(function(modalElement) {
        new bootstrap.Modal(modalElement);
    });

    // Auto-dismiss alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // QR Code input formatting
    var qrInputs = document.querySelectorAll('input[name="qr_code_id"]');
    qrInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            // Convert to uppercase for consistency
            e.target.value = e.target.value.toUpperCase();
        });

        // Auto-submit on barcode scanner input (ends with Enter)
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                // Small delay to ensure full barcode is captured
                setTimeout(function() {
                    if (input.form) {
                        input.form.submit();
                    }
                }, 100);
            }
        });
    });

    // Confirmation dialogs for destructive actions
    var deleteLinks = document.querySelectorAll('a[href*="/delete_user/"]');
    deleteLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Status change confirmations
    var statusLinks = document.querySelectorAll('a[href*="/change_status/"]');
    statusLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            var action = link.href.includes('/banned') ? 'ban' : 'allow';
            if (!confirm(`Are you sure you want to ${action} this user?`)) {
                e.preventDefault();
            }
        });
    });

    // Search functionality with debounce
    var searchInputs = document.querySelectorAll('input[name="q"], input[name="query"]');
    searchInputs.forEach(function(input) {
        var timeoutId;
        input.addEventListener('input', function(e) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(function() {
                // Auto-search after 500ms of inactivity
                if (e.target.value.length >= 2 || e.target.value.length === 0) {
                    // You could implement live search here if needed
                }
            }, 500);
        });
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-refresh activity data every 30 seconds on dashboard
    if (window.location.pathname.includes('/admin')) {
        setInterval(function() {
            // Only refresh if tab is visible
            if (!document.hidden) {
                refreshActivityData();
            }
        }, 30000);
    }

    // Smooth scrolling for anchor links
    var anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            var href = this.getAttribute('href');
            if (href && href !== '#' && href.length > 1) {
                var target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Alt + A: Go to Access Control
        if (e.altKey && e.key === 'a') {
            e.preventDefault();
            window.location.href = '/access';
        }
        
        // Alt + D: Go to Dashboard (if logged in)
        if (e.altKey && e.key === 'd') {
            e.preventDefault();
            if (document.querySelector('a[href*="/admin"]')) {
                window.location.href = '/admin';
            }
        }
        
        // Alt + R: Go to Reports (if logged in)
        if (e.altKey && e.key === 'r') {
            e.preventDefault();
            if (document.querySelector('a[href*="/reports"]')) {
                window.location.href = '/reports';
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            var openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
});

// QR Code Scanner Simulation
function startQRScanner() {
    const qrInput = document.getElementById('qr_code_id');
    if (qrInput) {
        qrInput.focus();
    }
}
function simulateQRScan() {
    return new Promise(function(resolve, reject) {
        // Simulate scanning delay
        setTimeout(function() {
            // Generate demo QR codes
            var demoQRCodes = [
                'USER001', 'USER002', 'USER003', 'EMP123', 'EMP456',
                'GUEST789', 'ADMIN001', 'VISITOR99', 'STAFF007'
            ];
            
            var randomQR = demoQRCodes[Math.floor(Math.random() * demoQRCodes.length)];
            resolve(randomQR);
        }, 1500);
    });
}

// Refresh activity data
function refreshActivityData() {
    var activityContainer = document.querySelector('.activity-list');
    if (activityContainer) {
        // Add loading indicator
        var loadingHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Refreshing...</div>';
        var originalHTML = activityContainer.innerHTML;
        
        // You could implement AJAX refresh here if needed
        // For now, just show a brief loading state
        activityContainer.innerHTML = loadingHTML;
        
        setTimeout(function() {
            activityContainer.innerHTML = originalHTML;
        }, 1000);
    }
}

// Utility functions
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function showToast(message, type = 'info') {
    var toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    var toastHTML = `
        <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas fa-${type === 'success' ? 'check-circle text-success' : 
                                    type === 'error' ? 'exclamation-circle text-danger' :
                                    type === 'warning' ? 'exclamation-triangle text-warning' :
                                    'info-circle text-info'} me-2"></i>
                <strong class="me-auto">System</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Auto-hide after 3 seconds
    setTimeout(function() {
        var toast = toastContainer.lastElementChild;
        if (toast) {
            var bsToast = new bootstrap.Toast(toast);
            bsToast.hide();
        }
    }, 3000);
}

// Export functions for global access
window.SecurityApp = {
    simulateQRScan: simulateQRScan,
    refreshActivityData: refreshActivityData,
    showToast: showToast,
    formatTimestamp: formatTimestamp
};
