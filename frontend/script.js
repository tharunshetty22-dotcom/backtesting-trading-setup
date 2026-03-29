// ==================== API CONFIGURATION ====================
const API_BASE_URL = 'http://localhost:5000';

// ==================== DOM ELEMENTS ====================
const backtestForm = document.getElementById('backtestForm');
const strategyCodeInput = document.getElementById('strategyCode');
const symbolSelect = document.getElementById('symbol');
const timeframeSelect = document.getElementById('timeframe');
const startDateInput = document.getElementById('startDate');
const endDateInput = document.getElementById('endDate');
const initialCapitalInput = document.getElementById('initialCapital');
const positionSizeInput = document.getElementById('positionSize');
const runBtn = document.getElementById('runBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultsSection = document.getElementById('resultsSection');
const resultsContent = document.getElementById('resultsContent');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const mt5Status = document.getElementById('mt5Status');
const statusText = document.getElementById('statusText');
const loadSampleBtn = document.getElementById('loadSampleBtn');
const newBacktestBtn = document.getElementById('newBacktestBtn');
const closeErrorBtn = document.getElementById('closeErrorBtn');

// ==================== SAMPLE STRATEGY ====================
const SAMPLE_STRATEGY = `import pandas as pd
import numpy as np

def generate_signals(ohlc_data):
    """
    Simple Moving Average Crossover Strategy
    Buy when short MA > long MA
    Sell when short MA < long MA
    """
    close = ohlc_data['Close'].values
    
    # Calculate moving averages
    sma_short = pd.Series(close).rolling(window=10).mean()
    sma_long = pd.Series(close).rolling(window=20).mean()
    
    signals = []
    for i in range(len(close)):
        if i < 20:  # Need 20 candles minimum
            signals.append(0)  # HOLD
        elif sma_short.iloc[i] > sma_long.iloc[i]:
            signals.append(1)  # BUY signal
        else:
            signals.append(-1)  # SELL signal
    
    return signals`;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    checkMT5Status();
    setDefaultDates();
    loadSymbols();
    attachEventListeners();
});

// ==================== EVENT LISTENERS ====================
function attachEventListeners() {
    backtestForm.addEventListener('submit', runBacktest);
    loadSampleBtn.addEventListener('click', loadSampleStrategy);
    newBacktestBtn.addEventListener('click', resetForm);
    closeErrorBtn.addEventListener('click', hideError);
}

// ==================== MT5 STATUS CHECK ====================
async function checkMT5Status() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/status`);
        const data = await response.json();
        
        if (data.status === 'connected') {
            mt5Status.classList.add('connected');
            statusText.textContent = `✓ MT5 Connected | Balance: $${data.account_balance.toFixed(2)}`;
        } else {
            mt5Status.classList.add('disconnected');
            statusText.textContent = '✗ MT5 Disconnected - Check your config.py';
        }
    } catch (error) {
        mt5Status.classList.add('disconnected');
        statusText.textContent = '✗ Cannot connect to server';
        console.error('Status check error:', error);
    }
}

// ==================== LOAD SYMBOLS ====================
async function loadSymbols() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/symbols`);
        const data = await response.json();
        
        if (data.symbols && data.symbols.length > 0) {
            // Clear existing options
            symbolSelect.innerHTML = '<option value="">-- Select Symbol --</option>';
            
            // Create symbol groups
            const groups = {
                'FOREX': [],
                'CRYPTO': [],
                'METALS': [],
                'INDICES': [],
                'COMMODITIES': [],
                'STOCKS': [],
                'OTHER': []
            };
            
            // Categorize symbols
            data.symbols.forEach(symbol => {
                const upperSymbol = symbol.toUpperCase();
                
                // Categorize based on symbol name
                if (upperSymbol.startsWith('XAU') || upperSymbol.startsWith('XAG') || upperSymbol.startsWith('XPT') || upperSymbol.startsWith('XPD')) {
                    groups['METALS'].push(symbol);
                } else if (upperSymbol.includes('BTC') || upperSymbol.includes('ETH') || upperSymbol.includes('LTC') || upperSymbol.includes('XRP') || upperSymbol.includes('DOGE') || upperSymbol.includes('BCH')) {
                    groups['CRYPTO'].push(symbol);
                } else if (upperSymbol.includes('CASH') || upperSymbol.match(/^(US30|US100|US500|DE40|FR40|GB100|JP225|AU200|ChinaH|SA40|Sing30)/i)) {
                    groups['INDICES'].push(symbol);
                } else if (upperSymbol.includes('OIL') || upperSymbol.includes('GAS') || upperSymbol.includes('WHEAT') || upperSymbol.includes('CORN') || upperSymbol.includes('SOYBEAN') || upperSymbol.includes('SUGAR') || upperSymbol.includes('COCOA') || upperSymbol.includes('COFFEE')) {
                    groups['COMMODITIES'].push(symbol);
                } else if (upperSymbol.length <= 7 && upperSymbol.match(/^[A-Z]{6}$/) && !upperSymbol.includes('CASH')) {
                    groups['FOREX'].push(symbol);
                } else {
                    groups['OTHER'].push(symbol);
                }
            });
            
            // Add grouped options
            Object.keys(groups).forEach(groupName => {
                if (groups[groupName].length > 0) {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = `${groupName} (${groups[groupName].length})`;
                    
                    groups[groupName].sort().forEach(symbol => {
                        const option = document.createElement('option');
                        option.value = symbol;
                        option.textContent = symbol;
                        optgroup.appendChild(option);
                    });
                    
                    symbolSelect.appendChild(optgroup);
                }
            });
            
            console.log(`✅ Loaded ${data.symbols.length} symbols from MT5`);
            console.log(`   FOREX: ${groups['FOREX'].length}`);
            console.log(`   CRYPTO: ${groups['CRYPTO'].length}`);
            console.log(`   METALS: ${groups['METALS'].length}`);
            console.log(`   INDICES: ${groups['INDICES'].length}`);
            console.log(`   COMMODITIES: ${groups['COMMODITIES'].length}`);
            console.log(`   OTHER: ${groups['OTHER'].length}`);
        }
    } catch (error) {
        console.warn('Could not load symbols from MT5:', error);
        // Keep default symbols if API fails
    }
}

