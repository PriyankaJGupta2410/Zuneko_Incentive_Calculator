// ===========================
// Global Variables
// ===========================
let calculationResults = [];
let uploadedData = {
    sales: { total_rows: 0, processed: 0, failed: 0, lastUpload: null },
    rules: { total_rows: 0, processed: 0, failed: 0, lastUpload: null }
};

// ===========================
// Toast Notification System
// ===========================

/**
 * Show toast notification
 */
function showToast(title, message, type = 'success', duration = 5000) {
    const container = document.getElementById('toastContainer');
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Icon based on type
    let icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-circle-xmark';
    if (type === 'info') icon = 'fa-circle-info';
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fa-solid ${icon}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// ===========================
// Utility Functions
// ===========================

/**
 * Log messages with timestamp
 */
function log(msg, ...args) {
    console.log(`[App ${new Date().toLocaleTimeString()}] ${msg}`, ...args);
}

/**
 * Format number as Indian Rupees
 */
function formatCurrency(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN');
}

/**
 * Format date and time
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show loading state on button
 */
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.style.opacity = '0.6';
        button.style.cursor = 'not-allowed';
        
        // Store original content
        button.dataset.originalHtml = button.innerHTML;
        
        // Show loading spinner
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Processing...</span>';
    } else {
        button.disabled = false;
        button.style.opacity = '1';
        button.style.cursor = 'pointer';
        
        // Restore original content
        if (button.dataset.originalHtml) {
            button.innerHTML = button.dataset.originalHtml;
        }
    }
}

/**
 * Update uploaded data display
 */
function updateDataDisplay(type, data) {
    const prefix = type === 'sales' ? 'sales' : 'rules';
    
    document.getElementById(`${prefix}TotalRows`).textContent = data.total_rows || '-';
    document.getElementById(`${prefix}Processed`).textContent = data.processed || '-';
    document.getElementById(`${prefix}Failed`).textContent = data.failed || '-';
    document.getElementById(`${prefix}LastUpload`).textContent = formatDateTime(data.lastUpload);
    
    // Store in global state
    uploadedData[type] = data;
}

// ===========================
// File Input Handlers
// ===========================

/**
 * Update file label when file is selected
 */
document.addEventListener('DOMContentLoaded', function() {
    const salesFile = document.getElementById('salesFile');
    const rulesFile = document.getElementById('rulesFile');
    
    if (salesFile) {
        salesFile.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Choose CSV file';
            document.getElementById('salesFileName').textContent = fileName;
        });
    }
    
    if (rulesFile) {
        rulesFile.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'Choose CSV file';
            document.getElementById('rulesFileName').textContent = fileName;
        });
    }
});

// ===========================
// File Upload Functions
// ===========================

/**
 * Generic file upload handler
 */
async function uploadFile(endpoint, fileInputId, statusId, dataType) {
    const fileInput = document.getElementById(fileInputId);
    const statusSpan = document.getElementById(statusId);
    const uploadBtn = event.target;

    // Validate file selection
    if (!fileInput.files.length) {
        showToast('No File Selected', 'Please select a CSV file to upload', 'error');
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    const fileName = fileInput.files[0].name;

    try {
        // Show loading state
        setButtonLoading(uploadBtn, true);
        statusSpan.textContent = "⏳ Uploading...";
        statusSpan.className = "status";

        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }

        // Show success status
        statusSpan.textContent = "✓ Upload successful";
        statusSpan.className = "status success";

        // Show success toast
        showToast(
            'Upload Successful',
            `${fileName} uploaded successfully. ${data.summary.processed} rows processed.`,
            'success'
        );

        // Update data display
        updateDataDisplay(dataType, {
            total_rows: data.summary.total_rows,
            processed: data.summary.processed,
            failed: data.summary.failed,
            lastUpload: new Date().toISOString()
        });

        // Log failed rows for debugging
        if (data.failed_rows && data.failed_rows.length > 0) {
            console.warn("Failed Rows:", data.failed_rows);
            
            // Show warning toast if there are failed rows
            if (data.summary.failed > 0) {
                showToast(
                    'Some Rows Failed',
                    `${data.summary.failed} rows failed to process. Check console for details.`,
                    'error',
                    7000
                );
            }
        }

        // Clear file input and reset label
        fileInput.value = '';
        const labelId = fileInputId === 'salesFile' ? 'salesFileName' : 'rulesFileName';
        document.getElementById(labelId).textContent = 'Choose CSV file';

    } catch (error) {
        log("Upload error:", error);
        statusSpan.textContent = "✗ Upload failed";
        statusSpan.className = "status error";
        
        showToast(
            'Upload Failed',
            error.message || 'An error occurred while uploading the file',
            'error',
            7000
        );
    } finally {
        setButtonLoading(uploadBtn, false);
    }
}

