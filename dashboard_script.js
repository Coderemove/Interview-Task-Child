// Add more detailed logging
console.log('=== Dashboard Script Starting ===');
console.log('Document ready state:', document.readyState);
console.log('Window rawData available:', !!window.rawData);
console.log('Window availablePeriods available:', !!window.availablePeriods);
console.log('Window availableMetrics available:', !!window.availableMetrics);

// Debug function to update debug info
function updateDebugInfo() {
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        debugContent.innerHTML = `
            Raw Data: ${window.rawData ? window.rawData.length + ' records' : 'NOT LOADED'}<br>
            Available Periods: ${window.availablePeriods ? window.availablePeriods.length + ' periods' : 'NOT LOADED'}<br>
            Available Metrics: ${window.availableMetrics ? window.availableMetrics.length + ' metrics' : 'NOT LOADED'}<br>
            Periods: ${window.availablePeriods ? JSON.stringify(window.availablePeriods.slice(0, 3)) + '...' : 'None'}<br>
            Metrics: ${window.availableMetrics ? JSON.stringify(window.availableMetrics.slice(0, 3)) + '...' : 'None'}<br>
            DOM Elements: period-checkboxes=${!!document.getElementById('period-checkboxes')}, metric-buttons=${!!document.getElementById('metric-buttons')}
        `;
    }
}

// Convert string dates back to Date objects and clean the data
const data = (window.rawData && Array.isArray(window.rawData)) ? window.rawData.map(row => {
    // Create a new row object with cleaned data
    const cleanRow = {
        Date: new Date(row.Date + 'T00:00:00'), // Add time to ensure proper parsing
        MonthYear: row.MonthYear
    };
    
    // Clean numeric columns - convert empty strings, null, undefined to 0
    Object.keys(row).forEach(key => {
        if (key !== 'Date' && key !== 'MonthYear') {
            let value = row[key];
            
            // Handle various empty/null cases
            if (value === '' || value === null || value === undefined || isNaN(value)) {
                cleanRow[key] = 0;
            } else {
                // Try to parse as number
                const numValue = parseFloat(value);
                cleanRow[key] = isNaN(numValue) ? 0 : numValue;
            }
        }
    });
    
    return cleanRow;
}) : [];

console.log('Dashboard data processed:', data.length, 'records');
if (data.length > 0) {
    console.log('Sample data row:', data[0]);
}

// Theme management
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    
    const button = document.getElementById('theme-toggle');
    if (button) {
        if (newTheme === 'dark') {
            button.innerHTML = '☀️ Light Mode';
        } else {
            button.innerHTML = '🌙 Dark Mode';
        }
    }
    
    // Save theme preference
    localStorage.setItem('dashboard-theme', newTheme);
    
    // Update charts with new theme
    updateCharts();
}

// Load saved theme
function loadTheme() {
    const savedTheme = localStorage.getItem('dashboard-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const button = document.getElementById('theme-toggle');
    if (button) {
        if (savedTheme === 'dark') {
            button.innerHTML = '☀️ Light Mode';
        } else {
            button.innerHTML = '🌙 Dark Mode';
        }
    }
}

// Get current theme colors for charts
function getThemeColors() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    return {
        background: isDark ? '#1a202c' : '#ffffff',
        paper: isDark ? '#2d3748' : '#ffffff',
        text: isDark ? '#f7fafc' : '#333333',
        grid: isDark ? '#4a5568' : '#e2e8f0'
    };
}

