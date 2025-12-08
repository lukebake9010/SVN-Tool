/**
 * SVN External Manager - Frontend Application
 * Handles all client-side logic for the SVN External Manager web application
 */

// Global state
let externalsData = [];
let filteredData = [];
let currentSort = { column: 'name', ascending: true };
let autoRefreshInterval = null;
let currentChangelog = { logs: [], format: 'plain' };

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Check SVN status
    checkStatus();

    // Load externals
    loadExternals();

    // Load settings
    loadSettings();

    // Setup event listeners
    setupEventListeners();
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadExternals();
    });

    // Settings button
    document.getElementById('settingsBtn').addEventListener('click', function() {
        openSettingsModal();
    });

    // Search input
    document.getElementById('searchInput').addEventListener('input', function() {
        filterExternals();
    });

    // Filter checkboxes
    document.getElementById('filterModified').addEventListener('change', filterExternals);
    document.getElementById('filterClean').addEventListener('change', filterExternals);
    document.getElementById('filterError').addEventListener('change', filterExternals);

    // Table sorting
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', function() {
            const column = this.dataset.column;
            sortTable(column);
        });
    });

    // Settings form
    document.getElementById('settingsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });

    // Set working copy button
    document.getElementById('setWorkingCopyBtn').addEventListener('click', function() {
        setWorkingCopy();
    });

    // Auto-refresh toggle
    document.getElementById('autoRefreshToggle').addEventListener('change', function() {
        const intervalGroup = document.getElementById('autoRefreshIntervalGroup');
        intervalGroup.style.display = this.checked ? 'block' : 'none';
    });

    // Format select in changelog modal
    document.getElementById('formatSelect').addEventListener('change', function() {
        reformatChangelog(this.value);
    });

    // Copy changelog button
    document.getElementById('copyChangelogBtn').addEventListener('click', function() {
        copyChangelog();
    });

    // Manual log form
    document.getElementById('manualLogForm').addEventListener('submit', function(e) {
        e.preventDefault();
        fetchManualLog();
    });

    // Close modals on outside click
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

/**
 * Check SVN status
 */
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const statusBadge = document.getElementById('svnStatus');
        const workingCopyPath = document.getElementById('workingCopyPath');

        if (data.svn_available) {
            statusBadge.innerHTML = '<i class="fas fa-check-circle"></i> SVN Available';
            statusBadge.className = 'status-badge status-success';
        } else {
            statusBadge.innerHTML = '<i class="fas fa-exclamation-circle"></i> SVN Not Available';
            statusBadge.className = 'status-badge status-error';
            showToast('SVN command not found. Please install Subversion.', 'error');
        }

        workingCopyPath.textContent = data.working_copy;

    } catch (error) {
        console.error('Error checking status:', error);
    }
}

/**
 * Load externals from the API
 */
async function loadExternals() {
    const tableBody = document.getElementById('externalsTableBody');
    const emptyState = document.getElementById('emptyState');
    const errorState = document.getElementById('errorState');

    // Show loading state
    tableBody.innerHTML = `
        <tr class="loading-row">
            <td colspan="5">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i> Loading externals...
                </div>
            </td>
        </tr>
    `;

    emptyState.style.display = 'none';
    errorState.style.display = 'none';

    // Disable refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

    try {
        const response = await fetch('/api/externals');
        const data = await response.json();

        if (data.success) {
            externalsData = data.externals;
            filteredData = [...externalsData];

            // Update last scan time
            const timestamp = new Date(data.timestamp);
            document.getElementById('lastScanTime').textContent = timestamp.toLocaleString();

            if (externalsData.length === 0) {
                tableBody.innerHTML = '';
                emptyState.style.display = 'block';
            } else {
                renderTable();
            }

            showToast(`Loaded ${data.count} external(s)`, 'success');

        } else {
            throw new Error(data.error || 'Failed to load externals');
        }

    } catch (error) {
        console.error('Error loading externals:', error);
        tableBody.innerHTML = '';
        errorState.style.display = 'block';
        document.getElementById('errorMessage').textContent = error.message;
        showToast('Error loading externals: ' + error.message, 'error');

    } finally {
        // Re-enable refresh button
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    }
}

