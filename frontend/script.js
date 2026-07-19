/**
 * Frontend JavaScript for SPX WTR Dashboard
 */

const API_BASE = '/api';

// DOM Elements
const metricsDisplay = document.getElementById('metricsDisplay');
const wtrValues = document.getElementById('wtrValues');
const ttrValues = document.getElementById('ttrValues');
const tradeIdeasTable = document.getElementById('tradeIdeasTable');
const refreshBtn = document.getElementById('refreshBtn');
const refreshText = document.getElementById('refreshText');
const refreshSpinner = document.getElementById('refreshSpinner');
const lastRefresh = document.getElementById('lastRefresh');
const upcomingWeekDisplay = document.getElementById('upcomingWeekDisplay');

// State
let wtrData = {};
let ttrData = {};
let prevWtrData = {};
let prevTtrData = {};
let tradeIdeas = [];
let nextWeekStart = null;

/**
 * Fetch latest metrics from API
 */
async function fetchLatestMetrics() {
    try {
        const response = await fetch(`${API_BASE}/latest-metrics`);
        if (!response.ok) throw new Error('Failed to fetch metrics');
        const data = await response.json();
        
        // Store data
        prevWtrData = data.prev_wtr || {};
        prevTtrData = data.prev_ttr || {};
        
        // Display WTR metrics with trend
        displayMetrics('wtr', data.wtr, data.prev_wtr);
        
        // Display TTR metrics with trend
        displayMetrics('ttr', data.ttr, data.prev_ttr);
        
        return data;
    } catch (error) {
        console.error('Error fetching metrics:', error);
        wtrValues.innerHTML = '<p style="color: red;">Error loading metrics</p>';
        ttrValues.innerHTML = '<p style="color: red;">Error loading metrics</p>';
        return null;
    }
}

/**
 * Get trend arrow and color based on current vs previous value
 */
function getTrendArrow(current, previous) {
    if (current === null || current === undefined) {
        return { arrow: '—', color: '#999', title: 'No data' };
    }
    if (previous === null || previous === undefined) {
        return { arrow: '—', color: '#999', title: 'No previous data' };
    }
    
    if (current > previous) {
        return { arrow: '↑', color: '#16a34a', title: `Up from ${previous}%` };
    } else if (current < previous) {
        return { arrow: '↓', color: '#dc2626', title: `Down from ${previous}%` };
    } else {
        return { arrow: '→', color: '#2563eb', title: `Flat at ${previous}%` };
    }
}

/**
 * Display metrics as colored boxes
 */
function displayMetrics(type, metricsData, prevMetricsData = {}) {
    const container = type === 'wtr' ? wtrValues : ttrValues;
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    
    let html = '';
    for (const day of days) {
        const value = metricsData[day];
        const hasValue = value !== null && value !== undefined;
        const displayValue = hasValue ? value : null;
        const prevValue = prevMetricsData ? prevMetricsData[day] : null;
        const color = getMetricColor(displayValue);
        const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);
        
        // Get trend arrow
        const trend = getTrendArrow(displayValue, prevValue);
        
        html += `
            <div class="metric-value">
                <div class="metric-value-label">${dayLabel}</div>
                <div class="metric-value-number" style="color: ${color}">${hasValue ? value + '%' : 'N/A'}</div>
                <div class="metric-value-trend" style="color: ${trend.color};" title="${trend.title}">${trend.arrow}</div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Get color based on percentage
 */
function getMetricColor(percentage) {
    if (percentage === null || percentage === undefined) return '#999';
    if (percentage >= 60) return '#16a34a'; // green - strong signal
    if (percentage >= 50) return '#2563eb'; // blue - moderate signal
    if (percentage >= 40) return '#eab308'; // yellow - weak signal
    return '#ea580c'; // orange - no signal
}

/**
 * Fetch trade ideas from API
 */
async function fetchTradeIdeas() {
    try {
        const response = await fetch(`${API_BASE}/trade-ideas`);
        if (!response.ok) throw new Error('Failed to fetch trade ideas');
        const data = await response.json();
        tradeIdeas = data.trade_ideas || [];
        nextWeekStart = data.next_week_start;
        updateUpcomingWeekDisplay();
        renderTradeIdeasTable();
    } catch (error) {
        console.error('Error fetching trade ideas:', error);
        renderTradeIdeasTable([]);
    }
}

/**
 * Update the upcoming week display with formatted date
 */
function updateUpcomingWeekDisplay() {
    if (nextWeekStart) {
        const date = new Date(nextWeekStart + 'T00:00:00');
        const weekEnd = new Date(date);
        weekEnd.setDate(weekEnd.getDate() + 4); // Friday
        const label = `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
        upcomingWeekDisplay.textContent = label;
    }
}


