// Print Photo JavaScript

let currentFile = null;
let currentPages = 1;
let currentCost = 0;
let paidAmount = 0;
let paymentCheckInterval = null;

// Wait for DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function() {
    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            await uploadFile(file);
        });
    } else {
        console.error('Upload area or file input not found!');
    }
    
    // Calculate cost when settings change
    const copies = document.getElementById('copies');
    const orientation = document.getElementById('orientation');
    const colorMode = document.getElementById('colorMode');
    const printBtn = document.getElementById('printBtn');
    
    if (copies) copies.addEventListener('change', calculateCost);
    if (orientation) orientation.addEventListener('change', calculateCost);
    if (colorMode) colorMode.addEventListener('change', calculateCost);
    
    // Print button
    if (printBtn) {
        printBtn.addEventListener('click', async () => {
            if (paidAmount < currentCost) {
                alert('Please insert more coins');
                return;
            }
            
            // Disable button immediately to prevent double-clicks
            printBtn.disabled = true;
            
            await startPrinting();
        });
    }
});

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'photo');
    
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

async function calculateCost() {
    const copies = parseInt(document.getElementById('copies').value) || 1;
    const orientation = document.getElementById('orientation').value;
    const colorMode = document.getElementById('colorMode').value;
    
    try {
        const response = await fetch('/api/calculate-cost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pages: currentPages,
                copies: copies,
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
        alert('Please upload a photo first');
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