// Initialize period checkboxes
function initializePeriodSlicer() {
    console.log('=== Initializing Period Slicer ===');
    const container = document.getElementById('period-checkboxes');
    if (!container) {
        console.error('Period checkboxes container not found!');
        return;
    }
    
    console.log('Container found:', container);
    container.innerHTML = '';
    
    // Use the periods from window
    let periodsToUse = window.availablePeriods || [];
    console.log('Periods to use from window:', periodsToUse);
    
    // Fallback: get unique periods from actual data if availablePeriods is empty
    if (periodsToUse.length === 0) {
        console.log('No periods from window, generating from data...');
        const periodsSet = new Set();
        data.forEach(row => {
            if (row.MonthYear) {
                periodsSet.add(row.MonthYear);
            }
        });
        periodsToUse = Array.from(periodsSet).sort();
        console.log('Generated periods from data:', periodsToUse);
    }
    
    if (periodsToUse.length === 0) {
        console.error('No periods available!');
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No time periods available</p>';
        return;
    }
    
    console.log('Creating checkboxes for', periodsToUse.length, 'periods');
    
    periodsToUse.forEach((period, index) => {
        console.log(`Creating checkbox ${index + 1}/${periodsToUse.length}: ${period}`);
        
        const div = document.createElement('div');
        div.style.margin = '5px 0';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `period-${period}`;
        checkbox.value = period;
        checkbox.checked = true;
        checkbox.onchange = updateCharts;
        
        const label = document.createElement('label');
        label.htmlFor = `period-${period}`;
        label.textContent = period;
        label.style.marginLeft = '8px';
        label.style.cursor = 'pointer';
        label.style.color = 'var(--text-primary)';
        
        div.appendChild(checkbox);
        div.appendChild(label);
        container.appendChild(div);
    });
    
    console.log('Period slicer initialized successfully with', periodsToUse.length, 'periods');
    console.log('Container now has', container.children.length, 'child elements');
}

// Initialize metric toggle buttons
function initializeMetricSelector() {
    console.log('=== Initializing Metric Selector ===');
    const container = document.getElementById('metric-buttons');
    if (!container) {
        console.error('Metric buttons container not found!');
        return;
    }
    
    console.log('Container found:', container);
    container.innerHTML = '';
    
    // Use the metrics from window
    let metricsToUse = window.availableMetrics || [];
    console.log('Metrics to use from window:', metricsToUse);
    
    // Fallback: get available metrics from actual data if availableMetrics is empty
    if (metricsToUse.length === 0) {
        console.log('No metrics from window, generating from data...');
        metricsToUse = [];
        if (data.length > 0) {
            Object.keys(data[0]).forEach(key => {
                if (key !== 'Date' && key !== 'MonthYear' && typeof data[0][key] === 'number') {
                    metricsToUse.push(key);
                }
            });
        }
        console.log('Generated metrics from data:', metricsToUse);
    }
    
    if (metricsToUse.length === 0) {
        console.error('No metrics available!');
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No metrics available</p>';
        return;
    }
    
    console.log('Creating buttons for', metricsToUse.length, 'metrics');
    
    metricsToUse.forEach((metric, index) => {
        console.log(`Creating button ${index + 1}/${metricsToUse.length}: ${metric}`);
        
        const button = document.createElement('button');
        button.className = 'metric-button';
        button.id = `metric-btn-${metric.replace(/\s+/g, '-')}`;
        button.textContent = metric;
        button.setAttribute('data-metric', metric);
        
        // Default to first 3 metrics active
        if (index < 3) {
            button.classList.add('active');
            console.log(`Button ${metric} set to active`);
        }
        
        button.onclick = function() {
            console.log(`Button clicked: ${metric}, was active: ${button.classList.contains('active')}`);
            button.classList.toggle('active');
            console.log(`Button now active: ${button.classList.contains('active')}`);
            updateCharts();
        };
        
        container.appendChild(button);
    });
    
    console.log('Metric selector initialized successfully with', metricsToUse.length, 'metrics');
    console.log('Container now has', container.children.length, 'child elements');
}

// Get selected periods
function getSelectedPeriods() {
    const checkboxes = document.querySelectorAll('#period-checkboxes input[type="checkbox"]:checked');
    const selected = Array.from(checkboxes).map(cb => cb.value);
    console.log('Selected periods:', selected);
    return selected;
}

// Get selected metrics from toggle buttons
function getSelectedMetrics() {
    const activeButtons = document.querySelectorAll('#metric-buttons .metric-button.active');
    const selected = Array.from(activeButtons).map(btn => btn.getAttribute('data-metric'));
    console.log('Selected metrics:', selected);
    return selected;
}

