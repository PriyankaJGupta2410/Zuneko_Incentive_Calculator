// ================================
// NAVIGATION SYSTEM
// ================================

const navButtons = document.querySelectorAll('.nav-btn');
const screens = document.querySelectorAll('.screen');

navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetScreen = btn.getAttribute('data-screen');
        switchScreen(targetScreen);
    });
});

// Action cards navigation
const actionCards = document.querySelectorAll('.action-card');
actionCards.forEach(card => {
    card.addEventListener('click', () => {
        const targetScreen = card.getAttribute('data-navigate');
        switchScreen(targetScreen);
    });
});

function switchScreen(screenId) {
    // Update nav buttons
    navButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-screen') === screenId) {
            btn.classList.add('active');
        }
    });
    
    // Update screens
    screens.forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
    
    // Load dashboard data when dashboard is shown
    if (screenId === 'dashboard') {
        loadDashboardData();
    }
}

// ================================
// DASHBOARD DATA LOADING
// ================================

async function loadDashboardData() {
    try {
        const response = await fetch(`${API_URL}/results/GETdashboard_stats`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch dashboard data: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Dashboard data:', result);

        if (result.status === true && result.data) {
            const data = result.data;

            // Update KPI cards
            document.getElementById('dashTotalIncentives').textContent = 
                '₹' + data.total_incentive_calculated.toLocaleString('en-IN');

            document.getElementById('dashTotalEmployees').textContent = 
                data.salesperson_processed.toLocaleString();

            // Top performer
            document.getElementById('dashTopPerformer').textContent = 
                `${data.top_performer.employee_id} → ₹${data.top_performer.total_incentive.toLocaleString('en-IN')}`;

            // Last calculation run
            document.getElementById('dashLastRun').textContent = new Date(data.last_calculation_run).toLocaleDateString('en-IN', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });

            document.getElementById('dashStatus').textContent = '● Completed Successfully';
        }
    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});

// ================================
// FILE UPLOAD HANDLERS
// ================================

// Sales Data Upload
setupFileUpload('salesDropzone', 'salesFileInput', handleSalesUpload);

// Structured Rules Upload
setupFileUpload('rulesDropzone', 'rulesFileInput', handleRulesUpload);

// Ad-Hoc Rules Upload
setupFileUpload('adhocDropzone', 'adhocFileInput', handleAdhocUpload);

function setupFileUpload(dropzoneId, inputId, handler) {
    const dropzone = document.getElementById(dropzoneId);
    const input = document.getElementById(inputId);
    
    dropzone.addEventListener('click', () => input.click());
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    
    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });
    
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handler(e.dataTransfer.files[0]);
        }
    });
    
    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handler(e.target.files[0]);
        }
    });
}