/**
 * Render the externals table
 */
function renderTable() {
    const tableBody = document.getElementById('externalsTableBody');
    const externalsCount = document.getElementById('externalsCount');

    if (filteredData.length === 0) {
        tableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5">No externals match your filters</td>
            </tr>
        `;
        externalsCount.textContent = '0 externals';
        return;
    }

    // Sort data
    const sortedData = [...filteredData].sort((a, b) => {
        const aVal = a[currentSort.column] || '';
        const bVal = b[currentSort.column] || '';

        if (currentSort.ascending) {
            return aVal.toString().localeCompare(bVal.toString());
        } else {
            return bVal.toString().localeCompare(aVal.toString());
        }
    });

    // Render rows
    tableBody.innerHTML = sortedData.map(external => {
        const statusClass = getStatusClass(external.status);
        const statusIcon = getStatusIcon(external.status);

        // Build change details HTML if present
        let changeDetailsHTML = '';
        let viewLogButton = '';

        // Determine the revision range for changelog
        let oldRev = external.revision;
        let newRev = 'HEAD';
        let hasRevisionChange = false;

        if (external.change_details && external.status === 'changed') {
            const details = [];
            if (external.change_details.revision) {
                details.push(`Revision: ${escapeHtml(external.change_details.revision.old)} → ${escapeHtml(external.change_details.revision.new)}`);
                // Use old and new revisions for the changelog
                oldRev = external.change_details.revision.old;
                newRev = external.change_details.revision.new;
                hasRevisionChange = true;
            }
            if (external.change_details.url) {
                details.push(`URL changed`);
            }
            if (external.change_details.path) {
                details.push(`Path changed`);
            }
            if (details.length > 0) {
                changeDetailsHTML = `<div class="change-details">${details.join(' • ')}</div>`;
            }
        } else if (external.status === 'new') {
            changeDetailsHTML = `<div class="change-details">Newly added external</div>`;
        }

        // Create appropriate View Log button
        if (hasRevisionChange) {
            viewLogButton = `
                <button class="btn btn-sm btn-primary" onclick="viewChangelog('${escapeHtml(external.url)}', '${escapeHtml(oldRev)}', '${escapeHtml(newRev)}', '${escapeHtml(external.name)}')">
                    <i class="fas fa-list"></i> View Changes
                </button>
            `;
        } else {
            viewLogButton = `
                <button class="btn btn-sm btn-secondary" onclick="viewChangelog('${escapeHtml(external.url)}', '${escapeHtml(external.revision)}', 'HEAD', '${escapeHtml(external.name)}')">
                    <i class="fas fa-history"></i> View Log
                </button>
            `;
        }

        return `
            <tr class="external-row status-${statusClass}" data-path="${external.path}">
                <td>
                    <div class="external-name">${escapeHtml(external.name)}</div>
                    <div class="external-path">${escapeHtml(external.path)}</div>
                    ${changeDetailsHTML}
                </td>
                <td>
                    <span class="revision-badge">${escapeHtml(external.revision)}</span>
                </td>
                <td>
                    <div class="external-url" title="${escapeHtml(external.url)}">
                        ${escapeHtml(external.url)}
                    </div>
                </td>
                <td>
                    <span class="status-badge status-${statusClass}">
                        <i class="${statusIcon}"></i> ${escapeHtml(external.status)}
                    </span>
                </td>
                <td>
                    ${viewLogButton}
                </td>
            </tr>
        `;
    }).join('');

    externalsCount.textContent = `${filteredData.length} external(s)`;

    // Update sort indicators
    updateSortIndicators();
}

/**
 * Filter externals based on search and status filters
 */
function filterExternals() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const showModified = document.getElementById('filterModified').checked;
    const showClean = document.getElementById('filterClean').checked;
    const showError = document.getElementById('filterError').checked;

    filteredData = externalsData.filter(external => {
        // Search filter
        const matchesSearch = !searchTerm ||
            external.name.toLowerCase().includes(searchTerm) ||
            external.path.toLowerCase().includes(searchTerm) ||
            external.url.toLowerCase().includes(searchTerm);

        // Status filter - 'changed' and 'new' are considered 'modified'
        const matchesStatus =
            (showModified && (external.status === 'changed' || external.status === 'new')) ||
            (showClean && external.status === 'clean') ||
            (showError && (external.status === 'error' || external.status === 'missing'));

        return matchesSearch && matchesStatus;
    });

    renderTable();
}

/**
 * Sort table by column
 */
function sortTable(column) {
    if (currentSort.column === column) {
        currentSort.ascending = !currentSort.ascending;
    } else {
        currentSort.column = column;
        currentSort.ascending = true;
    }

    renderTable();
}

/**
 * Update sort indicators in table headers
 */
function updateSortIndicators() {
    document.querySelectorAll('.sortable').forEach(header => {
        const icon = header.querySelector('i');
        const column = header.dataset.column;

        if (column === currentSort.column) {
            icon.className = currentSort.ascending ? 'fas fa-sort-up' : 'fas fa-sort-down';
            header.classList.add('sorted');
        } else {
            icon.className = 'fas fa-sort';
            header.classList.remove('sorted');
        }
    });
}

/**
 * View changelog for an external
 */
async function viewChangelog(url, oldRev, newRev, name) {
    const modal = document.getElementById('changelogModal');
    const content = document.getElementById('changelogContent');
    const pathElement = document.getElementById('changelogPath');
    const revRangeElement = document.getElementById('changelogRevRange');
    const formatSelect = document.getElementById('formatSelect');

    // Open modal
    modal.style.display = 'flex';

    // Set info
    pathElement.textContent = name;
    revRangeElement.textContent = `r${oldRev}:${newRev}`;

    // Show loading
    content.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i> Loading changelog...
        </div>
    `;

    try {
        const format = formatSelect.value;
        const response = await fetch(`/api/log?url=${encodeURIComponent(url)}&old_rev=${oldRev}&new_rev=${newRev}&format=${format}`);
        const data = await response.json();

        if (data.success) {
            currentChangelog = { logs: data.logs, format: data.format };
            displayChangelog(data.logs, data.formatted);
        } else {
            throw new Error(data.error || 'Failed to load changelog');
        }

    } catch (error) {
        console.error('Error loading changelog:', error);
        content.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Error loading changelog: ${escapeHtml(error.message)}</p>
            </div>
        `;
        showToast('Error loading changelog: ' + error.message, 'error');
    }
}

/**
 * Display changelog in the modal
 */
function displayChangelog(logs, formatted) {
    const content = document.getElementById('changelogContent');

    if (logs.length === 0) {
        content.innerHTML = `
            <div class="empty-message">
                <i class="fas fa-info-circle"></i>
                <p>No changes found in this revision range.</p>
            </div>
        `;
        return;
    }

    // Display formatted changelog
    content.innerHTML = `<pre class="changelog-text">${escapeHtml(formatted)}</pre>`;
}

/**
 * Reformat changelog with different format
 */
async function reformatChangelog(format) {
    if (!currentChangelog.logs || currentChangelog.logs.length === 0) {
        return;
    }

    const content = document.getElementById('changelogContent');
    content.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner fa-spin"></i> Formatting...
        </div>
    `;

    try {
        const response = await fetch('/api/log/format', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                logs: currentChangelog.logs,
                format: format
            })
        });

        const data = await response.json();

        if (data.success) {
            currentChangelog.format = data.format;
            displayChangelog(currentChangelog.logs, data.formatted);
        } else {
            throw new Error(data.error || 'Failed to format changelog');
        }

    } catch (error) {
        console.error('Error formatting changelog:', error);
        showToast('Error formatting changelog: ' + error.message, 'error');
    }
}