// Helper: Ensure chart divs always exist
function ensureChartDivs() {
    const chartsContainer = document.getElementById('charts-container');
    if (!chartsContainer) return;
    if (!document.getElementById('overview-chart')) {
        chartsContainer.innerHTML = `
            <div id="overview-chart" style="margin: 20px 0;"></div>
            <div id="comparison-chart" style="margin: 20px 0;"></div>
            <div id="trends-chart" style="margin: 20px 0;"></div>
            <div id="summary-stats" style="margin: 20px 0; padding: 20px; background: var(--bg-secondary); border-radius: 8px; border: 1px solid var(--border-color);"></div>
        `;
    }
}

// Update all charts based on selected filters
function updateCharts() {
    ensureChartDivs();
    const selectedPeriods = getSelectedPeriods();
    const selectedMetrics = getSelectedMetrics();

    const overviewDiv = document.getElementById('overview-chart');
    const comparisonDiv = document.getElementById('comparison-chart');
    const trendsDiv = document.getElementById('trends-chart');
    const summaryStatsContainer = document.getElementById('summary-stats');

    if (!overviewDiv || !comparisonDiv || !trendsDiv || !summaryStatsContainer) return;

    if (selectedPeriods.length === 0 || selectedMetrics.length === 0) {
        overviewDiv.innerHTML = '';
        comparisonDiv.innerHTML = '';
        trendsDiv.innerHTML = '';
        summaryStatsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">Please select at least one time period and one metric to display charts.</p>';
        return;
    }

    const filteredData = data.filter(row => selectedPeriods.includes(row.MonthYear));
    if (filteredData.length === 0) {
        overviewDiv.innerHTML = '';
        comparisonDiv.innerHTML = '';
        trendsDiv.innerHTML = '';
        summaryStatsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">No data available for the selected periods.</p>';
        return;
    }

    // Clear messages
    overviewDiv.innerHTML = '';
    comparisonDiv.innerHTML = '';
    trendsDiv.innerHTML = '';
    summaryStatsContainer.innerHTML = '';

    createOverviewChart(filteredData, selectedMetrics);
    createComparisonChart(filteredData, selectedMetrics);
    createTrendsChart(filteredData, selectedMetrics);
    updateSummaryStats(filteredData, selectedMetrics);
}

// Overview: Line chart, x=MonthYear, y=metric sum per period
function createOverviewChart(filteredData, selectedMetrics) {
    const periods = Array.from(new Set(filteredData.map(row => row.MonthYear))).sort();
    const traces = selectedMetrics.map((metric, idx) => {
        // For each period, sum the metric
        const y = periods.map(period =>
            filteredData
                .filter(row => row.MonthYear === period)
                .reduce((sum, row) => sum + (row[metric] || 0), 0)
        );
        return {
            x: periods,
            y: y,
            type: 'scatter',
            mode: 'lines+markers',
            name: metric,
            line: { width: 3 },
            marker: { size: 8 }
        };
    });

    const themeColors = getThemeColors();
    const layout = {
        title: { text: 'Monthly Metrics Overview', font: { color: themeColors.text } },
        xaxis: { title: 'Month', color: themeColors.text, gridcolor: themeColors.grid },
        yaxis: { title: 'Value', color: themeColors.text, gridcolor: themeColors.grid },
        height: 400,
        plot_bgcolor: themeColors.background,
        paper_bgcolor: themeColors.paper,
        font: { color: themeColors.text }
    };
    Plotly.newPlot('overview-chart', traces, layout);
}

// Trends: Line chart, x=Date, y=metric value per day
function createTrendsChart(filteredData, selectedMetrics) {
    // Get all unique dates in filteredData, sorted
    const dates = Array.from(new Set(filteredData.map(row => row.Date.getTime())))
        .sort((a, b) => a - b)
        .map(ts => new Date(ts));

    const traces = selectedMetrics.map((metric, idx) => {
        // For each date, get the metric value (or 0 if missing)
        const y = dates.map(date => {
            const row = filteredData.find(r => r.Date.getTime() === date.getTime());
            return row ? row[metric] : 0;
        });
        return {
            x: dates,
            y: y,
            type: 'scatter',
            mode: 'lines+markers',
            name: metric,
            line: { width: 2 },
            marker: { size: 6 }
        };
    });

    const themeColors = getThemeColors();
    const layout = {
        title: { text: 'Daily Trends', font: { color: themeColors.text } },
        xaxis: { title: 'Date', color: themeColors.text, gridcolor: themeColors.grid, type: 'date' },
        yaxis: { title: 'Value', color: themeColors.text, gridcolor: themeColors.grid },
        height: 400,
        plot_bgcolor: themeColors.background,
        paper_bgcolor: themeColors.paper,
        font: { color: themeColors.text }
    };
    Plotly.newPlot('trends-chart', traces, layout);
}