async function handleSalesUpload(file) {
    console.log('Uploading sales data:', file.name);

    const preview = document.getElementById('salesPreview');
    const rowCount = document.getElementById('salesRowCount');
    const validation = document.getElementById('salesValidation');
    const table = document.getElementById('salesPreviewTable');

    // Show uploading status
    rowCount.textContent = 'Uploading...';
    validation.textContent = '';
    preview.style.display = 'none';
    table.innerHTML = '';

    try {
        // Prepare FormData
        const formData = new FormData();
        formData.append('file', file);

        // Call API to upload file
        const response = await fetch(`${API_URL}/data-ingestion/upload_sales_data`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.status) {
            // Update summary info
            rowCount.textContent = `Total Rows: ${data.total_records}`;
            validation.textContent = `Valid: ${data.total_records - data.invalid_rows_count} | Invalid: ${data.invalid_rows_count}`;
            validation.style.color = 'var(--success)';
            preview.style.display = 'block';
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (err) {
        console.error('Error uploading file:', err);
        rowCount.textContent = 'Upload failed';
        validation.textContent = err.message;
        validation.style.color = 'var(--error)';
    }
}

async function handleRulesUpload(file) {
    console.log('Uploading structured rules:', file.name);

    const status = document.getElementById('rulesStatus');
    status.style.display = 'block';
    status.innerHTML = 'Uploading...';

    try {
        // Prepare FormData
        const formData = new FormData();
        formData.append('file', file);

        // Call API
        const response = await fetch(`${API_URL}/data-ingestion/upload_structured_rule`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.status) {
            // Show success message
            status.innerHTML = `
                <strong>✓ Upload Successful</strong><br>
                ${data.total_records} rules detected | Validity: Sep 2025 - Dec 2025<br>
                <span style="color: var(--warning);">⚠ Warning: Check for overlapping rules if any</span>
            `;
            status.style.color = 'var(--success)';
        } else {
            throw new Error(data.message || 'Unknown error');
        }

    } catch (err) {
        console.error('Error uploading structured rules:', err);
        status.innerHTML = `Upload failed: ${err.message}`;
        status.style.color = 'var(--error)';
    }
}

async function handleAdhocUpload(file) {
    console.log('Uploading ad-hoc rules:', file.name);

    const parsed = document.getElementById('adhocParsed');
    const confidence = document.getElementById('confidenceBadge');
    const content = document.getElementById('parsedContent');

    // Show uploading status
    parsed.style.display = 'none';
    confidence.textContent = '';
    content.innerHTML = 'Uploading...';

    try {
        // Prepare FormData
        const formData = new FormData();
        formData.append('file', file);

        // Call API
        const response = await fetch(`${API_URL}/data-ingestion/upload_ad_hoc_rule`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.status) {
            // Show success content
            confidence.textContent = 'High';
            confidence.style.background = 'var(--success-light)';
            confidence.style.color = 'var(--success)';

            content.innerHTML = `
                <p><strong>${data.total_records} ad-hoc rules uploaded successfully</strong></p>
                <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                    <li>File saved: ${data.saved_file}</li>
                    ${data.invalid_rows_count > 0 ? `<li>Invalid Rows: ${data.invalid_rows_count}</li>` : ''}
                </ul>
            `;

            parsed.style.display = 'block';
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (err) {
        console.error('Error uploading ad-hoc rules:', err);
        content.innerHTML = `Upload failed: ${err.message}`;
        confidence.textContent = '';
        parsed.style.display = 'block';
    }
}

// ================================
// TAB SYSTEM
// ================================

const tabButtons = document.querySelectorAll('.tab-btn');
tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.getAttribute('data-tab');
        
        // Update buttons
        tabButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(targetTab + 'Tab').classList.add('active');
    });
});

// ================================
// MANUAL AD-HOC RULE
// ================================

document.getElementById('addAdhocBtn').addEventListener('click', () => {
    const text = document.getElementById('adhocText').value;
    const from = document.getElementById('adhocFrom').value;
    const to = document.getElementById('adhocTo').value;
    const priority = document.getElementById('adhocPriority').value;
    
    if (!text || !from || !to) {
        alert('Please fill in all required fields');
        return;
    }
    
    alert('Ad-hoc rule added successfully!\n\nRule: ' + text);
    
    // Clear form
    document.getElementById('adhocText').value = '';
    document.getElementById('adhocFrom').value = '';
    document.getElementById('adhocTo').value = '';
});

// ================================
// CALCULATION SYSTEM - SIMPLIFIED
// ================================

