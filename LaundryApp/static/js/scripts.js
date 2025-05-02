// ==================== CORE MODULES ====================
(() => {
    const BaseModule = (() => {
        // Navbar scroll behavior
        const initNavbarScroll = () => {
            const navbar = document.querySelector('.main-header');
            if (!navbar) return;

            let lastScroll = 0;
            const freezeThreshold = 50;

            window.addEventListener('scroll', () => {
                const currentScroll = window.scrollY;
                
                if (currentScroll > freezeThreshold) {
                    navbar.classList.add('frozen');
                    navbar.style.animation = 'smoothFreeze 0.3s forwards';
                    
                    if (currentScroll > lastScroll) {
                        navbar.style.transform = 'translateY(-100%)';
                    } else {
                        navbar.style.transform = 'translateY(0)';
                    }
                } else {
                    navbar.classList.remove('frozen');
                    navbar.style.transform = 'translateY(0)';
                }
                
                lastScroll = currentScroll;
            });
        };

        // Sidebar toggle
        const initSidebar = () => {
            const toggleBtn = document.querySelector('.sidebar-toggle');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => {
                    document.querySelector('.just-sidebar').classList.toggle('collapsed');
                });
            }
        };

        // Toast notification
        const showToast = (message, type = 'success') => {
            const bgColor = type === 'success' ? '#28a745' : '#dc3545';
            Toastify({
                text: message,
                duration: 3000,
                gravity: "top",
                backgroundColor: bgColor
            }).showToast();
        };

        return {
            init: () => {
                initNavbarScroll();
                initSidebar();
            },
            showToast
        };
    })();

    // ==================== DASHBOARD MODULE V1 ====================
    //Production Chart
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize charts only if elements exist
        if (document.getElementById('productionChart')) {
            initializeProductionChart();
        }
        
        if (document.getElementById('utilizationChart')) {
            initializeUtilizationChart();
        }
    });

    let productionChart = null;

    function initializeProductionChart() {
        // Check if Chart.js is loaded

        const chartElement = document.getElementById('productionChart');
        if (!chartElement) return;
        
        if (typeof Chart === "undefined") {
            console.error("Chart.js is not loaded");
            return;
        }

        // Get chart elements
        const ctx = chartElement.getContext('2d');
        if (!ctx) {
            console.error("Production chart canvas context not found");
            return;
        }

        // Get data from Django
        const labelsElement = document.getElementById('chart-labels');
        const valuesElement = document.getElementById('chart-values');
        
        if (!labelsElement || !valuesElement) {
            console.error("Chart data elements not found");
            return;
        }

        try {
            const labels = JSON.parse(labelsElement.textContent);
            const values = JSON.parse(valuesElement.textContent);

            // Create gradient
            const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
            gradient.addColorStop(0, "rgba(13, 110, 253, 0.7)");
            gradient.addColorStop(1, "rgba(13, 110, 253, 0.2)");

            // Destroy previous chart if exists
            if (productionChart) {
                productionChart.destroy();
            }

            // Create new chart
            productionChart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Production Output (Tonnage)",
                        data: values,
                        borderColor: "#0d6efd",
                        backgroundColor: gradient,
                        pointBackgroundColor: "#ffffff",
                        pointBorderColor: "#0d6efd",
                        pointRadius: 1,
                        fill: true,
                        tension: 0.4,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true, 
                            position: "top", 
                            labels: { 
                                color: "#333", 
                                font: { size: 14 } 
                            } 
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return ` ${context.raw.toLocaleString()} Tonnage`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: "Time", color: "#666" },
                            ticks: { color: "#555", autoSkip: true, maxTicksLimit: 10 },
                            grid: { color: "rgba(255, 255, 255, 0.1)" }
                        },
                        y: {
                            title: { display: true, text: "Tonnage", color: "#666" },
                            beginAtZero: true,
                            ticks: { color: "#555" },
                            grid: { color: "rgba(0, 0, 0, 0.06)" }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error initializing production chart:", error);
        }
    }

    function initializeUtilizationChart() {
        const chartElement = document.getElementById('utilizationChart'); 
        if (!chartElement) return;
        if (!utilizationDataElement) {
            console.error("Utilization data element not found");
            return;
        }

        const ctx = chartElement.getContext('2d');
        if (!ctx) {
            console.error("Utilization chart canvas context not found");
            return;
        }

        try {
            let utilizationData = JSON.parse(utilizationDataElement.textContent);
            
            new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: ["Operational Hours", "Idle Hours"],
                    datasets: [{
                        data: [utilizationData.operational_hours, utilizationData.idle_hours],
                        backgroundColor: [
                            // Gradient for operational hours (blue)
                            (() => {
                                let gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
                                gradient.addColorStop(0, "rgba(76, 0, 255, 0.62)");
                                gradient.addColorStop(1, "rgba(8, 120, 241, 0.8)");
                                return gradient;
                            })(),
                            // Gradient for idle hours (green)
                            (() => {
                                let gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
                                gradient.addColorStop(0, "rgba(13, 74, 4, 0.99)");
                                gradient.addColorStop(1, "rgba(88, 130, 4, 0.85)");
                                return gradient;
                            })()
                        ],
                        borderColor: "#fff",
                        borderWidth: 2,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.raw.toFixed(2)} hours`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error("Error initializing utilization chart:", error);
        }
    }



    function updateUtilizationChart(utilizationData) {
        const utilizationChart = Chart.getChart("utilizationChart");
        if (utilizationChart) {
            utilizationChart.data.datasets[0].data = [
                utilizationData.operational_hours,
                utilizationData.idle_hours
            ];
            utilizationChart.update();
        }
    }

    // ==================== NEW WIDGETS & TABLE FUNCTIONALITY ====================
    function updateWidgets() {
        // const widgetData = JSON.parse(document.getElementById('widget-data').textContent);
        const widgetDataElement = document.getElementById('widget-data');
        if (!widgetDataElement) return;

        try {
            const widgetData = JSON.parse(widgetDataElement.textContent);
            
            //  Production Widget if exists
            const productionElement = document.querySelector('.production-data');
            if (productionElement && widgetData.total_production !== undefined) {
                productionElement.textContent = widgetData.total_production;
            }
            
            //  RAP Consumption Widget if exists
            const rapElements = document.querySelectorAll('.small-box h3');
            if (rapElements.length > 1 && widgetData.rap_consumption !== undefined) {
                rapElements[1].textContent = widgetData.rap_consumption;
            }

            // Electricity Consumption Widget if exists
            const electricityElement = document.querySelector('.electricity-data');
            if (electricityElement && widgetData.electricity_consumption !== undefined) {
                electricityElement.textContent = widgetData.electricity_consumption;
            }
        } catch (error) {
            console.error('Error updating widgets:', error);
        }

    }

    // scripts.js (updated initializeMaterialTable function)
    // scripts.js (updated table initialization)
    function initializeMaterialTable() {
        const materialDataElement = document.getElementById('material-data');
        if (!materialDataElement || !materialDataElement.textContent) return;
    
        try {
            const rawData = JSON.parse(materialDataElement.textContent);
            const tbody = document.getElementById('materialTableBody');
            
            // Clear existing rows
            tbody.innerHTML = '';
            
            // Filter and clean data
            const cleanData = rawData.filter(item => 
                item.MaterialName && 
                item.MaterialName.trim() && 
                !item.MaterialName.toLowerCase().includes('undefined')
            );
            
            // Create new rows with numbering
            cleanData.forEach((item, index) => {
                const row = document.createElement('tr');
                
                // Ensure proper values
                const materialName = item.MaterialName.trim() || 'Other Material';
                const quantity = item.Quantity !== undefined 
                    ? item.Quantity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) 
                    : '0.00';
                
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${materialName}</td>
                    <td class="text-end">${quantity} </td>
                `;
                tbody.appendChild(row);
            });
    
        } catch (error) {
            console.error('Error initializing material table:', error);
            // Fallback empty row if there's an error
            const tbody = document.getElementById('materialTableBody');
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">No material data available</td></tr>';
        }
    }
    // Initialize new features when DOM loads
    document.addEventListener('DOMContentLoaded', () => {
        updateWidgets();
        initializeMaterialTable();
    });


    // ==================== DATA TABLES MODULE ====================

    const DataTablesModule = (() => {
        const commonConfig = {
            dom: 'B<"clear">lfrtip',
            buttons: ['copy', 'csv', 'excel', 'pdf', 'print'],
            responsive: true,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search...",
                paginate: {
                    first: "<i class='fas fa-angle-double-left'></i>",
                    previous: "<i class='fas fa-chevron-left'></i>",
                    next: "<i class='fas fa-chevron-right'></i>",
                    last: "<i class='fas fa-angle-double-right'></i>"
                }
            },
            pagingType: "full_numbers"
        };

        return {
            init: () => {
                if (document.getElementById('batchTable')) {
                    $('#batchTable').DataTable($.extend({}, commonConfig, {
                        scrollX: true,
                        autoWidth: false
                    }));
                }

                if (document.getElementById('processedFilesTable')) {
                    $('#processedFilesTable').DataTable($.extend({}, commonConfig, {
                        pageLength: 10,
                        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]]
                    }));
                }
            }
        };
    })();

    // ==================== SCHEDULE LIST MODULE ====================

    const ScheduleListModule = (() => {
        return {
            init: () => {
                if (!document.getElementById('scheduleTable')) return;

                // Toggle schedule status
                document.querySelectorAll('.toggle-schedule').forEach(btn => {
                    btn.addEventListener('change', async function() {
                        const scheduleId = this.dataset.scheduleId;
                        const isActive = this.checked;
                        
                        try {
                            const response = await fetch(`/api/schedules/${scheduleId}/toggle/`, {
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ is_active: isActive })
                            });
                            
                            const data = await response.json();
                            if (!response.ok) throw new Error(data.message || 'Failed to toggle schedule');
                            
                            BaseModule.showToast(`Schedule ${isActive ? 'activated' : 'deactivated'}`, 'success');
                        } catch (error) {
                            console.error('Error toggling schedule:', error);
                            this.checked = !isActive; // Revert UI on error
                            BaseModule.showToast(error.message, 'error');
                        }
                    });
                });
            }
        };
    })();

    // ==================== FILTER CONTROLS ==================== 
    // (DITO ILALAGAY ANG NUMBER 3)
    const initFilters = () => {
        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.addEventListener('click', function() {
                const filter = this.dataset.filter;
                
                // 1. Update active button styles
                document.querySelectorAll('[data-filter]').forEach(b => {
                    b.classList.remove('active', 'btn-primary');
                    b.classList.add('btn-outline-secondary');
                });
                this.classList.add('active', 'btn-primary');
                this.classList.remove('btn-outline-secondary');
                
                // 2. Filter the list items
                document.querySelectorAll('#processedFilesList li').forEach(item => {
                    item.style.display = (filter === 'all' || item.dataset.status === filter) 
                        ? '' 
                        : 'none';
                });
            });
        });
    };


    // ==================== PARSING MODULE ====================
    const ParsingModule = (() => {
        let socket = null;
        let progressInterval = null;

        // WebSocket connection
        const connectWebSocket = (taskId = null) => {
            const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsPath = taskId ? `ws/parsing_progress/${taskId}/` : 'ws/parsing_progress/';
            
            socket = new WebSocket(protocol + window.location.host + `/ws/${wsPath}`

            );

            socket.onmessage = (e) => {
                const data = JSON.parse(e.data);
                updateProgressUI(data);
                
                if (data.state === 'COMPLETED' || data.state === 'FAILED') {
                    updateParsingComplete();
                }
            };

            socket.onclose = (e) => {
                if (document.getElementById('parsingStatus')) { // Only reconnect if needed
                    console.log('WebSocket closed, reconnecting...', e.reason);
                    setTimeout(() => connectWebSocket(taskId), 5000);
                }
            };

            socket.onerror = (err) => {
                console.error('WebSocket error:', err);
            };
        };

        // Update progress UI with counts
        function updateProgressUI(data) {
            // Progress bar
            const progress = data.progress || 0;
            document.getElementById('progressBar').style.width = `${progress}%`;
            document.getElementById('progressText').textContent = `${progress}%`;
            
            // File and batch counters
            if (data.files_processed !== undefined) {
                document.getElementById('filesProcessed').textContent = data.files_processed;
            }
            if (data.batches_processed !== undefined) {
                document.getElementById('batchesProcessed').textContent = data.batches_processed;
            }
            
            // Current file info
            if (data.current_file) {
                document.getElementById('currentFile').textContent = `Processing: ${data.current_file}`;
            }
            
            if (data.description) {
                document.getElementById('currentStatus').textContent = data.description;
            }
        }

        // Handle parsing completion
        const updateParsingComplete = () => {
            document.getElementById('parsingStatus').textContent = "Status: Ready";
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            document.getElementById('pauseBtn').innerHTML = '<i class="bi bi-pause-circle"></i> Pause';
            fetchProcessedFiles();
        };

        // Fetch processed files
        const fetchProcessedFiles = async () => {
            try {
                const response = await fetch('/api/get-processed-files/');
                const data = await response.json();
                updateFileList(data.files);
            } catch (error) {
                console.error('Error fetching processed files:', error);
            }
        };

        
        // Enhanced file list update with counts
        function updateFileList(files) {
            const fileList = document.getElementById('processedFilesList');
            fileList.innerHTML = '';
            
            // Counters
            let successCount = 0;
            let errorCount = 0;

            files.forEach(file => {
                if (file.status === 'success') successCount++;
                if (file.status === 'error') errorCount++;
                
                const li = document.createElement('li');
                li.className = `list-group-item d-flex justify-content-between align-items-center py-2 
                            ${file.status === 'error' ? 'list-group-item-danger' : 
                                file.status === 'skipped' ? 'list-group-item-warning' : ''}`;
                li.dataset.status = file.status;
                
                li.innerHTML = `
                    <div>
                        <span class="badge ${file.status === 'success' ? 'bg-success' : 
                                        file.status === 'skipped' ? 'bg-warning' : 'bg-danger'} me-2">
                            ${file.status === 'success' ? '<i class="bi bi-check-circle"></i>' :
                            file.status === 'skipped' ? '<i class="bi bi-skip-forward"></i>' : 
                            '<i class="bi bi-exclamation-triangle"></i>'}
                        </span>
                        <span class="file-name">${file.file_name}</span>
                        ${file.schedule ? `<span class="badge bg-info ms-2">${file.schedule}</span>` : ''}
                    </div>
                    <small class="text-muted">${file.export_time}</small>
                `;
                fileList.appendChild(li);
            });

            // Update counters in the UI
            document.getElementById('filesProcessed').textContent = files.length;

            
            // Update filter buttons
            updateFilterButtons(successCount, errorCount, files.length);
        }

        // Update filter buttons with counts
        function updateFilterButtons(success, error, total) {
            const buttons = {
                all: total,
                success: success,
                error: error
            };
            
            document.querySelectorAll('[data-filter]').forEach(btn => {
                const filter = btn.dataset.filter;
                btn.innerHTML = `${filter.charAt(0).toUpperCase() + filter.slice(1)} 
                                <span class="badge bg-dark ms-1">${buttons[filter]}</span>`;
            });
        }

        // Initialize parsing functionality
        const initParsing = () => {
            // File filtering
            document.querySelectorAll('[data-filter]').forEach(btn => {
                btn.addEventListener('click', function() {
                    const filter = this.dataset.filter;
                    document.querySelectorAll('#processedFilesList li').forEach(item => {
                        item.style.display = (filter === 'all' || item.dataset.status === filter) 
                            ? '' 
                            : 'none';
                    });
                    document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                });
            });

            // Start Parsing Button
            document.getElementById('startBtn').addEventListener('click', async function() {
                const scheduleSelect = document.getElementById('scheduleSelect');
                const scheduleId = scheduleSelect ? scheduleSelect.value : '';
                
                try {
                    const url = scheduleId ? 
                        `/api/trigger-parsing/?schedule_id=${scheduleId}` : 
                        '/api/trigger-parsing/';
                    
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }
                    });

                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                    const data = await response.json();
                    
                    if (data.status === 'started') {
                        BaseModule.showToast("Parsing started successfully!", "success");
                        document.getElementById('parsingStatus').textContent = "Status: Parsing in progress";
                        document.getElementById('startBtn').disabled = true;
                        document.getElementById('pauseBtn').disabled = false;
                        connectWebSocket(data.task_id);
                    } else {
                        BaseModule.showToast(data.message || "Failed to start parsing", "error");
                    }
                } catch (error) {
                    BaseModule.showToast("Error: " + error.message, "error");
                    document.getElementById('startBtn').disabled = false;
                }
            });

            // Pause/Resume Button
            document.getElementById('pauseBtn').addEventListener('click', async function() {
                try {
                    const response = await fetch("/api/toggle-parsing/", {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'paused' || data.status === 'resumed') {
                        BaseModule.showToast(`Parsing ${data.status}`, data.status === 'paused' ? 'warning' : 'success');
                        this.innerHTML = data.status === 'paused' 
                            ? '<i class="bi bi-play-circle"></i> Resume' 
                            : '<i class="bi bi-pause-circle"></i> Pause';
                    }
                } catch (error) {
                    BaseModule.showToast("Error: " + error.message, "error");
                }
            });

            // Initial load and check for interrupted tasks
            fetchProcessedFiles();
            fetch('/api/check-interrupted/')
                .then(response => response.json())
                .then(data => {
                    if (data.found) {
                        BaseModule.showToast(`Found interrupted task for file: ${data.last_file}`, 'warning');
                    }
                })
                .catch(error => console.error('Error checking interrupted tasks:', error));
        };

        return {
            init: initParsing
        };
    })();


    // ==================== INITIALIZATION ====================
    // ==================== MODIFIED INITIALIZATION ====================
    document.addEventListener('DOMContentLoaded', () => {
        BaseModule.init();
        ParsingModule.init();
        initFilters();
        
        // Only call fetchProcessedFiles if the required elements exist
        if (document.getElementById('processedFilesList')) {
            fetchProcessedFiles();
            setTimeout(fetchProcessedFiles, 0);
            setInterval(fetchProcessedFiles, 30000);
        }
        
        // Only update widgets if on a page that has them
        if (document.getElementById('widget-data')) {
            updateWidgets();
        }

        // Initialize modules based on current page
        if (document.body.classList.contains('dashboard-page')) {
            initializeProductionChart();
            initializeUtilizationChart();
            initializeMaterialTable();
        }
        
        if (document.getElementById('batchTable') || document.getElementById('processedFilesTable')) {
            DataTablesModule.init();
        }
        
        if (document.getElementById('scheduleTable')) {
            ScheduleListModule.init();
        }
    });
})();

