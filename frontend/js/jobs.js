/**
 * CaptionFoundry Jobs Module
 * Handles caption generation job management
 */

const Jobs = {
    refreshInterval: null,
    
    /**
     * Initialize the jobs module
     */
    init() {
        this.bindEvents();
    },
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        document.getElementById('refreshJobsBtn').addEventListener('click', () => this.loadJobs());
        
        // Start auto-caption button in modal
        document.getElementById('startAutoCaptionBtn').addEventListener('click', () => this.startAutoCaption());
    },
    
    /**
     * Load and display jobs
     */
    async loadJobs() {
        const container = document.getElementById('jobsList');
        container.innerHTML = Utils.loadingSpinner();
        
        try {
            const jobs = await API.listJobs();
            
            if (jobs.length === 0) {
                container.innerHTML = Utils.emptyState(
                    'bi-clock-history', 
                    'No caption jobs yet',
                    'Start auto-captioning from a dataset\'s caption set'
                );
                return;
            }
            
            container.innerHTML = jobs.map(job => this.renderJobCard(job)).join('');
            
            // Bind job action buttons
            container.querySelectorAll('[data-job-id]').forEach(card => {
                const jobId = card.dataset.jobId;
                
                card.querySelector('.pause-btn')?.addEventListener('click', () => this.pauseJob(jobId));
                card.querySelector('.resume-btn')?.addEventListener('click', () => this.resumeJob(jobId));
                card.querySelector('.cancel-btn')?.addEventListener('click', () => this.cancelJob(jobId));
            });
            
            // Start auto-refresh if there are running jobs
            const hasRunningJobs = jobs.some(j => j.status === 'running' || j.status === 'pending');
            this.setAutoRefresh(hasRunningJobs);
            
        } catch (error) {
            container.innerHTML = Utils.emptyState('bi-exclamation-triangle', 'Error loading jobs', error.message);
        }
    },
    
    /**
     * Render a job card
     */
    renderJobCard(job) {
        const percent = job.total_files > 0 
            ? Math.round((job.completed_files / job.total_files) * 100) 
            : 0;
        
        const statusClass = `job-status-${job.status}`;
        
        const actionButtons = this.getJobActionButtons(job);
        
        return `
            <div class="job-card" data-job-id="${job.id}">
                <div class="job-header">
                    <div>
                        <h6 class="mb-1">
                            <i class="bi bi-cpu me-2"></i>Caption Job
                            <span class="job-status ${statusClass} ms-2">${job.status}</span>
                        </h6>
                        <small class="text-muted">
                            Model: ${Utils.escapeHtml(job.vision_model)} (${job.vision_backend})
                            • Started: ${Utils.formatRelativeTime(job.started_date || job.created_date)}
                        </small>
                    </div>
                    <div class="btn-group btn-group-sm">
                        ${actionButtons}
                    </div>
                </div>
                
                <div class="job-progress">
                    <div class="d-flex justify-content-between mb-1">
                        <small>${job.completed_files} / ${job.total_files} files</small>
                        <small>${percent}%</small>
                    </div>
                    <div class="progress" style="height: 8px;">
                        <div class="progress-bar ${job.status === 'failed' ? 'bg-danger' : ''}" 
                             style="width: ${percent}%"></div>
                    </div>
                    ${job.failed_files > 0 ? `
                        <small class="text-danger mt-1 d-block">
                            <i class="bi bi-exclamation-triangle"></i> ${job.failed_files} failed
                        </small>
                    ` : ''}
                    ${job.last_error ? `
                        <small class="text-danger mt-1 d-block">
                            Error: ${Utils.escapeHtml(Utils.truncate(job.last_error, 100))}
                        </small>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    /**
     * Get action buttons based on job status
     */
    getJobActionButtons(job) {
        switch (job.status) {
            case 'running':
                return `
                    <button class="btn btn-outline-warning pause-btn" title="Pause">
                        <i class="bi bi-pause-fill"></i>
                    </button>
                    <button class="btn btn-outline-danger cancel-btn" title="Cancel">
                        <i class="bi bi-x-lg"></i>
                    </button>
                `;
            case 'paused':
                return `
                    <button class="btn btn-outline-success resume-btn" title="Resume">
                        <i class="bi bi-play-fill"></i>
                    </button>
                    <button class="btn btn-outline-danger cancel-btn" title="Cancel">
                        <i class="bi bi-x-lg"></i>
                    </button>
                `;
            case 'pending':
                return `
                    <button class="btn btn-outline-danger cancel-btn" title="Cancel">
                        <i class="bi bi-x-lg"></i>
                    </button>
                `;
            default:
                return '';
        }
    },
    
    /**
     * Start auto-caption job
     */
    async startAutoCaption() {
        const captionSetId = Datasets.currentCaptionSetId;
        if (!captionSetId) {
            Utils.showToast('No caption set selected', 'warning');
            return;
        }
        
        const overwriteExisting = document.getElementById('overwriteExisting').checked;
        
        try {
            const job = await API.startAutoCaptionJob(captionSetId, {
                overwrite_existing: overwriteExisting
            });
            
            Utils.showToast(`Started caption job for ${job.total_files} files`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('autoCaptionModal')).hide();
            
            // Switch to jobs view
            App.showView('jobs');
            this.loadJobs();
            
        } catch (error) {
            Utils.showToast('Failed to start job: ' + error.message, 'error');
        }
    },
    
    /**
     * Pause a job
     */
    async pauseJob(jobId) {
        try {
            await API.pauseJob(jobId);
            Utils.showToast('Job paused', 'info');
            this.loadJobs();
        } catch (error) {
            Utils.showToast('Failed to pause job: ' + error.message, 'error');
        }
    },
    
    /**
     * Resume a job
     */
    async resumeJob(jobId) {
        try {
            await API.resumeJob(jobId);
            Utils.showToast('Job resumed', 'info');
            this.loadJobs();
        } catch (error) {
            Utils.showToast('Failed to resume job: ' + error.message, 'error');
        }
    },
    
    /**
     * Cancel a job
     */
    async cancelJob(jobId) {
        if (!await Utils.confirm('Cancel this job? Progress will be saved.')) {
            return;
        }
        
        try {
            await API.cancelJob(jobId);
            Utils.showToast('Job cancelled', 'info');
            this.loadJobs();
        } catch (error) {
            Utils.showToast('Failed to cancel job: ' + error.message, 'error');
        }
    },
    
    /**
     * Set auto-refresh interval
     */
    setAutoRefresh(enabled) {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        if (enabled) {
            this.refreshInterval = setInterval(() => {
                if (document.getElementById('view-jobs').style.display !== 'none') {
                    this.loadJobs();
                }
            }, 3000);
        }
    }
};

// Make available globally
window.Jobs = Jobs;