/**
 * Upload sales data
 */
function uploadSales() {
    uploadFile("/data-ingestion/upload_sales_data", "salesFile", "salesStatus", "sales");
}

/**
 * Upload incentive rules
 */
function uploadRules() {
    uploadFile("/data-ingestion/upload_structured_rule", "rulesFile", "rulesStatus", "rules");
}

// ===========================
// Calculation Functions
// ===========================

/**
 * Trigger incentive calculation
 */
async function triggerCalculation() {
    const period = document.getElementById("calcPeriod").value;
    const button = event.target;

    if (!period) {
        showToast('Period Required', 'Please select a calculation period', 'error');
        return;
    }

    log("Triggering calculation for period:", period);

    try {
        setButtonLoading(button, true);

        const response = await fetch(`${API_URL}/calculator/calculate-incentives`, {
            method: 'POST',
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                period: period
            })
        });

        const data = await response.json();

        if (response.ok) {
            showToast(
                'Calculation Complete',
                data.message || 'Incentives calculated successfully',
                'success'
            );
            
            // Refresh dashboard data
            await Promise.all([fetchStats(), fetchResults()]);
        } else {
            throw new Error(data.detail || "Calculation failed");
        }

    } catch (error) {
        log("Calculation error:", error);
        showToast(
            'Calculation Failed',
            error.message || 'An error occurred during calculation',
            'error',
            7000
        );
    } finally {
        setButtonLoading(button, false);
    }
}

// ===========================
// Dashboard Stats Functions
// ===========================

/**
 * Fetch and update dashboard statistics
 */
async function fetchStats() {
    try {
        const response = await fetch(`${API_URL}/results/GETdashboard_stats`);

        if (!response.ok) {
            throw new Error("Failed to fetch stats");
        }

        const data = await response.json();

        // Update stat cards
        document.getElementById("totalIncentive").textContent = formatCurrency(data.total_incentive);
        document.getElementById("totalProcessed").textContent = data.total_salespeople || "0";
        document.getElementById("avgIncentive").textContent = formatCurrency(Math.round(data.avg_incentive || 0));
        document.getElementById("topPerformer").textContent = data.top_performer || "-";

        log("Stats updated successfully");

    } catch (error) {
        console.error("Failed to fetch stats:", error);
        // Set default values on error
        document.getElementById("totalIncentive").textContent = "₹0";
        document.getElementById("totalProcessed").textContent = "0";
        document.getElementById("avgIncentive").textContent = "₹0";
        document.getElementById("topPerformer").textContent = "-";
    }
}

// ===========================
// Results Table Functions
// ===========================

/**
 * Fetch and display calculation results
 */