// Main scripts file for LaundryApp

// DOM Ready handler
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    DataTableManager.init();
    FilterManager.init();
    ToastManager.init();
    ExportManager.init();
    UIManager.init();
    
    // Only initialize parsing functionality if the elements exist
    if (document.querySelector('[data-parsing-related]')) {
        ParsingManager.init();
    }
});

// DataTable Manager
const DataTableManager = {
    init: function() {
        // DataTable initialization handled by specific page scripts
        // This is a placeholder for global DataTable configurations
    }
};

// Filter Manager for reports
const FilterManager = {
    init: function() {
        // Date filter buttons
        const applyFilterBtn = document.getElementById('applyFilter');
        if (applyFilterBtn) {
            applyFilterBtn.addEventListener('click', this.applyFilters);
        }
        
        // Initialize date pickers with default values if present
        this.initDatePickers();
    },
    
    initDatePickers: function() {
        const fromDate = document.getElementById('fromDate');
        const toDate = document.getElementById('toDate');
        
        if (fromDate && toDate) {
            // Set default dates (last 7 days) if not already set
            if (!fromDate.value) {
                const lastWeek = new Date();
                lastWeek.setDate(lastWeek.getDate() - 7);
                fromDate.value = lastWeek.toISOString().split('T')[0];
            }
            
            if (!toDate.value) {
                const today = new Date();
                toDate.value = today.toISOString().split('T')[0];
            }
        }
    },
    
    applyFilters: function() {
        // This function is intended to work with client-side filtering
        // Show a notification that filters have been applied
        ToastManager.showToast('Filters applied successfully');
    }
};

