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

// Function to toggle debug info visibility
function toggleDebugInfo() {
    const content = document.getElementById('debug-content');
    const button = document.getElementById('debug-toggle-btn');
    if (content && button) {
        if (content.style.display === 'none' || content.style.display === '') {
            content.style.display = 'block';
            button.textContent = '▲';
        } else {
            content.style.display = 'none';
            button.textContent = '▼';
        }
    }
}

// Helper: Ensure chart divs always exist
function ensureChartDivs() {
    const chartsContainer = document.getElementById('charts-container');
    if (!chartsContainer) {
        console.error("CRITICAL: charts-container not found in ensureChartDivs. Charts cannot be drawn.");
        // Attempt to create charts-container if it's missing (though it should be in the HTML from Python)
        const mainContentArea = document.querySelector('div[style*="flex: 1"]'); // A bit fragile selector
        if (mainContentArea && !document.getElementById('charts-container')) {
            console.warn("charts-container was missing, attempting to create it.");
            const newChartsContainer = document.createElement('div');
            newChartsContainer.id = 'charts-container';
            newChartsContainer.style.padding = "24px 0 24px 0";
            mainContentArea.appendChild(newChartsContainer);
        } else if (!mainContentArea) {
             console.error("Main content area for charts-container also not found.");
        }
    }

    // Re-fetch container in case it was just created
    const currentChartsContainer = document.getElementById('charts-container');
    if (!currentChartsContainer) return; // If still not found, exit

    // Ensure specific chart areas exist
    if (!document.getElementById('overview-charts-area')) {
        const overviewArea = document.createElement('div');
        overviewArea.id = 'overview-charts-area';
        overviewArea.style.margin = "20px 0";
        currentChartsContainer.appendChild(overviewArea);
    }
    // REMOVE comparison-chart creation
    if (!document.getElementById('trends-chart')) {
        const trendsArea = document.createElement('div');
        trendsArea.id = 'trends-chart';
        trendsArea.style.margin = "20px 0";
        currentChartsContainer.appendChild(trendsArea);
    }
    if (!document.getElementById('summary-stats')) {
        const summaryArea = document.createElement('div');
        summaryArea.id = 'summary-stats';
        summaryArea.style.cssText = "margin: 20px 0; padding: 20px; background: var(--bg-secondary); border-radius: 8px; border: 1px solid var(--border-color);";
        currentChartsContainer.appendChild(summaryArea);
    }
     // If the main structure was missing, we might need to re-order or ensure they are in the right place.
    // For simplicity, this assumes charts-container exists and we are just ensuring its children.
    // A more robust way would be to clear charts-container and rebuild if any are missing.
    // For now, let's refine the check:
    if (!document.getElementById('overview-charts-area') ||
        !document.getElementById('trends-chart') ||
        !document.getElementById('summary-stats')) {
        console.log("Recreating chart areas in ensureChartDivs as one or more were missing.");
        currentChartsContainer.innerHTML = `
            <div id="overview-charts-area" style="margin: 20px 0;"></div>
            <div id="trends-chart" style="margin: 20px 0;"></div>
            <div id="summary-stats" style="margin: 20px 0; padding: 20px; background: var(--bg-secondary); border-radius: 8px; border: 1px solid var(--border-color);"></div>
        `;
    }
}

// Update all charts based on selected filters
function updateCharts() {
    console.log("updateCharts called.");
    ensureChartDivs();

    const selectedPeriods = getSelectedPeriods();
    const selectedMetrics = getSelectedMetrics();

    const overviewChartsArea = document.getElementById('overview-charts-area');
    // const comparisonDiv = document.getElementById('comparison-chart'); // REMOVED
    const trendsDiv = document.getElementById('trends-chart');
    const summaryStatsContainer = document.getElementById('summary-stats');

    if (!overviewChartsArea || !trendsDiv || !summaryStatsContainer) { // Adjusted check
        console.error("One or more chart/stats areas are null in updateCharts. Aborting update.");
        return;
    }
    
    overviewChartsArea.innerHTML = ''; // Clear previous overview charts
    // comparisonDiv.innerHTML = ''; // REMOVED
    trendsDiv.innerHTML = '';
    summaryStatsContainer.innerHTML = '';

    if (selectedPeriods.length === 0 || selectedMetrics.length === 0) {
        console.log("No periods or metrics selected. Displaying message.");
        summaryStatsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">Please select at least one time period and one metric to display charts.</p>';
        return;
    }

    const filteredData = data.filter(row => selectedPeriods.includes(row.MonthYear));
    console.log("Filtered data length:", filteredData.length);

    if (filteredData.length === 0) {
        console.log("No data available for selected filters. Displaying message.");
        summaryStatsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">No data available for the selected periods.</p>';
        return;
    }

    console.log("Proceeding to create charts.");
    try {
        // Create individual overview chart for each selected metric
        selectedMetrics.forEach((metric) => {
            const chartId = `overview-chart-${metric.replace(/\s+/g, '-')}`;
            const chartDiv = document.createElement('div');
            chartDiv.id = chartId;
            chartDiv.style.marginBottom = "30px"; // Add space between metric overview charts
            overviewChartsArea.appendChild(chartDiv);
            createSingleMetricOverviewChart(filteredData, metric, chartId);
        });
        
        // createComparisonChart(filteredData, selectedMetrics); // REMOVED
        createTrendsChart(filteredData, selectedMetrics);
        updateSummaryStats(filteredData, selectedMetrics);
    } catch (error) {
        console.error("Error during chart creation process:", error);
        summaryStatsContainer.innerHTML = `<p style="text-align: center; color: red; padding: 40px;">Error generating charts: ${error.message}</p>`;
    }
}