/**
 * Copy changelog to clipboard
 */
async function copyChangelog() {
    const content = document.querySelector('#changelogContent .changelog-text');

    if (!content) {
        showToast('No changelog to copy', 'warning');
        return;
    }

    try {
        await navigator.clipboard.writeText(content.textContent);
        showToast('Changelog copied to clipboard!', 'success');

        // Visual feedback
        const btn = document.getElementById('copyChangelogBtn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('btn-success');

        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.classList.remove('btn-success');
        }, 2000);

    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showToast('Failed to copy to clipboard', 'error');
    }
}

/**
 * Close changelog modal
 */
function closeChangelogModal() {
    document.getElementById('changelogModal').style.display = 'none';
}

/**
 * Open settings modal
 */
function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';
    loadSettingsForm();
}

/**
 * Close settings modal
 */
function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

/**
 * Load settings into form
 */
async function loadSettingsForm() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        document.getElementById('workingCopyInput').value = config.working_copy_path || '';
        document.getElementById('autoRefreshToggle').checked = config.auto_refresh || false;
        document.getElementById('autoRefreshInterval').value = config.auto_refresh_interval || 60;
        document.getElementById('defaultFormat').value = config.default_format || 'plain';

        // Show/hide auto-refresh interval
        const intervalGroup = document.getElementById('autoRefreshIntervalGroup');
        intervalGroup.style.display = config.auto_refresh ? 'block' : 'none';

    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

