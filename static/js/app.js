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

// CSV Upload Functions
let csvAnalysisData = null;

function analyzeCSV() {
    const fileInput = document.getElementById('csv_file');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a CSV file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('csv_file', file);
    
    // Show loading
    document.getElementById('csvAnalytics').style.display = 'none';
    document.getElementById('importBtn').style.display = 'none';
    
    fetch('/admin/analyze_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            csvAnalysisData = data;
            displayCSVAnalytics(data);
        } else {
            showToast(data.message || 'Error analyzing CSV', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error analyzing CSV file', 'error');
    });
}

function displayCSVAnalytics(data) {
    document.getElementById('csvAnalytics').style.display = 'block';
    
    // Update stats
    document.getElementById('totalRecords').textContent = data.total_records;
    document.getElementById('newRecords').textContent = data.new_records;
    document.getElementById('duplicateRecords').textContent = data.duplicate_records;
    document.getElementById('errorRecords').textContent = data.error_records;
    
    // Update preview table
    const tbody = document.getElementById('csvPreviewBody');
    tbody.innerHTML = '';
    
    data.preview.forEach(record => {
        const row = tbody.insertRow();
        
        // Add error styling for rows with issues
        if (record.has_errors) {
            row.className = 'table-warning';
        }
        
        row.innerHTML = `
            <td>
                ${record.complete_name || record.full_name}
                ${record.has_errors ? '<i class="fas fa-exclamation-triangle text-warning ms-2" title="Has validation errors"></i>' : ''}
            </td>
            <td><code>${record.barcode || record.qr_code_id}</code></td>
            <td><span class="badge bg-${record.status === 'allowed' || record.status === 'Active' ? 'success' : 'danger'}">${record.status}</span></td>
            <td>
                <span class="badge bg-${getStatusBadgeColor(record.import_status)}">${record.import_status}</span>
                ${record.error_count > 0 ? `<small class="text-danger d-block">${record.error_count} error(s)</small>` : ''}
            </td>
        `;
        
        // Add tooltip with error details if there are errors
        if (record.errors && record.errors.length > 0) {
            row.title = 'Errors: ' + record.errors.join('; ');
        }
    });
    
    // Show errors and detailed explanations
    const errorDetails = document.getElementById('errorDetails');
    const errorList = document.getElementById('errorList');
    
    if (data.errors && data.errors.length > 0) {
        errorDetails.style.display = 'block';
        errorList.innerHTML = '';
        
        // Show regular errors
        data.errors.forEach(error => {
            const li = document.createElement('li');
            li.className = 'text-danger mb-1';
            li.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${error}`;
            errorList.appendChild(li);
        });
        
        // Add separator if there are undefined fields or validation issues
        if ((data.undefined_fields && data.undefined_fields.length > 0) || 
            (data.field_explanations && data.field_explanations.length > 0)) {
            const separator = document.createElement('hr');
            errorList.appendChild(separator);
        }
        
        // Show undefined fields explanation
        if (data.undefined_fields && data.undefined_fields.length > 0) {
            const undefinedHeader = document.createElement('h6');
            undefinedHeader.className = 'text-warning mt-3 mb-2';
            undefinedHeader.innerHTML = '<i class="fas fa-question-circle me-2"></i>Unrecognized Columns';
            errorList.appendChild(undefinedHeader);
            
            const undefinedList = document.createElement('ul');
            undefinedList.className = 'list-unstyled ms-3';
            data.undefined_fields.forEach(field => {
                const li = document.createElement('li');
                li.className = 'text-warning small';
                li.innerHTML = `<i class="fas fa-arrow-right me-2"></i><code>${field}</code>`;
                undefinedList.appendChild(li);
            });
            errorList.appendChild(undefinedList);
        }
        
        // Show field explanations
        if (data.field_explanations && data.field_explanations.length > 0) {
            data.field_explanations.forEach(explanation => {
                const explanationDiv = document.createElement('div');
                explanationDiv.className = 'alert alert-warning mt-3';
                explanationDiv.innerHTML = `
                    <h6 class="alert-heading">${explanation.title}</h6>
                    <p class="mb-2">${explanation.description}</p>
                    <hr>
                    <ul class="mb-0">
                        ${explanation.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                    </ul>
                `;
                errorList.appendChild(explanationDiv);
            });
        }
        
        // Show validation summary if available
        if (data.validation_summary) {
            const summaryDiv = document.createElement('div');
            summaryDiv.className = 'alert alert-info mt-3';
            summaryDiv.innerHTML = `
                <h6 class="alert-heading"><i class="fas fa-info-circle me-2"></i>CSV Format Guide</h6>
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="text-success">Required Fields:</h6>
                        <ul class="small">
                            ${Object.entries(data.validation_summary.required_fields).map(([field, desc]) => 
                                `<li><code>${field}</code> - ${desc}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6 class="text-primary">Optional Fields:</h6>
                        <ul class="small">
                            ${Object.entries(data.validation_summary.optional_fields).slice(0, 4).map(([field, desc]) => 
                                `<li><code>${field}</code> - ${desc}</li>`).join('')}
                        </ul>
                        <small class="text-muted">...and more</small>
                    </div>
                </div>
                <hr>
                <h6 class="text-warning">Format Requirements:</h6>
                <ul class="small mb-0">
                    ${Object.entries(data.validation_summary.format_requirements).map(([field, format]) => 
                        `<li><code>${field}</code>: ${format}</li>`).join('')}
                </ul>
            `;
            errorList.appendChild(summaryDiv);
        }
        
    } else {
        errorDetails.style.display = 'none';
    }
    
    // Show import button if there are new records
    if (data.new_records > 0) {
        document.getElementById('importBtn').style.display = 'inline-block';
        document.getElementById('importCount').textContent = data.new_records;
    }
}

function getStatusBadgeColor(status) {
    switch (status) {
        case 'New': return 'success';
        case 'Duplicate': return 'warning';
        case 'Error': return 'danger';
        default: return 'secondary';
    }
}

function importCSV() {
    if (!csvAnalysisData) {
        showToast('Please analyze the CSV first', 'error');
        return;
    }
    
    const fileInput = document.getElementById('csv_file');
    const file = fileInput.files[0];
    
    const formData = new FormData();
    formData.append('csv_file', file);
    
    // Disable import button
    const importBtn = document.getElementById('importBtn');
    importBtn.disabled = true;
    importBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Importing...';
    
    fetch('/admin/import_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Successfully imported ${data.imported_count} records`, 'success');
            
            // Close modal and refresh page
            const modal = bootstrap.Modal.getInstance(document.getElementById('csvUploadModal'));
            modal.hide();
            
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showToast(data.message || 'Import failed', 'error');
            importBtn.disabled = false;
            importBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Import ' + csvAnalysisData.new_records + ' Records';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error importing CSV file', 'error');
        importBtn.disabled = false;
        importBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Import ' + csvAnalysisData.new_records + ' Records';
    });
}

// Export functions for global access
window.SecurityApp = {
    simulateQRScan: simulateQRScan,
    refreshActivityData: refreshActivityData,
    showToast: showToast,
    formatTimestamp: formatTimestamp,
    analyzeCSV: analyzeCSV,
    importCSV: importCSV
};
