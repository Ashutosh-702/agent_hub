// LinkedIn SDR Frontend JavaScript

// Global state
let selectedFile = null;
let batches = [];

// API Configuration
const API_BASE = window.location.origin;

// =====================
// UTILITY FUNCTIONS
// =====================

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }
    
    // More than 24 hours
    const days = Math.floor(diff / 86400000);
    if (days < 7) {
        return `${days} day${days !== 1 ? 's' : ''} ago`;
    }
    
    return date.toLocaleDateString();
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideToast();
        }, 5000);
    } else {
        // Fallback to alert if toast elements don't exist
        alert(message);
    }
}

function hideToast() {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.style.display = 'none';
    }
}

// =====================
// FILE UPLOAD FUNCTIONS
// =====================

function handleDragOver(event) {
    event.preventDefault();
    const dropZone = document.getElementById('dropZone');
    dropZone.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    const dropZone = document.getElementById('dropZone');
    dropZone.classList.remove('dragover');
}

function handleFileDrop(event) {
    event.preventDefault();
    const dropZone = document.getElementById('dropZone');
    dropZone.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelection(files[0]);
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFileSelection(file);
    }
}

function handleFileSelection(file) {
    // Validate file type
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showToast('Please select a CSV file', 'error');
        return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('File size must be less than 10MB', 'error');
        return;
    }
    
    selectedFile = file;
    displayFileInfo(file);
    
    // Enable submit button
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.disabled = false;
    }
}

function displayFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileCount = document.getElementById('fileCount');
    
    if (fileInfo && fileName && fileSize) {
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        
        // Try to estimate row count (rough estimation)
        const estimatedRows = Math.max(1, Math.floor(file.size / 100) - 1); // Assuming ~100 bytes per row
        if (fileCount) {
            fileCount.textContent = `Estimated ~${estimatedRows} leads`;
        }
        
        fileInfo.style.display = 'block';
    }
}

function removeFile() {
    selectedFile = null;
    
    const fileInfo = document.getElementById('fileInfo');
    const csvFileInput = document.getElementById('csvFile');
    const submitBtn = document.getElementById('submitBtn');
    
    if (fileInfo) fileInfo.style.display = 'none';
    if (csvFileInput) csvFileInput.value = '';
    if (submitBtn) submitBtn.disabled = true;
}

// =====================
// FORM SUBMISSION
// =====================

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUploadSubmit);
    }
});

async function handleUploadSubmit(event) {
    event.preventDefault();
    
    if (!selectedFile) {
        showToast('Please select a CSV file', 'error');
        return;
    }
    
    const formData = new FormData();
    const linkedinAccount = document.getElementById('linkedin_account').value;
    const password = document.getElementById('password').value;
    
    if (!linkedinAccount || !password) {
        showToast('Please fill in all LinkedIn credentials', 'error');
        return;
    }
    
    // Show loading overlay
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
    
    // Prepare form data
    formData.append('file', selectedFile);
    formData.append('account_id', linkedinAccount);
    formData.append('password', password);
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/upload-leads`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(`Batch created successfully! Batch ID: ${result.batch_id}`, 'success');
            
            // Redirect to batches page after a short delay
            setTimeout(() => {
                window.location.href = 'batches.html';
            }, 2000);
        } else {
            const errorData = await response.json();
            showToast(errorData.detail || 'Failed to create batch', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Network error. Please check your connection.', 'error');
    } finally {
        // Hide loading overlay
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }
}

// =====================
// BATCH MANAGEMENT FUNCTIONS
// =====================

async function loadBatches() {
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const batchList = document.getElementById('batchList');
    
    // Show loading state
    if (loadingState) loadingState.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';
    if (batchList) batchList.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/batches`);
        
        if (response.ok) {
            batches = await response.json();
            
            if (batches.length === 0) {
                // Show empty state
                if (loadingState) loadingState.style.display = 'none';
                if (emptyState) emptyState.style.display = 'block';
            } else {
                // Show batch list
                if (loadingState) loadingState.style.display = 'none';
                if (batchList) batchList.style.display = 'block';
                renderBatches();
                updateStats();
            }
        } else {
            throw new Error('Failed to load batches');
        }
    } catch (error) {
        console.error('Error loading batches:', error);
        showToast('Failed to load batches', 'error');
        
        // Show empty state as fallback
        if (loadingState) loadingState.style.display = 'none';
        if (emptyState) emptyState.style.display = 'block';
    }
}

function renderBatches() {
    const batchList = document.getElementById('batchList');
    if (!batchList || !batches) return;
    
    batchList.innerHTML = batches.map(batch => createBatchCard(batch)).join('');
}

