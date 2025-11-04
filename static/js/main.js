// HR Operations Toolkit - Main JavaScript

// Global state management
const HROpsToolkit = {
    state: {
        currentTool: null,
        uploads: [],
        processing: false,
        theme: localStorage.getItem('theme') || 'dark'
    },

    // Initialize the toolkit
    init() {
        this.setupTheme();
        this.setupFileUploads();
        this.setupTooltips();
        this.setupNotifications();
        this.setupKeyboardShortcuts();
        this.trackPageView();
    },

    // Theme management
    setupTheme() {
        const htmlEl = document.documentElement;
        htmlEl.classList.add(this.state.theme);

        // Listen for theme changes
        window.addEventListener('storage', (e) => {
            if (e.key === 'theme') {
                this.state.theme = e.newValue;
                htmlEl.classList.remove('light', 'dark');
                htmlEl.classList.add(this.state.theme);
            }
        });
    },

    // File upload handling
    setupFileUploads() {
        const fileUploadAreas = document.querySelectorAll('.file-upload-area');

        fileUploadAreas.forEach(area => {
            this.setupFileUploadArea(area);
        });
    },

    setupFileUploadArea(area) {
        const input = area.querySelector('input[type="file"]');
        if (!input) return;

        // Click to upload
        area.addEventListener('click', () => {
            input.click();
        });

        // Drag and drop
        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');

            const files = Array.from(e.dataTransfer.files);
            this.handleFileSelect(files, input);
        });

        // File selection
        input.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFileSelect(files, input);
        });
    },

    handleFileSelect(files, input) {
        const maxFiles = parseInt(input.dataset.maxFiles || '10');
        const maxSize = parseInt(input.dataset.maxSize || '16') * 1024 * 1024; // 16MB default

        if (files.length > maxFiles) {
            this.showNotification(`Maximum ${maxFiles} files allowed`, 'error');
            return;
        }

        const validFiles = files.filter(file => {
            if (file.size > maxSize) {
                this.showNotification(`${file.name} exceeds maximum size limit`, 'error');
                return false;
            }
            return true;
        });

        if (validFiles.length > 0) {
            this.state.uploads = this.state.uploads.concat(validFiles);
            this.displaySelectedFiles(validFiles, input);
        }
    },

    displaySelectedFiles(files, input) {
        const container = input.parentElement.querySelector('.selected-files') ||
                         this.createFilesContainer(input);

        container.innerHTML = '';

        files.forEach((file, index) => {
            const fileElement = this.createFileElement(file, index);
            container.appendChild(fileElement);
        });

        container.classList.remove('hidden');
    },

    createFilesContainer(input) {
        const container = document.createElement('div');
        container.className = 'selected-files mt-4 space-y-2';
        input.parentElement.appendChild(container);
        return container;
    },

    createFileElement(file, index) {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg';

        const fileInfo = document.createElement('div');
        fileInfo.className = 'flex items-center space-x-3';

        const icon = this.getFileIcon(file.type);
        fileInfo.innerHTML = `
            <i class="${icon} text-slate-400"></i>
            <div>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-300">${file.name}</p>
                <p class="text-xs text-slate-500 dark:text-slate-400">${this.formatFileSize(file.size)}</p>
            </div>
        `;

        const removeButton = document.createElement('button');
        removeButton.className = 'text-red-500 hover:text-red-700';
        removeButton.innerHTML = '<i class="fas fa-times"></i>';
        removeButton.onclick = () => {
            div.remove();
            this.state.uploads = this.state.uploads.filter((_, i) => i !== index);
        };

        div.appendChild(fileInfo);
        div.appendChild(removeButton);

        return div;
    },

    getFileIcon(fileType) {
        if (fileType.startsWith('image/')) return 'fas fa-image';
        if (fileType.includes('pdf')) return 'fas fa-file-pdf';
        if (fileType.includes('word') || fileType.includes('document')) return 'fas fa-file-word';
        if (fileType.includes('excel') || fileType.includes('sheet')) return 'fas fa-file-excel';
        if (fileType.includes('zip') || fileType.includes('compressed')) return 'fas fa-file-archive';
        return 'fas fa-file';
    },

    // Tooltip setup
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');

        tooltipElements.forEach(element => {
            element.classList.add('tooltip');
        });
    },

    // Notification system
    setupNotifications() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notifications')) {
            const container = document.createElement('div');
            container.id = 'notifications';
            container.className = 'fixed top-20 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    },

    showNotification(message, type = 'info', duration = 3000) {
        const container = document.getElementById('notifications');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification p-4 rounded-lg shadow-lg max-w-sm animate-slide-in ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;

        const icon = type === 'success' ? 'fa-check-circle' :
                     type === 'error' ? 'fa-exclamation-circle' :
                     type === 'warning' ? 'fa-exclamation-triangle' :
                     'fa-info-circle';

        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icon} mr-3"></i>
                <span class="flex-grow">${message}</span>
                <button class="ml-3 hover:opacity-75" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        container.appendChild(notification);

        // Auto remove
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    },

    // Keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('search-input') ||
                                 document.getElementById('mobile-search-input');
                if (searchInput) searchInput.focus();
            }

            // Escape to close modals
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.fixed.inset-0');
                modals.forEach(modal => {
                    if (!modal.classList.contains('hidden')) {
                        modal.classList.add('hidden');
                        document.body.style.overflow = '';
                    }
                });
            }

            // Ctrl/Cmd + / for help
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                const helpButton = document.getElementById('help-button');
                if (helpButton) helpButton.click();
            }
        });
    },

    // Analytics tracking
    trackPageView() {
        // Track page view for analytics
        const path = window.location.pathname;
        const tool = this.getToolFromPath(path);

        if (tool) {
            this.trackEvent('page_view', { tool, path });
        }
    },

    trackEvent(eventName, data = {}) {
        // Send analytics data to server
        fetch('/api/analytics', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event: eventName,
                data: data,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                url: window.location.href
            })
        }).catch(err => console.log('Analytics tracking failed:', err));
    },

    getToolFromPath(path) {
        const toolMap = {
            '/id-processor': 'ID Image Processor',
            '/pdf-toolkit': 'Complete PDF Toolkit',
            '/exit-verifier': 'Employee Exit Verifier',
            '/exp-calculator': 'Candidate Experience Calculator',
            '/offer-tracker': 'Offer Release Tracker',
            '/id-checker': 'Employee ID Availability'
        };
        return toolMap[path] || null;
    },

    // Utility functions
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    },

    showLoadingOverlay(message = 'Processing...') {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner-lg mx-auto mb-4"></div>
                <p class="text-white text-lg">${message}</p>
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    },

    hideLoadingOverlay(overlay) {
        if (overlay) {
            overlay.remove();
        }
    },

    // Form validation
    validateForm(formElement) {
        const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('border-red-500');
                isValid = false;
            } else {
                input.classList.remove('border-red-500');
            }
        });

        return isValid;
    },

    // API calls
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('Operation failed. Please try again.', 'error');
            throw error;
        }
    }
};

