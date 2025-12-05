// Dashboard JavaScript

async function loadDashboard() {
    await loadStatistics();
    await loadLogs();
    await loadPrinterStatus();
    
    // Refresh every 30 seconds
    setInterval(async () => {
        await loadStatistics();
        await loadLogs();
        await loadPrinterStatus();
    }, 30000);
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/dashboard/stats');
        const data = await response.json();
        
        document.getElementById('totalPrints').textContent = data.total_prints || 0;
        document.getElementById('todayPrints').textContent = data.today_prints || 0;
        document.getElementById('totalRevenue').textContent = `₱${(data.total_revenue || 0).toFixed(2)}`;
        document.getElementById('successRate').textContent = `${data.success_rate || 0}%`;
        document.getElementById('unresolvedErrors').textContent = data.unresolved_errors || 0;
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

async function loadLogs() {
    try {
        const response = await fetch('/api/dashboard/logs?limit=50');
        const data = await response.json();
        
        const tbody = document.getElementById('logsTableBody');
        tbody.innerHTML = '';
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9">No logs available</td></tr>';
            return;
        }
        
        data.forEach(log => {
            const row = document.createElement('tr');
            
            const timestamp = new Date(log.timestamp).toLocaleString();
            const statusClass = `status-${log.status}`;
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${log.file_type || '-'}</td>
                <td>${log.file_name || '-'}</td>
                <td>${log.pages || 0}</td>
                <td>${log.copies || 1}</td>
                <td>${log.color_mode || '-'}</td>
                <td>₱${(log.cost || 0).toFixed(2)}</td>
                <td class="${statusClass}">${log.status || '-'}</td>
                <td>${log.error_message || '-'}</td>
            `;
            
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logsTableBody').innerHTML = 
            '<tr><td colspan="9">Error loading logs</td></tr>';
    }
}

async function loadPrinterStatus() {
    try {
        const response = await fetch('/api/printer-status');
        const data = await response.json();
        
        document.getElementById('printerName').textContent = data.printer_name || '-';
        document.getElementById('printerState').textContent = data.state || '-';
        document.getElementById('paperStatus').textContent = data.paper_status || '-';
        document.getElementById('inkStatus').textContent = data.ink_status || '-';
        document.getElementById('errorStatus').textContent = data.error_status || 'None';
        
        // Color code error status
        const errorStatusEl = document.getElementById('errorStatus');
        if (data.error_status && data.error_status !== 'None') {
            errorStatusEl.style.color = '#dc3545';
            errorStatusEl.style.fontWeight = 'bold';
        } else {
            errorStatusEl.style.color = '#28a745';
        }
    } catch (error) {
        console.error('Error loading printer status:', error);
    }
}

// Load dashboard on page load
document.addEventListener('DOMContentLoaded', loadDashboard);

