/**
 * Enhanced Reports JavaScript
 * Provides advanced filtering, charting, and interaction features for reports
 */

// Date Range Presets
const DATE_PRESETS = {
    today: {
        label: 'Today',
        getRange: () => {
            const today = new Date();
            return {
                start: formatDate(today),
                end: formatDate(today)
            };
        }
    },
    yesterday: {
        label: 'Yesterday',
        getRange: () => {
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            return {
                start: formatDate(yesterday),
                end: formatDate(yesterday)
            };
        }
    },
    thisWeek: {
        label: 'This Week',
        getRange: () => {
            const today = new Date();
            const first = today.getDate() - today.getDay();
            const firstDay = new Date(today.setDate(first));
            const lastDay = new Date();
            return {
                start: formatDate(firstDay),
                end: formatDate(lastDay)
            };
        }
    },
    lastWeek: {
        label: 'Last Week',
        getRange: () => {
            const today = new Date();
            const first = today.getDate() - today.getDay() - 7;
            const last = first + 6;
            const firstDay = new Date(today.setDate(first));
            const lastDay = new Date(today.setDate(last));
            return {
                start: formatDate(firstDay),
                end: formatDate(lastDay)
            };
        }
    },
    thisMonth: {
        label: 'This Month',
        getRange: () => {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            return {
                start: formatDate(firstDay),
                end: formatDate(lastDay)
            };
        }
    },
    lastMonth: {
        label: 'Last Month',
        getRange: () => {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            const lastDay = new Date(today.getFullYear(), today.getMonth(), 0);
            return {
                start: formatDate(firstDay),
                end: formatDate(lastDay)
            };
        }
    },
    last7Days: {
        label: 'Last 7 Days',
        getRange: () => {
            const today = new Date();
            const sevenDaysAgo = new Date(today);
            sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
            return {
                start: formatDate(sevenDaysAgo),
                end: formatDate(today)
            };
        }
    },
    last30Days: {
        label: 'Last 30 Days',
        getRange: () => {
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            return {
                start: formatDate(thirtyDaysAgo),
                end: formatDate(today)
            };
        }
    },
    thisYear: {
        label: 'This Year',
        getRange: () => {
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), 0, 1);
            const lastDay = new Date(today.getFullYear(), 11, 31);
            return {
                start: formatDate(firstDay),
                end: formatDate(lastDay)
            };
        }
    }
};

// Utility Functions
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatHours(hours) {
    return parseFloat(hours).toFixed(1) + 'h';
}

function formatCurrency(amount, currency = '$') {
    return currency + ' ' + parseFloat(amount).toFixed(2);
}

// Initialize Date Range Presets
function initDateRangePresets() {
    const container = document.getElementById('datePresets');
    if (!container) return;

    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'btn-group btn-group-sm flex-wrap mb-3';
    buttonGroup.setAttribute('role', 'group');
    buttonGroup.setAttribute('aria-label', 'Date range presets');

    for (const [key, preset] of Object.entries(DATE_PRESETS)) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-outline-secondary';
        button.textContent = preset.label;
        button.onclick = () => applyDatePreset(key);
        buttonGroup.appendChild(button);
    }

    container.appendChild(buttonGroup);
}

function applyDatePreset(presetKey) {
    const preset = DATE_PRESETS[presetKey];
    if (!preset) return;

    const range = preset.getRange();
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    if (startDateInput) startDateInput.value = range.start;
    if (endDateInput) endDateInput.value = range.end;

    // Trigger form submission
    const form = document.getElementById('filtersForm');
    if (form) form.submit();
}

// Chart Utilities
class ReportCharts {
    static colors = {
        primary: '#3b82f6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#06b6d4',
        secondary: '#64748b'
    };

    static createProjectComparisonChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const chartData = {
            labels: data.map(p => p.name),
            datasets: [
                {
                    label: 'Total Hours',
                    data: data.map(p => p.total_hours),
                    backgroundColor: this.colors.primary + '40',
                    borderColor: this.colors.primary,
                    borderWidth: 2
                },
                {
                    label: 'Billable Hours',
                    data: data.map(p => p.billable_hours),
                    backgroundColor: this.colors.success + '40',
                    borderColor: this.colors.success,
                    borderWidth: 2
                }
            ]
        };

        return new Chart(ctx, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + 'h';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 'h';
                            }
                        }
                    }
                }
            }
        });
    }

    static createUserDistributionChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const chartData = {
            labels: data.map(u => u.name),
            datasets: [{
                label: 'Hours',
                data: data.map(u => u.hours),
                backgroundColor: [
                    this.colors.primary,
                    this.colors.success,
                    this.colors.warning,
                    this.colors.info,
                    this.colors.secondary,
                    this.colors.danger
                ],
                borderWidth: 0
            }]
        };

        return new Chart(ctx, {
            type: 'doughnut',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed.toFixed(1) + 'h (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    static createTimelineChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const chartData = {
            labels: data.labels,
            datasets: [{
                label: 'Hours per Day',
                data: data.values,
                fill: true,
                backgroundColor: this.colors.primary + '20',
                borderColor: this.colors.primary,
                borderWidth: 2,
                tension: 0.4
            }]
        };

        return new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(1) + 'h';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 'h';
                            }
                        }
                    }
                }
            }
        });
    }

    static createTaskCompletionChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const chartData = {
            labels: data.map(t => t.name),
            datasets: [{
                label: 'Hours Spent',
                data: data.map(t => t.hours),
                backgroundColor: this.colors.success + '80',
                borderColor: this.colors.success,
                borderWidth: 2
            }]
        };

        return new Chart(ctx, {
            type: 'horizontalBar',
            data: chartData,
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.x.toFixed(2) + 'h';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 'h';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Table Sorting
function initTableSorting() {
    const tables = document.querySelectorAll('.sortable-table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sortable]');
        
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="fas fa-sort ms-1 text-muted"></i>';
            
            header.addEventListener('click', () => {
                sortTable(table, index, header);
            });
        });
    });
}