// Renamed and modified from createOverviewChart
// Overview: Line chart for a SINGLE metric, x=MonthYear, y=metric sum per period
function createSingleMetricOverviewChart(filteredData, metric, chartId) {
    console.log(`Attempting to create Overview chart for METRIC: ${metric} on div ID: ${chartId}. Data rows: ${filteredData.length}`);
    const periods = Array.from(new Set(filteredData.map(row => row.MonthYear))).sort();
    
    const yValues = periods.map(period =>
        filteredData
            .filter(row => row.MonthYear === period)
            .reduce((sum, row) => sum + (row[metric] || 0), 0)
    );
    
    const trace = { 
        x: periods, 
        y: yValues, 
        type: 'scatter', 
        mode: 'lines+markers', 
        name: metric, // Name for legend, though only one trace here
        line: { width: 3 }, 
        marker: { size: 8 } 
    };
    console.log(`Overview - Metric: ${metric}, X: [${periods.join(', ')}], Y: [${yValues.join(', ')}]`);

    const themeColors = getThemeColors();
    const layout = {
        title: { text: `Monthly Overview: ${metric}`, font: { color: themeColors.text } }, // Dynamic title
        xaxis: { title: 'Month', color: themeColors.text, gridcolor: themeColors.grid },
        yaxis: { title: 'Value', color: themeColors.text, gridcolor: themeColors.grid },
        height: 350, // Slightly smaller height if multiple charts
        plot_bgcolor: themeColors.background, 
        paper_bgcolor: themeColors.paper, 
        font: { color: themeColors.text }, 
        legend: { font: { color: themeColors.text } }
    };
    Plotly.newPlot(chartId, [trace], layout); // Plot to the specific chartId
    console.log(`Overview chart for ${metric} plotting attempted on ${chartId}.`);
}

