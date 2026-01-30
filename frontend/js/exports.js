/**
 * CaptionFoundry Exports Module
 * Handles export history and downloads
 */

const Exports = {
    /**
     * Initialize the exports module
     */
    init() {
        // Note: Export modal is managed by Datasets module, no event listeners needed here
        Utils.initDroppablePaths();
    },
    
    /**
     * Load and display export history
     */
    async loadExports() {
        const container = document.getElementById('exportHistory');
        container.innerHTML = Utils.loadingSpinner();
        
        try {
            const exports = await API.getExportHistory(null, 50);
            
            if (exports.length === 0) {
                container.innerHTML = Utils.emptyState(
                    'bi-archive', 
                    'No exports yet',
                    'Export a dataset to create training-ready files'
                );
                return;
            }
            
            container.innerHTML = exports.map(exp => this.renderExportItem(exp)).join('');
            
            // Bind download buttons
            container.querySelectorAll('[data-export-id]').forEach(el => {
                const downloadBtn = el.querySelector('.download-btn');
                if (downloadBtn) {
                    downloadBtn.addEventListener('click', () => {
                        window.open(API.getExportDownloadUrl(el.dataset.exportId), '_blank');
                    });
                }
            });
            
        } catch (error) {
            container.innerHTML = Utils.emptyState('bi-exclamation-triangle', 'Error loading exports', error.message);
        }
    },
    
    /**
     * Render an export item
     */
    renderExportItem(exp) {
        const statusBadge = this.getStatusBadge(exp.status);
        
        return `
            <div class="export-item" data-export-id="${exp.id}">
                <div>
                    <div class="d-flex align-items-center gap-2">
                        <i class="bi ${exp.export_type === 'zip' ? 'bi-file-earmark-zip' : 'bi-folder'} fs-4"></i>
                        <div>
                            <div class="fw-medium">
                                Export ${Utils.formatDate(exp.created_date, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </div>
                            <small class="text-muted">
                                ${exp.file_count || '?'} files
                                ${exp.total_size_bytes ? `• ${Utils.formatBytes(exp.total_size_bytes)}` : ''}
                                • ${exp.export_type.toUpperCase()}
                            </small>
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-3">
                    ${statusBadge}
                    ${exp.status === 'completed' && exp.export_type === 'zip' ? `
                        <button class="btn btn-sm btn-primary download-btn">
                            <i class="bi bi-download me-1"></i>Download
                        </button>
                    ` : ''}
                    ${exp.export_type === 'folder' && exp.export_path ? `
                        <small class="text-muted">${Utils.escapeHtml(Utils.truncate(exp.export_path, 40))}</small>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    /**
     * Get status badge HTML
     */
    getStatusBadge(status) {
        const badges = {
            'completed': '<span class="badge bg-success">Completed</span>',
            'running': '<span class="badge bg-primary">Running</span>',
            'failed': '<span class="badge bg-danger">Failed</span>',
            'cancelled': '<span class="badge bg-secondary">Cancelled</span>'
        };
        return badges[status] || `<span class="badge bg-secondary">${status}</span>`;
    }
};

// Make available globally
window.Exports = Exports;