document.getElementById('runCalcBtn').addEventListener('click', async () => {
    const month = document.getElementById('calcMonth').value;

    const output = document.getElementById('calcOutput');
    const statusText = document.getElementById('statusText');
    const statusIndicator = document.getElementById('statusIndicator');

    // Show output
    output.style.display = 'block';

    // Reset state
    statusText.textContent = 'Processing...';
    statusText.style.color = 'var(--gray-700)';
    statusIndicator.querySelector('.spinner').style.display = 'block';
    document.getElementById('recordsProcessed').textContent = '-';
    document.getElementById('successCount').textContent = '-';
    document.getElementById('exceptionsCount').textContent = '-';
    document.getElementById('execTime').textContent = '-';

    const startTime = Date.now();

    try {
        // Call the API
        const response = await fetch(`${API_URL}/calculator/api/incentives/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ period: month })
        });

        if (!response.ok) {
            throw new Error(`API call failed with status ${response.status}`);
        }

        const data = await response.json();

        if (data.status) {
            const incentives = data.data;

            // Calculate metrics
            const recordsProcessed = incentives.length;
            const totalIncentive = incentives.reduce((sum, emp) => sum + emp.total_incentive, 0);
            const exceptionsCount = incentives.filter(emp => emp.total_incentive === 0).length;
            
            const endTime = Date.now();
            const executionTime = ((endTime - startTime) / 1000).toFixed(2);

            // Update UI
            statusIndicator.querySelector('.spinner').style.display = 'none';
            statusText.textContent = '✓ Completed Successfully';
            statusText.style.color = 'var(--success)';

            document.getElementById('recordsProcessed').textContent = recordsProcessed.toLocaleString();
            document.getElementById('successCount').textContent = '₹' + totalIncentive.toLocaleString('en-IN');
            document.getElementById('exceptionsCount').textContent = exceptionsCount;
            document.getElementById('execTime').textContent = executionTime + 's';
            
            // Update dashboard data after calculation
            loadDashboardData();

        } else {
            throw new Error(data.message || 'Unknown error from API');
        }
    } catch (err) {
        console.error('Error calculating incentives:', err);
        statusIndicator.querySelector('.spinner').style.display = 'none';
        statusText.textContent = `✗ ${err.message}`;
        statusText.style.color = 'var(--error)';
    }
});

document.getElementById('viewResultsBtn').addEventListener('click', () => {
    loadIncentiveResults();
});

// ================================
// LOAD INCENTIVE RESULTS FROM API
// ================================

async function loadIncentiveResults() {
    const tbody = document.getElementById('resultsTableBody');
    const totalRecordsEl = document.getElementById('resultsTotalRecords');
    const totalIncentivesEl = document.getElementById('resultsTotalIncentives');
    const topPerformerEl = document.getElementById('resultsTopPerformer');
    // Show loading
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;">Loading results...</td></tr>';

    try {
        const response = await fetch(`${API_URL}/results/GETincentiveresults`);
        if (!response.ok) throw new Error(`API failed with status ${response.status}`);

        const data = await response.json();
        if (!data.status) throw new Error(data.message || 'Failed to fetch results');

        // Update summary info
        const summary = data.summary || {};
        if (totalRecordsEl) totalRecordsEl.textContent = (summary.total_records || 0).toLocaleString();
        if (totalIncentivesEl) totalIncentivesEl.textContent = '₹' + (summary.total_incentives || 0).toLocaleString('en-IN');
        if (topPerformerEl && summary.top_performer) {
            const tp = summary.top_performer;
            topPerformerEl.textContent = `${tp.employee_id} → ₹${(tp.total_incentive || 0).toLocaleString('en-IN')} (${tp.branch} - ${tp.role})`;
        }

        // Clear table
        tbody.innerHTML = '';

        if (!data.data || data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:gray;">No results found. Please run calculation first.</td></tr>';
            switchScreen('results');
            return;
        }

        // Populate table
        data.data.forEach(emp => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><code>${emp.employee_id}</code></td>
                <td>${emp.branch || '-'}</td>
                <td>${emp.role || '-'}</td>
                <td>${emp.total_units || 0}</td>
                <td>₹${(emp.structured_incentive || 0).toLocaleString('en-IN')}</td>
                <td>₹${(emp.adhoc_incentive || 0).toLocaleString('en-IN')}</td>
                <td><strong>₹${(emp.total_incentive || 0).toLocaleString('en-IN')}</strong></td>
                <td>
                    <span class="status-badge ${emp.total_incentive === 0 ? 'error' : 'success'}">
                        ${emp.total_incentive === 0 ? 'Exception' : 'Success'}
                    </span>
                </td>
                <td>
                    <button class="btn-link" onclick='showBreakdown("${emp.employee_id}")'>View Breakdown</button>
                </td>
            `;
            tbody.appendChild(row);
        });

        switchScreen('results');

    } catch (err) {
        console.error('Error loading incentive results:', err);
        tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:2rem;color:red;">Error: ${err.message}</td></tr>`;
        switchScreen('results');
    }
}

