let currentTaskId = null;
let currentFileName = '';

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeDragAndDrop();
});

function initializeDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('dragover', 'border-primary');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('dragover', 'border-primary');
        }, false);
    });

    uploadArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFileSelect(files);
    }
}

function handleFileSelect(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.name.match(/\.(doc|docx)$/)) {
            currentFileName = file.name;
            document.getElementById('fileName').textContent = file.name;
            
            const selectedFile = document.getElementById('selectedFile');
            selectedFile.classList.remove('d-none');
            
            document.getElementById('convertBtn').disabled = false;
            hideMessages();
        } else {
            showError('Please select a Word document (.doc or .docx)');
        }
    }
}

async function convertFile() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) return;

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // Reset UI
    document.getElementById('convertBtn').disabled = true;
    
    const progressContainer = document.getElementById('progressContainer');
    progressContainer.classList.remove('d-none');
    
    document.getElementById('downloadBtn').classList.add('d-none');
    hideMessages();
    updateProgress(0, 'Starting conversion...');

    try {
        const response = await axios.post('/api/upload/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        currentTaskId = response.data.task_id;
        showSuccess('Conversion started! Tracking progress...');
        pollTaskStatus();

    } catch (error) {
        showError(error.response?.data?.error || 'Conversion failed');
        resetUI();
    }
}

async function pollTaskStatus() {
    if (!currentTaskId) return;

    try {
        const response = await axios.get(`/api/task/${currentTaskId}/`);
        const task = response.data;

        if (task.status === 'processing') {
            updateProgress(task.progress, `Converting... ${task.progress}%`);
            setTimeout(pollTaskStatus, 1000);
        } else if (task.status === 'completed') {
            updateProgress(100, 'Conversion completed!');
            showSuccess('File converted successfully!');
            
            const downloadBtn = document.getElementById('downloadBtn');
            downloadBtn.classList.remove('d-none');
        } else if (task.status === 'failed') {
            throw new Error(task.message || 'Conversion failed');
        } else {
            setTimeout(pollTaskStatus, 1000);
        }

    } catch (error) {
        showError(error.message);
        resetUI();
    }
}

async function downloadFile() {
    if (!currentTaskId) return;

    try {
        const response = await axios.get(`/api/download/${currentTaskId}/`, {
            responseType: 'blob'
        });
        
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // Get filename from response headers or use original name
        const contentDisposition = response.headers['content-disposition'];
        let filename = currentFileName.replace(/\.(doc|docx)$/, '.pdf');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        showError('Failed to download file: ' + error.message);
    }
}

function updateProgress(percent, message) {
    const progressFill = document.getElementById('progressFill');
    progressFill.style.width = percent + '%';
    progressFill.textContent = percent + '%';
    
    document.getElementById('progressText').textContent = message;
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.classList.remove('d-none');
    document.getElementById('successMessage').classList.add('d-none');
}

function showSuccess(message) {
    const successDiv = document.getElementById('successMessage');
    successDiv.textContent = message;
    successDiv.classList.remove('d-none');
    document.getElementById('errorMessage').classList.add('d-none');
}

function hideMessages() {
    document.getElementById('errorMessage').classList.add('d-none');
    document.getElementById('successMessage').classList.add('d-none');
}

function resetUI() {
    document.getElementById('convertBtn').disabled = false;
    document.getElementById('progressContainer').classList.add('d-none');
    document.getElementById('downloadBtn').classList.add('d-none');
    updateProgress(0, '0%');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Auto cleanup on page load
window.addEventListener('load', () => {
    axios.post('/api/cleanup/');
});