// Toast notifications
const ToastManager = {
    init: function() {
        // Bootstrap 5 Toast initialization
        const toastElList = document.querySelectorAll('.toast');
        if (toastElList.length) {
            toastElList.forEach(toastEl => {
                const toast = new bootstrap.Toast(toastEl);
            });
        }
    },
    
    showToast: function(message, type = 'success') {
        const filterToast = document.getElementById('filterToast');
        if (filterToast) {
            const toastBody = document.getElementById('toastBody');
            
            // Construct the message
            let toastMessage = message;
            if (message === 'Filters applied successfully') {
                toastMessage = 'Filters applied: ';
                const fromDate = document.getElementById('fromDate')?.value || '';
                const toDate = document.getElementById('toDate')?.value || '';
                const customer = document.getElementById('customerFilter')?.value || '';
                
                if (fromDate || toDate) {
                    toastMessage += `Date range ${fromDate || ''} to ${toDate || ''}`;
                }
                if (customer) {
                    toastMessage += `${fromDate || toDate ? ' and ' : ''}Customer: ${customer}`;
                }
                toastMessage = toastMessage || 'All filters cleared';
            }
            
            // Set message and styling
            if (toastBody) {
                toastBody.textContent = toastMessage;
                filterToast.classList.remove('bg-danger', 'bg-success');
                filterToast.classList.add(type === 'error' ? 'bg-danger' : 'bg-success');
            }
            
            // Show the toast
            const bsToast = new bootstrap.Toast(filterToast);
            bsToast.show();
        }
    }
};