// ================================
// BREAKDOWN MODAL
// ================================

async function showBreakdown(employeeId) {
    const modal = document.getElementById('breakdownModal');
    const content = document.getElementById('breakdownContent');

    // Loading state
    content.innerHTML = '<p style="text-align:center;padding:2rem;">Loading breakdown...</p>';
    modal.classList.add('active');

    try {
        const response = await fetch(`${API_URL}/results/GETincentiveresults`);
        if (!response.ok) throw new Error(`API failed with status ${response.status}`);
        const data = await response.json();
        if (!data.status) throw new Error('Failed to fetch breakdown data');

        const empData = data.data.find(emp => emp.employee_id === employeeId);
        if (!empData) {
            content.innerHTML = '<p style="text-align:center;padding:2rem;">Breakdown data not available for this employee.</p>';
            return;
        }

        // Structured incentives
        let structuredHTML = '<p style="color: gray; font-style: italic;">No structured incentives applied</p>';
        if (empData.details.structured && empData.details.structured.length > 0) {
            structuredHTML = `
                <table class="breakdown-table">
                    <thead>
                        <tr><th>Vehicle Model</th><th>Vehicle Type</th><th>Quantity</th><th>Rule Applied</th><th>Amount</th></tr>
                    </thead>
                    <tbody>
                        ${empData.details.structured.map(item => `
                            <tr>
                                <td>${item.vehicle_model || '-'}</td>
                                <td>${item.vehicle_type || '-'}</td>
                                <td>${item.quantity || 0}</td>
                                <td>${item.rule_applied || '-'}</td>
                                <td>₹${(item.amount || 0).toLocaleString('en-IN')}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        // Ad-hoc incentives
        let adhocHTML = '<p style="color: gray; font-style: italic;">No ad-hoc incentives applied</p>';
        if (empData.details.ad_hoc && empData.details.ad_hoc.length > 0) {
            adhocHTML = `
                <table class="breakdown-table">
                    <thead>
                        <tr><th>Scheme Name</th><th>Condition</th><th>Amount</th></tr>
                    </thead>
                    <tbody>
                        ${empData.details.ad_hoc.map(item => `
                            <tr>
                                <td>${item.scheme_name || '-'}</td>
                                <td>${item.condition || '-'}</td>
                                <td>₹${(item.amount || 0).toLocaleString('en-IN')}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        // Full modal content
        content.innerHTML = `
            <h4>${empData.employee_id} - ${empData.branch}</h4>
            <p><strong>Role:</strong> ${empData.role}</p>
            <p><strong>Total Units:</strong> ${empData.total_units}</p>
            <p><strong>Status:</strong> <span class="status-badge ${empData.total_incentive === 0 ? 'error' : 'success'}">${empData.status}</span></p>

            <div style="display:flex;gap:1rem;margin:1rem 0;">
                <div><strong>Structured:</strong> ₹${empData.structured_incentive.toLocaleString('en-IN')}</div>
                <div><strong>Ad-Hoc:</strong> ₹${empData.adhoc_incentive.toLocaleString('en-IN')}</div>
                <div><strong>Total:</strong> ₹${empData.total_incentive.toLocaleString('en-IN')}</div>
            </div>

            <h5>Structured Incentives Breakdown</h5>
            ${structuredHTML}

            <h5>Ad-Hoc Incentives Breakdown</h5>
            ${adhocHTML}
        `;

    } catch (err) {
        console.error('Error loading breakdown:', err);
        content.innerHTML = `<p style="text-align:center;padding:2rem;color:red;">Error: ${err.message}</p>`;
    }
}

function closeBreakdown() {
    document.getElementById('breakdownModal').classList.remove('active');
}

window.showBreakdown = showBreakdown;
window.closeBreakdown = closeBreakdown;

// ================================
// INIT - Load results on page load
// ================================
document.addEventListener('DOMContentLoaded', () => {
    loadIncentiveResults();
});

// Close modal on ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeBreakdown();
    }
});