// Tool-specific classes
class IDProcessor {
    constructor() {
        this.selectedFiles = [];
        this.processedImages = [];
    }

    async processImages(options = {}) {
        if (this.selectedFiles.length === 0) {
            HROpsToolkit.showNotification('Please select images to process', 'warning');
            return;
        }

        const overlay = HROpsToolkit.showLoadingOverlay('Processing images...');

        try {
            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                formData.append('images', file);
            });

            Object.keys(options).forEach(key => {
                formData.append(key, options[key]);
            });

            const response = await fetch('/id-processor/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.processedImages = result.images;
                this.displayProcessedImages(result.images);
                HROpsToolkit.showNotification('Images processed successfully!', 'success');
                HROpsToolkit.trackEvent('id_images_processed', {
                    count: this.selectedFiles.length
                });
            } else {
                throw new Error(result.message || 'Processing failed');
            }
        } catch (error) {
            HROpsToolkit.showNotification('Failed to process images', 'error');
            console.error('Processing error:', error);
        } finally {
            HROpsToolkit.hideLoadingOverlay(overlay);
        }
    }

    displayProcessedImages(images) {
        const container = document.getElementById('processed-images');
        if (!container) return;

        container.innerHTML = '';
        container.classList.remove('hidden');

        images.forEach((image, index) => {
            const imageCard = document.createElement('div');
            imageCard.className = 'id-preview-card';
            imageCard.innerHTML = `
                <img src="${image.url}" alt="Processed ${index + 1}" class="id-preview-image">
                <p class="text-sm font-medium text-slate-700 dark:text-slate-300">Image ${index + 1}</p>
                <button onclick="HROpsToolkit.downloadFile('${image.url}', 'processed_${index + 1}.png')"
                        class="mt-2 px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600">
                    <i class="fas fa-download mr-1"></i> Download
                </button>
            `;
            container.appendChild(imageCard);
        });
    }
}

class PDFToolkit {
    constructor() {
        this.selectedFiles = [];
        this.operation = null;
    }

    async performOperation(operation, files, options = {}) {
        this.operation = operation;

        const overlay = HROpsToolkit.showLoadingOverlay(`${this.getOperationMessage(operation)}...`);

        try {
            const formData = new FormData();
            files.forEach(file => {
                formData.append('pdfs', file);
            });

            formData.append('operation', operation);
            Object.keys(options).forEach(key => {
                formData.append(key, options[key]);
            });

            const response = await fetch('/pdf-toolkit/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                HROpsToolkit.downloadFile(result.url, result.filename);
                HROpsToolkit.showNotification('PDF operation completed successfully!', 'success');
                HROpsToolkit.trackEvent('pdf_operation_completed', {
                    operation,
                    files_count: files.length
                });
            } else {
                throw new Error(result.message || 'Operation failed');
            }
        } catch (error) {
            HROpsToolkit.showNotification('PDF operation failed', 'error');
            console.error('PDF operation error:', error);
        } finally {
            HROpsToolkit.hideLoadingOverlay(overlay);
        }
    }

    getOperationMessage(operation) {
        const messages = {
            merge: 'Merging PDFs',
            split: 'Splitting PDF',
            compress: 'Compressing PDF',
            watermark: 'Adding watermark',
            convert: 'Converting PDF',
            extract: 'Extracting content'
        };
        return messages[operation] || 'Processing PDF';
    }
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', () => {
    HROpsToolkit.init();

    // Auto-initialize tool classes based on current page
    const currentPath = window.location.pathname;

    if (currentPath.includes('id-processor')) {
        window.idProcessor = new IDProcessor();
    } else if (currentPath.includes('pdf-toolkit')) {
        window.pdfToolkit = new PDFToolkit();
    }
});

// Export for use in other scripts
window.HROpsToolkit = HROpsToolkit;
window.IDProcessor = IDProcessor;
window.PDFToolkit = PDFToolkit;