// ==================== SET DEFAULT DATES ====================
function setDefaultDates() {
    const today = new Date();
    const lastYear = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    
    // Set end date to today
    endDateInput.valueAsDate = today;
    
    // Set start date to 1 year ago
    startDateInput.valueAsDate = lastYear;
}

// ==================== LOAD SAMPLE STRATEGY ====================
function loadSampleStrategy() {
    strategyCodeInput.value = SAMPLE_STRATEGY;
    strategyCodeInput.focus();
    showNotification('Sample strategy loaded!');
}

// ==================== RUN BACKTEST ====================
async function runBacktest(e) {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
        return;
    }
    
    // Show loading indicator
    loadingIndicator.style.display = 'block';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    runBtn.disabled = true;
    
    try {
        // Prepare request data
        const requestData = {
            strategy_code: strategyCodeInput.value,
            symbol: symbolSelect.value,
            timeframe: timeframeSelect.value,
            start_date: startDateInput.value,
            end_date: endDateInput.value,
            initial_capital: parseFloat(initialCapitalInput.value),
            position_size: parseFloat(positionSizeInput.value)
        };
        
        console.log('Sending backtest request:', requestData);
        
        // Send request
        const response = await fetch(`${API_BASE_URL}/api/backtest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        // Handle response
        if (response.ok) {
            displayResults(data);
        } else {
            showError(data.error || 'Backtest failed');
        }
    } catch (error) {
        showError(`Error: ${error.message}`);
        console.error('Backtest error:', error);
    } finally {
        loadingIndicator.style.display = 'none';
        runBtn.disabled = false;
    }
}

// ==================== VALIDATE FORM ====================
function validateForm() {
    if (!strategyCodeInput.value.trim()) {
        showError('Please enter your strategy code');
        return false;
    }
    
    if (!symbolSelect.value) {
        showError('Please select a symbol');
        return false;
    }
    
    if (!timeframeSelect.value) {
        showError('Please select a timeframe');
        return false;
    }
    
    if (!startDateInput.value || !endDateInput.value) {
        showError('Please select both start and end dates');
        return false;
    }
    
    if (new Date(startDateInput.value) >= new Date(endDateInput.value)) {
        showError('Start date must be before end date');
        return false;
    }
    
    return true;
}

// ==================== DISPLAY RESULTS ====================
function displayResults(data) {
    resultsContent.textContent = formatResults(data);
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// ==================== FORMAT RESULTS ====================
function formatResults(data) {
    return `
====================================================
           BACKTEST RESULTS
====================================================
  Starting capital : $  ${data.starting_capital.toFixed(2)}
  Final value      : $    ${data.final_value.toFixed(2)}
  Net P&L          : $   ${data.net_pnl.toFixed(2)}
  Total return     :    ${data.total_return.toFixed(2)}%
  Total trades     :         ${data.total_trades}
  Won / Lost       : ${data.wins} / ${data.losses}
  Win rate         :      ${data.win_rate.toFixed(1)}%
  Sharpe ratio     :     ${data.sharpe_ratio.toFixed(2)}
  Max drawdown     :    ${data.max_drawdown.toFixed(2)}%
====================================================

  Strategy rating:
  Return  : ${getRating(data.total_return > 15 ? 'good' : 'needs_work')}
  Win rate: ${getRating(data.win_rate > 50 ? 'good' : 'needs_work')}
  Drawdown: ${getRating(data.max_drawdown < 20 ? 'good' : 'too_high')}
  Sharpe  : ${getRating(data.sharpe_ratio > 1 ? 'good' : 'needs_work')}
====================================================`;
}

// ==================== GET RATING ====================
function getRating(rating) {
    const ratings = {
        'good': '✓ Good',
        'needs_work': '✗ Needs work',
        'too_high': '✗ Too high',
        'excellent': '✓✓ Excellent'
    };
    return ratings[rating] || '? Unknown';
}

// ==================== SHOW ERROR ====================
function showError(message) {
    errorMessage.textContent = message;
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// ==================== HIDE ERROR ====================
function hideError() {
    errorSection.style.display = 'none';
}

// ==================== SHOW NOTIFICATION ====================
function showNotification(message) {
    console.log('📢', message);
}

// ==================== RESET FORM ====================
function resetForm() {
    backtestForm.reset();
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    setDefaultDates();
}

// ==================== AUTO-REFRESH MT5 STATUS ====================
// Check MT5 status every 30 seconds
setInterval(checkMT5Status, 30000);