/**
 * Save settings
 */
async function saveSettings() {
    const config = {
        auto_refresh: document.getElementById('autoRefreshToggle').checked,
        auto_refresh_interval: parseInt(document.getElementById('autoRefreshInterval').value),
        default_format: document.getElementById('defaultFormat').value
    };

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.success) {
            showToast('Settings saved successfully', 'success');
            loadSettings(); // Reload settings
            closeSettingsModal();
        } else {
            throw new Error(data.error || 'Failed to save settings');
        }

    } catch (error) {
        console.error('Error saving settings:', error);
        showToast('Error saving settings: ' + error.message, 'error');
    }
}

/**
 * Set working copy path
 */
async function setWorkingCopy() {
    const path = document.getElementById('workingCopyInput').value.trim();

    if (!path) {
        showToast('Please enter a path', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/working-copy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });

        const data = await response.json();

        if (data.success) {
            showToast('Working copy path updated', 'success');
            document.getElementById('workingCopyPath').textContent = data.path;
            loadExternals(); // Reload externals
        } else {
            throw new Error(data.error || 'Failed to set working copy');
        }

    } catch (error) {
        console.error('Error setting working copy:', error);
        showToast('Error: ' + error.message, 'error');
    }
}

/**
 * Load settings and apply
 */
async function loadSettings() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Apply auto-refresh
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }

        if (config.auto_refresh) {
            const interval = (config.auto_refresh_interval || 60) * 1000;
            autoRefreshInterval = setInterval(() => {
                loadExternals();
            }, interval);
        }

        // Set default format in changelog modal
        document.getElementById('formatSelect').value = config.default_format || 'plain';

    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

/**
 * Open manual log lookup modal
 */
function openManualLogModal() {
    document.getElementById('manualLogModal').style.display = 'flex';
}

/**
 * Close manual log lookup modal
 */
function closeManualLogModal() {
    document.getElementById('manualLogModal').style.display = 'none';
}

/**
 * Fetch manual log
 */
async function fetchManualLog() {
    const url = document.getElementById('manualUrl').value.trim();
    const oldRev = document.getElementById('manualOldRev').value.trim();
    const newRev = document.getElementById('manualNewRev').value.trim();

    if (!url || !oldRev || !newRev) {
        showToast('Please fill in all fields', 'warning');
        return;
    }

    closeManualLogModal();
    viewChangelog(url, oldRev, newRev, 'Manual Lookup');
}

/**
 * Get status class for styling
 */
function getStatusClass(status) {
    const statusMap = {
        'clean': 'success',
        'changed': 'warning',
        'new': 'info',
        'modified': 'warning',
        'error': 'error',
        'missing': 'error',
        'unknown': 'default'
    };

    return statusMap[status] || 'default';
}

/**
 * Get status icon
 */
function getStatusIcon(status) {
    const iconMap = {
        'clean': 'fas fa-check-circle',
        'changed': 'fas fa-edit',
        'new': 'fas fa-plus-circle',
        'modified': 'fas fa-exclamation-circle',
        'error': 'fas fa-times-circle',
        'missing': 'fas fa-question-circle',
        'unknown': 'fas fa-circle'
    };

    return iconMap[status] || 'fas fa-circle';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'exclamation-circle' :
                 type === 'warning' ? 'exclamation-triangle' : 'info-circle';

    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => container.removeChild(toast), 300);
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