// Comparison: Bar chart, x=metric, y=sum over selected periods
function createComparisonChart(filteredData, selectedMetrics) {
    const y = selectedMetrics.map(metric =>
        filteredData.reduce((sum, row) => sum + (row[metric] || 0), 0)
    );
    const trace = {
        x: selectedMetrics,
        y: y,
        type: 'bar'
    };
    const themeColors = getThemeColors();
    const layout = {
        title: { text: 'Metrics Comparison (Selected Periods)', font: { color: themeColors.text } },
        xaxis: { title: 'Metrics', color: themeColors.text, gridcolor: themeColors.grid },
        yaxis: { title: 'Total Count', color: themeColors.text, gridcolor: themeColors.grid },
        height: 400,
        plot_bgcolor: themeColors.background,
        paper_bgcolor: themeColors.paper,
        font: { color: themeColors.text }
    };
    Plotly.newPlot('comparison-chart', [trace], layout);
}

// Update summary statistics
function updateSummaryStats(filteredData, selectedMetrics) {
    console.log('Updating summary stats');
    if (filteredData.length === 0 || selectedMetrics.length === 0) {
        document.getElementById('summary-stats').innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 20px;">No data available for the selected metrics and periods.</p>';
        return;
    }

    let statsHtml = '<h3 style="color: var(--text-primary);">Summary Statistics</h3>';
    
    selectedMetrics.forEach(metric => {
        const values = filteredData.map(row => row[metric] || 0);
        const total = values.reduce((sum, val) => sum + val, 0);
        const average = values.length > 0 ? total / values.length : 0;
        const max = values.length > 0 ? Math.max(...values) : 0;
        const min = values.length > 0 ? Math.min(...values) : 0;
        
        statsHtml += `
            <div style="margin: 20px 0; padding: 15px; background: var(--bg-primary); border-radius: 8px; border: 1px solid var(--border-color);">
                <h4 style="margin: 0 0 15px 0; color: var(--text-secondary);">${metric}</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px;">
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">Total</div>
                        <div style="font-size: 18px; font-weight: bold; color: var(--primary-color);">${total.toLocaleString()}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">Average</div>
                        <div style="font-size: 18px; font-weight: bold; color: var(--success-color);">${average.toFixed(0)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">Maximum</div>
                        <div style="font-size: 18px; font-weight: bold; color: var(--warning-color);">${max.toLocaleString()}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 5px;">Minimum</div>
                        <div style="font-size: 18px; font-weight: bold; color: var(--danger-color);">${min.toLocaleString()}</div>
                    </div>
                </div>
            </div>
        `;
    });
    
    statsHtml += `
        <div style="margin-top: 20px; padding: 15px; background: var(--bg-primary); border-radius: 8px; border: 1px solid var(--border-color);">
            <p style="color: var(--text-primary);"><strong>Selected Time Periods:</strong> ${getSelectedPeriods().length} periods</p>
            <p style="color: var(--text-primary);"><strong>Selected Metrics:</strong> ${selectedMetrics.length} metrics</p>
            <p style="color: var(--text-primary);"><strong>Data Points:</strong> ${filteredData.length} days</p>
        </div>
    `;
    
    document.getElementById('summary-stats').innerHTML = statsHtml;
    console.log('Summary stats updated');
}

// Control functions
function selectAllPeriods() {
    console.log('Selecting all periods');
    document.querySelectorAll('#period-checkboxes input[type="checkbox"]').forEach(cb => {
        cb.checked = true;
    });
    updateCharts();
}

