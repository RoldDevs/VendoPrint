// Print Document JavaScript

let currentFile = null;
let currentPages = 0;
let currentCost = 0;
let paidAmount = 0;
let paymentCheckInterval = null;

// File upload
document.getElementById('uploadArea').addEventListener('click', () => {
    document.getElementById('fileInput').click();
});

document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    await uploadFile(file);
});

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'document');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentFile = data.file_path;
            currentPages = data.pages;
            paidAmount = 0; // Reset payment
            
            // Update end page default
            document.getElementById('endPage').value = data.pages;
            document.getElementById('endPage').max = data.pages;
            
            // Show preview
            document.getElementById('previewImage').src = `/api/preview?file_path=${encodeURIComponent(data.preview_path)}`;
            document.getElementById('uploadArea').style.display = 'none';
            document.getElementById('previewSection').style.display = 'block';
            
            // Calculate initial cost
            await calculateCost();
            
            // Start payment monitoring
            startPaymentMonitoring();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('Error uploading file');
    }
}

// Page range selection
document.getElementById('pageRange').addEventListener('change', (e) => {
    const customRangeGroup = document.getElementById('customRangeGroup');
    if (e.target.value === 'custom') {
        customRangeGroup.style.display = 'block';
    } else {
        customRangeGroup.style.display = 'none';
    }
    calculateCost();
});

// Calculate cost when settings change
document.getElementById('copies').addEventListener('change', calculateCost);
document.getElementById('startPage').addEventListener('change', calculateCost);
document.getElementById('endPage').addEventListener('change', calculateCost);
document.getElementById('orientation').addEventListener('change', calculateCost);
document.getElementById('colorMode').addEventListener('change', calculateCost);

async function calculateCost() {
    const copies = parseInt(document.getElementById('copies').value) || 1;
    const orientation = document.getElementById('orientation').value;
    const colorMode = document.getElementById('colorMode').value;
    const pageRange = document.getElementById('pageRange').value;
    
    let rangeObj = null;
    if (pageRange === 'custom') {
        const startPage = parseInt(document.getElementById('startPage').value) || 1;
        const endPage = parseInt(document.getElementById('endPage').value) || currentPages;
        rangeObj = {
            start: Math.min(startPage, endPage),
            end: Math.max(startPage, endPage)
        };
    }
    
    try {
        const response = await fetch('/api/calculate-cost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pages: currentPages,
                copies: copies,
                page_range: rangeObj || 'all',
                orientation: orientation,
                color_mode: colorMode
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentCost = data.cost;
            document.getElementById('totalCost').textContent = `₱${data.cost.toFixed(2)}`;
            document.getElementById('pageCount').textContent = data.pages;
            document.getElementById('requiredAmount').textContent = `₱${data.cost.toFixed(2)}`;
            
            updatePaymentUI();
        }
    } catch (error) {
        console.error('Cost calculation error:', error);
    }
}

function startPaymentMonitoring() {
    // Check payment status every second
    paymentCheckInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/payment-status');
            const data = await response.json();
            
            paidAmount = data.paid;
            updatePaymentUI();
            
            // Enable print button ONLY if enough is paid AND cost is set
            const canPrint = data.can_print && currentCost > 0 && paidAmount >= currentCost;
            document.getElementById('printBtn').disabled = !canPrint;
        } catch (error) {
            console.error('Payment status error:', error);
            // On error, disable print button for safety
            document.getElementById('printBtn').disabled = true;
        }
    }, 1000);
}

function updatePaymentUI() {
    const remaining = Math.max(0, currentCost - paidAmount);
    const progress = currentCost > 0 ? Math.min(100, (paidAmount / currentCost) * 100) : 0;
    
    document.getElementById('paidAmount').textContent = `₱${paidAmount.toFixed(2)}`;
    document.getElementById('progressFill').style.width = `${progress}%`;
    
    // Update print button state based on payment
    const canPrint = currentCost > 0 && paidAmount >= currentCost;
    document.getElementById('printBtn').disabled = !canPrint;
}

// Print button
document.getElementById('printBtn').addEventListener('click', async () => {
    if (paidAmount < currentCost) {
        alert('Please insert more coins');
        return;
    }
    
    // Disable button immediately to prevent double-clicks
    document.getElementById('printBtn').disabled = true;
    
    await startPrinting();
});

async function startPrinting() {
    try {
        const response = await fetch('/api/start-print', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Stop payment monitoring
            if (paymentCheckInterval) {
                clearInterval(paymentCheckInterval);
            }
            
            // Show printing section
            document.getElementById('previewSection').style.display = 'none';
            document.getElementById('printingSection').style.display = 'block';
            
            // Monitor print progress
            monitorPrintProgress();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Print error:', error);
        alert('Error starting print');
    }
}

function monitorPrintProgress() {
    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/print-status');
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(progressInterval);
                showCompletion();
            } else if (data.status === 'error') {
                clearInterval(progressInterval);
                alert('Print error occurred');
                location.reload();
            } else if (data.status === 'printing') {
                const current = data.current_page || 0;
                const total = data.total_pages || 1;
                const progress = (current / total) * 100;
                
                document.getElementById('currentPage').textContent = current;
                document.getElementById('totalPages').textContent = total;
                document.getElementById('progressFillLarge').style.width = `${progress}%`;
            }
        } catch (error) {
            console.error('Progress monitoring error:', error);
        }
    }, 1000);
}

function showCompletion() {
    document.getElementById('printingSection').style.display = 'none';
    document.getElementById('completeSection').style.display = 'block';
}

// Test coin insertion function (for testing without hardware)
async function testCoinInsert(value) {
    // Validate that a file is uploaded and cost is calculated
    if (!currentFile || currentCost <= 0) {
        alert('Please upload a document first');
        return;
    }
    
    try {
        const response = await fetch('/api/coin-inserted', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ value: value })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            paidAmount = data.paid;
            updatePaymentUI();
            
            // Show feedback
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✓ Inserted!';
            btn.style.background = '#45a049';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '#4CAF50';
            }, 1000);
        } else {
            alert('Error: ' + (data.error || 'Failed to insert coin'));
            // Ensure button stays disabled on error
            document.getElementById('printBtn').disabled = true;
        }
    } catch (error) {
        console.error('Coin insertion error:', error);
        alert('Error inserting coin. Please check connection.');
        // Ensure button stays disabled on error
        document.getElementById('printBtn').disabled = true;
    }
}