function sortTable(table, columnIndex, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove sort classes from all headers
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        const icon = th.querySelector('i.fa-sort, i.fa-sort-up, i.fa-sort-down');
        if (icon) {
            icon.className = 'fas fa-sort ms-1 text-muted';
        }
    });
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aValue.replace(/[^\d.-]/g, ''));
        const bNum = parseFloat(bValue.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        }
        
        return isAscending 
            ? bValue.localeCompare(aValue)
            : aValue.localeCompare(bValue);
    });
    
    // Update table
    rows.forEach(row => tbody.appendChild(row));
    
    // Update header
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    const icon = header.querySelector('i');
    if (icon) {
        icon.className = `fas fa-sort-${isAscending ? 'down' : 'up'} ms-1`;
    }
}

// Table Search/Filter
function initTableSearch() {
    const searchInputs = document.querySelectorAll('.table-search');
    
    searchInputs.forEach(input => {
        const tableId = input.dataset.table;
        const table = document.getElementById(tableId);
        if (!table) return;
        
        input.addEventListener('input', (e) => {
            filterTable(table, e.target.value);
        });
    });
}

function filterTable(table, searchTerm) {
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

// Export Functions
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            let text = col.textContent.trim();
            // Escape quotes
            text = text.replace(/"/g, '""');
            return `"${text}"`;
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    downloadFile(csvContent, filename, 'text/csv');
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Print Report
function printReport() {
    window.print();
}

// Statistics Cards Animation
function animateStatCards() {
    const cards = document.querySelectorAll('.summary-card');
    
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'all 0.4s ease-out';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 50);
        }, index * 100);
    });
}

// Pagination
class TablePagination {
    constructor(tableId, itemsPerPage = 25) {
        this.table = document.getElementById(tableId);
        this.itemsPerPage = itemsPerPage;
        this.currentPage = 1;
        this.rows = [];
        
        if (this.table) {
            this.init();
        }
    }
    
    init() {
        const tbody = this.table.querySelector('tbody');
        this.rows = Array.from(tbody.querySelectorAll('tr'));
        this.totalPages = Math.ceil(this.rows.length / this.itemsPerPage);
        
        this.createPaginationControls();
        this.showPage(1);
    }
    
    createPaginationControls() {
        const container = document.createElement('div');
        container.className = 'pagination-controls d-flex justify-content-between align-items-center mt-3 px-3 pb-3';
        
        const info = document.createElement('div');
        info.className = 'pagination-info text-muted';
        info.id = 'paginationInfo';
        
        const controls = document.createElement('nav');
        controls.innerHTML = `
            <ul class="pagination pagination-sm mb-0">
                <li class="page-item" id="prevPage">
                    <a class="page-link" href="#" aria-label="Previous">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
                <li class="page-item" id="pageNumbers"></li>
                <li class="page-item" id="nextPage">
                    <a class="page-link" href="#" aria-label="Next">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
            </ul>
        `;
        
        container.appendChild(info);
        container.appendChild(controls);
        
        this.table.parentElement.appendChild(container);
        
        document.getElementById('prevPage').addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) this.showPage(this.currentPage - 1);
        });
        
        document.getElementById('nextPage').addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < this.totalPages) this.showPage(this.currentPage + 1);
        });
    }
    
    showPage(page) {
        this.currentPage = page;
        const start = (page - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        
        this.rows.forEach((row, index) => {
            row.style.display = (index >= start && index < end) ? '' : 'none';
        });
        
        this.updateControls();
    }
    
    updateControls() {
        const info = document.getElementById('paginationInfo');
        const start = (this.currentPage - 1) * this.itemsPerPage + 1;
        const end = Math.min(this.currentPage * this.itemsPerPage, this.rows.length);
        
        if (info) {
            info.textContent = `Showing ${start}-${end} of ${this.rows.length} entries`;
        }
        
        document.getElementById('prevPage').classList.toggle('disabled', this.currentPage === 1);
        document.getElementById('nextPage').classList.toggle('disabled', this.currentPage === this.totalPages);
    }
}

// Initialize everything on page load
document.addEventListener('DOMContentLoaded', function() {
    initDateRangePresets();
    initTableSorting();
    initTableSearch();
    animateStatCards();
    
    // Initialize pagination for large tables
    const tbody = document.querySelector('.report-table tbody');
    if (tbody && tbody.querySelectorAll('tr').length > 25) {
        new TablePagination('reportTable', 25);
    }
});

// Export for use in templates
window.ReportsEnhanced = {
    ReportCharts,
    exportTableToCSV,
    printReport,
    formatHours,
    formatCurrency,
    applyDatePreset
};