function clearAllPeriods() {
    console.log('Clearing all periods');
    document.querySelectorAll('#period-checkboxes input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    updateCharts();
}

function selectAllMetrics() {
    console.log('Selecting all metrics');
    document.querySelectorAll('#metric-buttons .metric-button').forEach(btn => {
        btn.classList.add('active');
    });
    updateCharts();
}

function clearAllMetrics() {
    console.log('Clearing all metrics');
    document.querySelectorAll('#metric-buttons .metric-button').forEach(btn => {
        btn.classList.remove('active');
    });
    updateCharts();
}

function selectLastWeek() {
    console.log('Selecting last week');
    clearAllPeriods();
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);
    sevenDaysAgo.setHours(0, 0, 0, 0); 
    today.setHours(23, 59, 59, 999); 

    const relevantPeriods = new Set();
    data.forEach(row => { 
        if (row.Date >= sevenDaysAgo && row.Date <= today) {
            relevantPeriods.add(row.MonthYear);
        }
    });
    
    relevantPeriods.forEach(period => {
        const checkbox = document.getElementById(`period-${period}`);
        if (checkbox) checkbox.checked = true;
    });
    updateCharts();
}

function selectLastMonth() {
    console.log('Selecting last month');
    clearAllPeriods();
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    thirtyDaysAgo.setHours(0, 0, 0, 0);
    today.setHours(23, 59, 59, 999);

    const relevantPeriods = new Set();
    data.forEach(row => {
        if (row.Date >= thirtyDaysAgo && row.Date <= today) {
            relevantPeriods.add(row.MonthYear);
        }
    });
    
    relevantPeriods.forEach(period => {
        const checkbox = document.getElementById(`period-${period}`);
        if (checkbox) checkbox.checked = true;
    });
    updateCharts();
}

function selectCurrentMonth() {
    console.log('Selecting current month');
    clearAllPeriods();
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth();

    const relevantPeriods = new Set();
    data.forEach(row => {
        if (row.Date.getFullYear() === currentYear && row.Date.getMonth() === currentMonth) {
            relevantPeriods.add(row.MonthYear);
        }
    });

    if (relevantPeriods.size === 0) {
        // Fallback to most recent period if current month has no data
        const allPeriods = new Set();
        data.forEach(row => allPeriods.add(row.MonthYear));
        const sortedPeriods = Array.from(allPeriods).sort();
        if (sortedPeriods.length > 0) {
            const mostRecentPeriod = sortedPeriods[sortedPeriods.length - 1];
            const checkbox = document.getElementById(`period-${mostRecentPeriod}`);
            if (checkbox) checkbox.checked = true;
        }
    } else {
        relevantPeriods.forEach(period => {
            const checkbox = document.getElementById(`period-${period}`);
            if (checkbox) checkbox.checked = true;
        });
    }
    updateCharts();
}

// Main initialization function with improved error handling
function robustInitializeDashboard(attempt = 0) {
    // Wait for all required DOM elements to exist
    const requiredElements = [
        'period-checkboxes',
        'metric-buttons',
        'charts-container',
        'summary-stats',
        'debug-content'
    ];
    const missing = requiredElements.filter(id => !document.getElementById(id));
    if (missing.length > 0) {
        if (attempt < 30) { // Try for up to ~3 seconds
            setTimeout(() => robustInitializeDashboard(attempt + 1), 100);
        } else {
            console.error('Failed to find required DOM elements after multiple attempts:', missing);
        }
        return;
    }

    // Now safe to initialize everything
    updateDebugInfo();
    loadTheme();
    initializePeriodSlicer();
    initializeMetricSelector();
    ensureChartDivs();
    updateCharts();
    console.log('Dashboard initialized after', attempt, 'attempts');
}

robustInitializeDashboard();

// Additional fallback
setTimeout(() => {
    if (!document.getElementById('period-checkboxes')?.children.length) {
        console.log('Elements still not initialized, trying again...');
        initializeDashboard();
    }
}, 500);

console.log('Period checkboxes:', document.getElementById('period-checkboxes').innerHTML);
console.log('Metric buttons:', document.getElementById('metric-buttons').innerHTML);