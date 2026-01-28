// Print Document JavaScript

console.log('[Print Document] Script loaded');

let currentFile = null;
let currentPages = 0;
let currentCost = 0;
let paidAmount = 0;
let paymentCheckInterval = null;

// Wait for DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Print Document] DOM Content Loaded');
    
    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    console.log('[Print Document] Upload Area:', uploadArea);
    console.log('[Print Document] File Input:', fileInput);
    
    if (fileInput) {
        console.log('[Print Document] Attaching change event to file input');
        
        fileInput.addEventListener('change', async (e) => {
            console.log('[Print Document] File selected');
            const file = e.target.files[0];
            if (!file) {
                console.log('[Print Document] No file selected');
                return;
            }
            
            console.log('[Print Document] Uploading file:', file.name);
            await uploadFile(file);
        });
        
        console.log('[Print Document] Event listener attached successfully');
    } else {
        console.error('[Print Document] ERROR: File input not found!');
        console.error('[Print Document] fileInput:', fileInput);
    }
    
    // Page range selection
    const pageRange = document.getElementById('pageRange');
    if (pageRange) {
        pageRange.addEventListener('change', (e) => {
            const customRangeGroup = document.getElementById('customRangeGroup');
            if (e.target.value === 'custom') {
                customRangeGroup.style.display = 'block';
            } else {
                customRangeGroup.style.display = 'none';
            }
            calculateCost();
        });
    }

    // Calculate cost when settings change
    const copies = document.getElementById('copies');
    const startPage = document.getElementById('startPage');
    const endPage = document.getElementById('endPage');
    const orientation = document.getElementById('orientation');
    const colorMode = document.getElementById('colorMode');
    const printBtn = document.getElementById('printBtn');
    
    if (copies) copies.addEventListener('change', calculateCost);
    if (startPage) startPage.addEventListener('change', calculateCost);
    if (endPage) endPage.addEventListener('change', calculateCost);
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
    // Check payment status and pending coins every second
    paymentCheckInterval = setInterval(async () => {
        try {
            // Check payment status
            const response = await fetch('/api/payment-status');
            const data = await response.json();
            
            paidAmount = data.paid;
            updatePaymentUI();
            
            // Enable print button ONLY if enough is paid AND cost is set
            const canPrint = data.can_print && currentCost > 0 && paidAmount >= currentCost;
            document.getElementById('printBtn').disabled = !canPrint;
            
            // Check for pending coins from physical coin slot
            await checkPendingCoin();
        } catch (error) {
            console.error('Payment status error:', error);
            // On error, disable print button for safety
            document.getElementById('printBtn').disabled = true;
        }
    }, 1000);
}

async function checkPendingCoin() {
    try {
        const response = await fetch('/api/pending-coin');
        const data = await response.json();
        
        // Get all coin buttons
        const coinButtons = document.querySelectorAll('[onclick^="testCoinInsert"]');
        
        if (data.has_pending && data.pending_coin) {
            const pendingValue = data.pending_coin;
            console.log(`[Print Document] Physical coin detected: P${pendingValue}`);
            
            // Enable only the matching button, disable others
            coinButtons.forEach(btn => {
                const match = btn.onclick.toString().match(/testCoinInsert\((\d+)\)/);
                if (match) {
                    const buttonValue = parseInt(match[1]);
                    if (buttonValue === pendingValue) {
                        btn.disabled = false;
                        btn.style.background = '#FFA500'; // Orange to indicate ready
                        btn.style.fontWeight = 'bold';
                        btn.textContent = `Confirm P${buttonValue}`;
                    } else {
                        btn.disabled = true;
                        btn.style.background = '#ccc';
                        btn.textContent = `Test P${buttonValue}`;
                    }
                }
            });
        } else {
            // No pending coin - disable all buttons (wait for physical coin)
            coinButtons.forEach(btn => {
                const match = btn.onclick.toString().match(/testCoinInsert\((\d+)\)/);
                if (match) {
                    const buttonValue = parseInt(match[1]);
                    btn.disabled = true;
                    btn.style.background = '#ccc';
                    btn.textContent = `Test P${buttonValue}`;
                }
            });
        }
    } catch (error) {
        console.error('[Print Document] Error checking pending coin:', error);
    }
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