async function fetchResults() {
    try {
        const response = await fetch(`${API_URL}/results/GETresults?limit=100`);

        if (!response.ok) {
            throw new Error("Failed to fetch results");
        }

        const data = await response.json();

        log("Fetched results:", data.length, "records");

        // Store globally for modal access
        calculationResults = data;

        const tbody = document.getElementById("resultsBody");
        tbody.innerHTML = "";

        // Handle empty results
        if (!data || data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="empty-state">
                        <i class="fa-solid fa-inbox"></i>
                        <p>No results available yet</p>
                        <span>Upload data and calculate incentives to see results</span>
                    </td>
                </tr>
            `;
            return;
        }

        // Populate table rows
        data.forEach((row, index) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${row.employee_id}</strong></td>
                <td>${row.period_month}</td>
                <td><strong>${formatCurrency(row.total_incentive)}</strong></td>
                <td><span style="color: var(--success); font-weight: 600;">${row.status}</span></td>
                <td>${formatDateTime(row.period_month)}</td>
                <td>
                    <button onclick="viewDetails(${index})">
                        <i class="fa-solid fa-eye"></i>
                        <span>View</span>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        log("Results table updated");

    } catch (error) {
        console.error("Failed to fetch results:", error);
        const tbody = document.getElementById("resultsBody");
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    <i class="fa-solid fa-exclamation-triangle"></i>
                    <p style="color: var(--error);">Error loading results</p>
                    <span>Please try again or contact support</span>
                </td>
            </tr>
        `;
    }
}

// ===========================
// Modal Functions
// ===========================

/**
 * View detailed breakdown in modal
 */
function viewDetails(index) {
    log("Opening details modal for index:", index);

    // Validate global state
    if (!calculationResults || calculationResults.length === 0) {
        console.error("calculationResults is empty!");
        showToast('Error', 'No data available. Please refresh the results.', 'error');
        fetchResults();
        return;
    }

    const row = calculationResults[index];

    if (!row) {
        console.error("No row data found for index:", index);
        showToast('Error', 'Error loading details. Please refresh the table.', 'error');
        return;
    }

    log("Row data:", row);

    // Parse breakdown JSON
    let breakdown = [];
    try {
        if (typeof row.breakdown_json === 'string') {
            breakdown = JSON.parse(row.breakdown_json);
        } else if (Array.isArray(row.breakdown_json)) {
            breakdown = row.breakdown_json;
        } else {
            throw new Error("Invalid breakdown format");
        }
    } catch (e) {
        console.error("Error parsing breakdown JSON:", e);
        showToast('Error', 'Error parsing incentive breakdown data', 'error');
        return;
    }

    // Build modal content
    let html = `
        <div style="margin-bottom: 1.5rem; padding: 1.25rem; background: linear-gradient(135deg, rgba(28, 57, 187, 0.05), rgba(41, 72, 216, 0.05)); border-radius: 8px; border-left: 4px solid var(--persian-blue);">
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Employee ID</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: var(--persian-blue); margin-bottom: 1rem;">${row.employee_id}</div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Total Incentive</div>
            <div style="font-size: 2rem; font-weight: 700; color: var(--persian-blue);">${formatCurrency(row.total_incentive)}</div>
        </div>
    `;

    // Add breakdown table
    if (breakdown && breakdown.length > 0) {
        html += `
            <table class="breakdown-table">
                <thead>
                    <tr>
                        <th style="text-align: left;">Incentive Component</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
        `;

        breakdown.forEach(item => {
            html += `
                <tr>
                    <td>${item.description || 'N/A'}</td>
                    <td style="text-align: right; font-weight: 600;">${formatCurrency(item.amount || 0)}</td>
                </tr>
            `;
        });

        html += `
                <tr class="total-row">
                    <td style="font-size: 1rem;">Total Payout</td>
                    <td style="text-align: right; font-size: 1.1rem;">${formatCurrency(row.total_incentive)}</td>
                </tr>
                </tbody>
            </table>
        `;
    } else {
        html += `<p style="text-align: center; color: var(--text-secondary); padding: 2rem;">No breakdown data available.</p>`;
    }

    // Update modal content
    const modalContent = document.getElementById("modalContent");
    if (!modalContent) {
        console.error("modalContent element missing from DOM");
        return;
    }
    modalContent.innerHTML = html;

    // Show modal
    const modal = document.getElementById("detailsModal");
    if (modal) {
        modal.style.display = "block";
        document.body.style.overflow = "hidden";
        log("Modal displayed");
    } else {
        console.error("detailsModal element missing from DOM");
    }
}

/**
 * Close modal
 */
function closeModal() {
    const modal = document.getElementById("detailsModal");
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "auto";
    }
}

// ===========================
// Event Listeners
// ===========================

/**
 * Close modal when clicking outside
 */
window.onclick = function (event) {
    const modal = document.getElementById("detailsModal");
    if (event.target === modal) {
        closeModal();
    }
}

/**
 * Close modal with Escape key
 */
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// ===========================
// Initialization
// ===========================

/**
 * Initialize app on page load
 */
window.onload = () => {
    log("App initialized");
    
    // Set default period to current month
    const today = new Date();
    const currentMonth = today.toISOString().slice(0, 7);
    document.getElementById("calcPeriod").value = currentMonth;
    
    // Fetch initial data
    fetchStats();
    fetchResults();
    
    log("Initial data fetch complete");
};