/**
 * Render trade ideas table
 */
function renderTradeIdeasTable(ideas = null) {
    const tableBody = tradeIdeasTable.querySelector('tbody');
    
    ideas = ideas || tradeIdeas;
    
    if (!ideas || ideas.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 20px;">
                    No trade ideas available for this week
                </td>
            </tr>
        `;
        return;
    }
    
    const rows = ideas.map(idea => {
        const signalClass = idea.signal === 'Go' ? 'signal-go' : 'signal-nogo';
        const signalHtml = `<span class="${signalClass}">${idea.signal}</span>`;
        const reason = idea.reason || '-';
        
        return `
            <tr>
                <td>${idea.day || ''}</td>
                <td>${idea.strategy || ''}</td>
                <td>${idea.entry_time || ''}</td>
                <td>${idea.expiration || ''}</td>
                <td>${idea.credit_target || ''}</td>
                <td>${idea.sma_check || ''}</td>
                <td>${idea.wtr_ttr || ''}</td>
                <td>${signalHtml}</td>
                <td>${reason}</td>
            </tr>
        `;
    }).join('');
    
    tableBody.innerHTML = rows;
}

/**
 * Handle refresh button click
 */
async function handleRefresh() {
    refreshBtn.disabled = true;
    refreshText.style.display = 'none';
    refreshSpinner.style.display = 'inline-block';
    
    try {
        const response = await fetch(`${API_BASE}/refresh`, { method: 'POST' });
        if (!response.ok) throw new Error('Refresh failed');
        
        const result = await response.json();
        
        // Update last refresh timestamp
        const now = new Date();
        lastRefresh.textContent = `Last refreshed: ${now.toLocaleTimeString()}`;
        
        // Reload data
        await fetchLatestMetrics();
        await fetchTradeIdeas();
        
        console.log('Data refreshed successfully:', result);
    } catch (error) {
        console.error('Error during refresh:', error);
        alert('Failed to refresh data. Check console for details.');
    } finally {
        refreshBtn.disabled = false;
        refreshText.style.display = 'inline';
        refreshSpinner.style.display = 'none';
    }
}

/**
 * Event Listeners
 */
refreshBtn.addEventListener('click', handleRefresh);

// TTR History Modal - Get elements
const ttrModal = document.getElementById('ttrModal');
const showTtrBtn = document.getElementById('showTtrBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const closeTtrBtn = document.getElementById('closeTtrBtn');
const ttrTableBody = document.getElementById('ttrTableBody');

let ttrHistoryData = {};

/**
 * Open TTR History Modal
 */
function openTtrModal() {
    ttrModal.classList.add('show');
    loadTtrHistory();
}

/**
 * Close TTR History Modal
 */
function closeTtrModal() {
    ttrModal.classList.remove('show');
}

/**
 * Load TTR History from API (read-only)
 */
async function loadTtrHistory() {
    try {
        const response = await fetch(`${API_BASE}/ttr-history`);
        if (!response.ok) throw new Error('Failed to load TTR history');
        
        ttrHistoryData = await response.json();
        renderTtrTable();
    } catch (error) {
        console.error('Error loading TTR history:', error);
        ttrTableBody.innerHTML = '<tr><td colspan="6" style="color: red; padding: 20px;">Error loading history. Try refreshing.</td></tr>';
    }
}

/**
 * Render TTR History Table (Read-Only)
 */
function renderTtrTable() {
    const weeks = Object.keys(ttrHistoryData).sort().reverse();
    
    if (weeks.length === 0) {
        ttrTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No historical data available</td></tr>';
        return;
    }
    
    let html = '';
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    
    for (const week of weeks) {
        const weekData = ttrHistoryData[week];
        html += `
            <tr>
                <td class="ttr-week-label">${week}</td>
        `;
        
        for (const day of days) {
            const value = weekData[day];
            const displayValue = (value === null || value === undefined) ? 'N/A' : `${value}%`;
            
            html += `
                <td>${displayValue}</td>
            `;
        }
        
        html += '</tr>';
    }
    
    ttrTableBody.innerHTML = html;
}

// Add event listeners to modal buttons
showTtrBtn.addEventListener('click', openTtrModal);
closeModalBtn.addEventListener('click', closeTtrModal);
closeTtrBtn.addEventListener('click', closeTtrModal);

// Close modal when clicking outside
ttrModal.addEventListener('click', (e) => {
    if (e.target === ttrModal) {
        closeTtrModal();
    }
});

// WTR History Modal - Get elements
const wtrModal = document.getElementById('wtrModal');
const showWtrBtn = document.getElementById('showWtrBtn');
const closeWtrModalBtn = document.getElementById('closeWtrModalBtn');
const closeWtrBtn = document.getElementById('closeWtrBtn');
const wtrTableBody = document.getElementById('wtrTableBody');

let wtrHistoryData = {};

function openWtrModal() {
    wtrModal.classList.add('show');
    loadWtrHistory();
}

function closeWtrModal() {
    wtrModal.classList.remove('show');
}

async function loadWtrHistory() {
    try {
        const response = await fetch(`${API_BASE}/wtr-history`);
        if (!response.ok) throw new Error('Failed to load WTR history');

        wtrHistoryData = await response.json();
        renderWtrTable();
    } catch (error) {
        console.error('Error loading WTR history:', error);
        wtrTableBody.innerHTML = '<tr><td colspan="6" style="color: red; padding: 20px;">Error loading history. Try refreshing.</td></tr>';
    }
}

function renderWtrTable() {
    const weeks = Object.keys(wtrHistoryData).sort().reverse();

    if (weeks.length === 0) {
        wtrTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px;">No historical data available</td></tr>';
        return;
    }

    let html = '';
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];

    for (const week of weeks) {
        const weekData = wtrHistoryData[week];
        html += `
            <tr>
                <td class="ttr-week-label">${week}</td>
        `;

        for (const day of days) {
            const value = weekData[day];
            const displayValue = (value === null || value === undefined) ? 'N/A' : `${value}%`;

            html += `
                <td>${displayValue}</td>
            `;
        }

        html += '</tr>';
    }

    wtrTableBody.innerHTML = html;
}

// Add event listeners to WTR modal buttons
showWtrBtn.addEventListener('click', openWtrModal);
closeWtrModalBtn.addEventListener('click', closeWtrModal);
closeWtrBtn.addEventListener('click', closeWtrModal);

// Close modal when clicking outside
wtrModal.addEventListener('click', (e) => {
    if (e.target === wtrModal) {
        closeWtrModal();
    }
});

/**
 * Initialize dashboard on page load
 */
async function init() {
    console.log('Initializing SPX WTR Dashboard...');
    
    // Load initial data
    await fetchLatestMetrics();
    await fetchTradeIdeas();
    
    // Set last refresh time
    const now = new Date();
    lastRefresh.textContent = `Last loaded: ${now.toLocaleTimeString()}`;
    
    console.log('Dashboard ready');
}

// Run on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