function createBatchCard(batch) {
    const statusClass = `status-${batch.status.toLowerCase().replace(' ', '-')}`;
    const isProcessing = batch.status.toLowerCase() === 'processing';
    const isReady = batch.status.toLowerCase() === 'ready';
    const isCompleted = batch.status.toLowerCase() === 'completed';
    
    let progressHtml = '';
    if (isProcessing && batch.progress) {
        const percentage = Math.round((batch.progress.completed / batch.progress.total) * 100);
        progressHtml = `
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${percentage}%"></div>
            </div>
            <small>${batch.progress.completed}/${batch.progress.total} completed (${percentage}%)</small>
        `;
    }
    
    return `
        <div class="batch-card">
            <div class="batch-header">
                <div class="batch-info">
                    <div class="batch-title">
                        <i class="fas fa-layer-group"></i>
                        Batch #${batch.id}
                    </div>
                    <div class="batch-meta">
                        <span><i class="fas fa-users"></i> ${batch.lead_count || 0} leads</span>
                        <span><i class="fas fa-clock"></i> ${formatDate(batch.created_at)}</span>
                        <span><i class="fas fa-envelope"></i> ${batch.account_id}</span>
                    </div>
                    <span class="batch-status ${statusClass}">
                        ${getStatusIcon(batch.status)} ${batch.status}
                    </span>
                    ${progressHtml}
                </div>
                <div class="batch-actions">
                    ${isReady ? `
                        <button class="btn primary" onclick="processBatch('${batch.id}')">
                            <i class="fas fa-play"></i> Process Batch
                        </button>
                    ` : ''}
                    ${isProcessing ? `
                        <button class="btn warning" onclick="viewBatchDetails('${batch.id}')">
                            <i class="fas fa-eye"></i> View Progress
                        </button>
                    ` : ''}
                    ${isCompleted ? `
                        <button class="btn success" onclick="viewBatchResults('${batch.id}')">
                            <i class="fas fa-chart-line"></i> View Results
                        </button>
                    ` : ''}
                    <button class="btn secondary" onclick="viewBatchDetails('${batch.id}')">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                </div>
            </div>
        </div>
    `;
}

function getStatusIcon(status) {
    const statusLower = status.toLowerCase();
    if (statusLower === 'ready') return '<i class="fas fa-clock"></i>';
    if (statusLower === 'processing') return '<i class="fas fa-spinner fa-spin"></i>';
    if (statusLower === 'completed') return '<i class="fas fa-check-circle"></i>';
    if (statusLower === 'failed') return '<i class="fas fa-exclamation-circle"></i>';
    return '<i class="fas fa-circle"></i>';
}

function updateStats() {
    const totalBatchesEl = document.getElementById('totalBatches');
    const activeBatchesEl = document.getElementById('activeBatches');
    const completedBatchesEl = document.getElementById('completedBatches');
    
    if (!batches) return;
    
    const total = batches.length;
    const active = batches.filter(b => b.status.toLowerCase() === 'processing').length;
    const completed = batches.filter(b => b.status.toLowerCase() === 'completed').length;
    
    if (totalBatchesEl) totalBatchesEl.textContent = total;
    if (activeBatchesEl) activeBatchesEl.textContent = active;
    if (completedBatchesEl) completedBatchesEl.textContent = completed;
}

// =====================
// BATCH ACTIONS
// =====================

async function processBatch(batchId) {
    if (!confirm('Are you sure you want to start processing this batch?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/v1/process-batch/${batchId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(`Batch processing started! ${result.scheduled_count} connections scheduled.`, 'success');
            
            // Reload batches to show updated status
            setTimeout(() => {
                loadBatches();
            }, 1000);
        } else {
            const errorData = await response.json();
            showToast(errorData.detail || 'Failed to start batch processing', 'error');
        }
    } catch (error) {
        console.error('Error processing batch:', error);
        showToast('Network error. Please try again.', 'error');
    }
}

async function viewBatchDetails(batchId) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/batch/${batchId}/details`);
        
        if (response.ok) {
            const details = await response.json();
            showBatchModal(details);
        } else {
            showToast('Failed to load batch details', 'error');
        }
    } catch (error) {
        console.error('Error loading batch details:', error);
        showToast('Failed to load batch details', 'error');
    }
}

function viewBatchResults(batchId) {
    // This could open a detailed results page or modal
    viewBatchDetails(batchId);
}

function showBatchModal(batchDetails) {
    const modal = document.getElementById('batchModal');
    const modalBody = document.getElementById('modalBody');
    
    if (!modal || !modalBody) return;
    
    modalBody.innerHTML = `
        <div class="batch-detail-content">
            <h4>Batch #${batchDetails.id}</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <strong>Status:</strong> ${batchDetails.status}
                </div>
                <div class="detail-item">
                    <strong>Total Leads:</strong> ${batchDetails.lead_count}
                </div>
                <div class="detail-item">
                    <strong>Account:</strong> ${batchDetails.account_id}
                </div>
                <div class="detail-item">
                    <strong>Created:</strong> ${formatDate(batchDetails.created_at)}
                </div>
            </div>
            
            ${batchDetails.batch_values ? `
                <h5>Individual Connections:</h5>
                <div class="connection-list">
                    ${batchDetails.batch_values.map(connection => `
                        <div class="connection-item">
                            <span class="connection-url">${connection.linkedin_url}</span>
                            <span class="connection-status ${connection.status}">${connection.status}</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    modal.style.display = 'flex';
}

function closeBatchModal() {
    const modal = document.getElementById('batchModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function refreshBatches() {
    loadBatches();
    showToast('Batches refreshed', 'success');
}

// =====================
// EVENT LISTENERS
// =====================

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('batchModal');
    if (event.target === modal) {
        closeBatchModal();
    }
});

// Handle escape key to close modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeBatchModal();
        hideToast();
    }
});

// =====================
// INITIALIZATION
// =====================

// Auto-refresh functionality for batch page
if (window.location.pathname.includes('batches.html')) {
    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadBatches();
    }, 30000);
}