// Trends: Line chart, x=Date, y=metric value per day (remains mostly the same)
function createTrendsChart(filteredData, selectedMetrics) {
    console.log(`Attempting to create Trends chart. Data rows: ${filteredData.length}, Metrics: ${selectedMetrics.join(', ')}`);
    const sortedData = [...filteredData].sort((a, b) => a.Date.getTime() - b.Date.getTime());

    const traces = selectedMetrics.map((metric) => {
        const xValues = sortedData.map(row => row.Date);
        const yValues = sortedData.map(row => row[metric] || 0);
        // Log only a sample if data is large
        const xSample = xValues.slice(0,5).map(d => d.toISOString().split('T')[0]).join(', ');
        const ySample = yValues.slice(0,5).join(', ');
        console.log(`Trends - Metric: ${metric}, X (sample): [${xSample}...], Y (sample): [${ySample}...]`);
        return { x: xValues, y: yValues, type: 'scatter', mode: 'lines+markers', name: metric, line: { width: 2 }, marker: { size: 6 } };
    });

    const themeColors = getThemeColors();
    const layout = {
        title: { text: 'Daily Trends', font: { color: themeColors.text } },
        xaxis: { title: 'Date', type: 'date', color: themeColors.text, gridcolor: themeColors.grid },
        yaxis: { title: 'Value', color: themeColors.text, gridcolor: themeColors.grid },
        height: 400, plot_bgcolor: themeColors.background, paper_bgcolor: themeColors.paper, font: { color: themeColors.text }, legend: { font: { color: themeColors.text } }
    };
    Plotly.newPlot('trends-chart', traces, layout);
    console.log("Trends chart plotting attempted.");
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

// Main initialization function with improved error handling
function robustInitializeDashboard(attempt = 0) {
    console.log(`robustInitializeDashboard attempt: ${attempt}`);
    const MAX_PLOTLY_ATTEMPTS = 150; // Increased to 15 seconds (150 * 100ms)
    const MAX_DOM_ATTEMPTS = MAX_PLOTLY_ATTEMPTS + 30; // Allow additional 3 seconds for DOM after Plotly

    // STEP 1: Check if Plotly is loaded
    if (typeof Plotly === 'undefined') {
        if (attempt === 0) { // Log this only on the first attempt for Plotly
            console.warn("Plotly.js is not yet defined. Waiting for it to load from CDN...");
            // Check if the Plotly script tag exists
            const plotlyScriptTag = document.querySelector('script[src*="cdn.plot.ly"]');
            if (!plotlyScriptTag) {
                console.error("CRITICAL: The Plotly.js script tag (<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>) was NOT FOUND in the HTML. This is likely an issue in dashboardgeneration.py or the HTML structure.");
            } else {
                console.log("Plotly.js script tag found in HTML. Waiting for it to execute...");
            }
        }

        if (attempt < MAX_PLOTLY_ATTEMPTS) {
            setTimeout(() => robustInitializeDashboard(attempt + 1), 100);
        } else {
            console.error(`CRITICAL: Plotly.js failed to load after ${MAX_PLOTLY_ATTEMPTS * 100 / 1000} seconds.`);
            const summaryStatsContainer = document.getElementById('summary-stats');
            let errorMessage = `
                <p style="text-align: center; color: red; padding: 20px; border: 1px solid red; background-color: #ffebee;">
                    <strong>Critical Error: Plotly.js library did not load. Charts cannot be displayed.</strong><br><br>
                    This usually means the browser could not download Plotly from its CDN (<code>https://cdn.plot.ly/plotly-latest.min.js</code>).<br><br>
                    <strong>Please try the following:</strong><br>
                    1. Check your internet connection.<br>
                    2. Open your browser's Developer Tools (usually F12), go to the "Network" tab, and refresh the page. Look for <code>plotly-latest.min.js</code>. If it's red or has an error status (like 404, 0, or CORS error), that's the issue.<br>
                    3. Disable browser extensions (especially ad-blockers or privacy tools) and try again.<br>
                    4. Try a different web browser.
                </p>`;
            
            if (summaryStatsContainer) {
                summaryStatsContainer.innerHTML = errorMessage;
            } else if (document.getElementById('charts-container')) {
                document.getElementById('charts-container').innerHTML = errorMessage;
            } else {
                 document.body.innerHTML = `<div style="padding:20px;">${errorMessage}</div>` + (document.body.innerHTML || "");
            }
        }
        return; // Exit and retry for Plotly
    }
    
    if (attempt < MAX_PLOTLY_ATTEMPTS && attempt > 0 && typeof Plotly !== 'undefined') {
      console.log(`Plotly.js successfully loaded after ${attempt * 100 / 1000} seconds.`);
    } else if (attempt === 0 && typeof Plotly !== 'undefined') {
      console.log('Plotly.js was already loaded on first check.');
    }


    // STEP 2: Check for required DOM elements (as before)
    ensureChartDivs(); 

    const requiredElements = [
        'period-checkboxes', 'metric-buttons',
        'charts-container', 
        'overview-charts-area', // CHANGED from 'overview-chart'
        // 'comparison-chart', // REMOVED
        'trends-chart', 'summary-stats', 
        'debug-content' // Keep this for the content div itself
    ];
    const missing = requiredElements.filter(id => !document.getElementById(id));

    if (missing.length > 0) {
        console.log('Missing DOM elements:', missing, `Attempt: ${attempt}`);
        if (attempt < MAX_DOM_ATTEMPTS) { 
            setTimeout(() => robustInitializeDashboard(attempt + 1), 100);
        } else {
            console.error('Failed to find required DOM elements after multiple attempts:', missing);
            const summaryStatsContainer = document.getElementById('summary-stats');
            const domErrorMessage = `<p style="text-align: center; color: red; padding: 40px;">Critical Error: Dashboard DOM elements missing: ${missing.join(', ')}. Cannot initialize.</p>`;
            if (summaryStatsContainer) {
                 summaryStatsContainer.innerHTML = domErrorMessage;
            } else if (document.getElementById('charts-container')) {
                document.getElementById('charts-container').innerHTML = domErrorMessage;
            } else {
                document.body.innerHTML = `<h1>${domErrorMessage}</h1>` + (document.body.innerHTML || "");
            }
        }
        return; // Exit and retry for DOM elements
    }

    console.log('All required DOM elements found for robustInitializeDashboard.');
    updateDebugInfo(); 
    loadTheme();
    initializePeriodSlicer();
    initializeMetricSelector();
    updateCharts(); 
    console.log('Dashboard initialized successfully after a total of', attempt, 'attempts for Plotly/DOM.');
}

// Initial call to start the process
robustInitializeDashboard();

// Fallback: This checks after a longer delay.
// The main robustInitializeDashboard should handle most cases.
// This is a last-ditch effort.
setTimeout(() => {
    const overviewChart = document.getElementById('overview-chart');
    const summaryStats = document.getElementById('summary-stats');
    let isInitialized = false;
    if (overviewChart && overviewChart.querySelector('.plot-container')) { // Check if a Plotly chart is rendered
        isInitialized = true;
    } else if (summaryStats && summaryStats.innerHTML.trim() !== '' && !summaryStats.innerHTML.includes("Loading...")) {
        // If summary stats has content (like a message or actual stats) and it's not the initial loading message
        isInitialized = true;
    }


    if (typeof Plotly !== 'undefined' && !isInitialized) {
        console.warn('Fallback (2000ms): Plotly loaded but dashboard might not be fully initialized. Forcing one more robustInitializeDashboard call.');
        robustInitializeDashboard();
    } else if (typeof Plotly === 'undefined') {
        console.warn('Fallback (2000ms): Plotly still not defined. Forcing one more robustInitializeDashboard call to show error if needed.');
        robustInitializeDashboard(); 
    }
}, 2000); // Increased delay for this final fallback check