// Export Manager
const ExportManager = {
    init: function() {
        const exportBtn = document.getElementById('exportCSV');
        if (exportBtn) {
            exportBtn.addEventListener('click', this.exportCSV);
        }
    },
    
    exportCSV: function() {
        // Find the DataTable instance and trigger its export button
        const dataTable = $('#laundryTable').DataTable();
        if (dataTable) {
            dataTable.button('.buttons-csv').trigger();
        }
    }
};

// UI Manager - handles loading overlay and other UI elements
const UIManager = {
    init: function() {
        // Hide loading overlay when page is fully loaded
        window.addEventListener('load', this.hideLoading);
        
        // Initialize other UI components
        this.initSidebar();
    },
    
    showLoading: function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    },
    
    hideLoading: function() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },
    
    initSidebar: function() {
        // AdminLTE sidebar functionality is handled by the AdminLTE JS
    }
};

// Only add ParsingManager if the parsing functionality is needed
// This is the section causing the error
const ParsingManager = {
    init: function() {
        // Add null checks before accessing elements
        const triggerBtn = document.getElementById('trigger-parsing');
        if (triggerBtn) {
            triggerBtn.addEventListener('click', this.triggerParsing);
        }
        
        const toggleBtn = document.getElementById('toggle-parsing');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', this.toggleParsing);
        }
        
        const resumeBtn = document.getElementById('resume-parsing');
        if (resumeBtn) {
            resumeBtn.addEventListener('click', this.resumeParsing);
        }
    },
    
    // Methods for parsing functionality that are safe to include
    // even if the elements don't exist
    triggerParsing: function() {
        console.log('Parsing triggered'); 
    },
    
    toggleParsing: function() {
        console.log('Parsing toggled');
    },
    
    resumeParsing: function() {
        console.log('Parsing resumed');
    }
};
