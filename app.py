#!/usr/bin/env python3
"""
Opsera Press Release Scraper - Web Frontend
Simple Flask app to view and run the scraper
"""

from flask import Flask, render_template_string, jsonify, request
import json
import os
import subprocess
import threading
from datetime import datetime

app = Flask(__name__)

# Path to scraped data
DATA_FILE = 'scraped_data.json'
scraper_status = {'running': False, 'last_run': None, 'message': ''}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Opsera Press Release Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .header {
            background: linear-gradient(90deg, #5b21b6 0%, #7c3aed 100%);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .logo {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -1px;
        }
        .logo span {
            color: #a78bfa;
        }
        .header-actions {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: #10b981;
            color: white;
        }
        .btn-primary:hover {
            background: #059669;
            transform: translateY(-2px);
        }
        .btn-primary:disabled {
            background: #6b7280;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: white;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .btn-secondary:hover {
            background: rgba(255,255,255,0.2);
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-card h3 {
            color: #a78bfa;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: 700;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-ready { background: #10b981; }
        .status-running { background: #f59e0b; animation: pulse 1s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .table-container {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .table-header {
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .table-header h2 {
            font-size: 18px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        th {
            background: rgba(0,0,0,0.2);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #a78bfa;
        }
        tr:hover {
            background: rgba(255,255,255,0.03);
        }
        .title-cell {
            max-width: 400px;
        }
        .title-cell a {
            color: #fff;
            text-decoration: none;
            font-weight: 500;
        }
        .title-cell a:hover {
            color: #a78bfa;
        }
        .date-cell {
            color: #9ca3af;
            white-space: nowrap;
        }
        .desc-cell {
            color: #9ca3af;
            font-size: 13px;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .category-badge {
            background: rgba(167, 139, 250, 0.2);
            color: #a78bfa;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #9ca3af;
        }
        .empty-state h3 {
            margin-bottom: 10px;
            color: #fff;
        }
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #1f2937;
            padding: 15px 25px;
            border-radius: 8px;
            border-left: 4px solid #10b981;
            display: none;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .search-box {
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.05);
            color: white;
            width: 250px;
        }
        .search-box::placeholder {
            color: #6b7280;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Opsera<span>.</span> Press Tracker</div>
        <div class="header-actions">
            <span id="status">
                <span class="status-indicator status-ready"></span>
                Ready
            </span>
            <button class="btn btn-primary" id="runBtn" onclick="runScraper()">
                Run Scraper
            </button>
            <button class="btn btn-secondary" onclick="refreshData()">
                Refresh
            </button>
        </div>
    </div>

    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Press Releases</h3>
                <div class="value" id="totalCount">-</div>
            </div>
            <div class="stat-card">
                <h3>Latest Release</h3>
                <div class="value" id="latestDate" style="font-size: 18px;">-</div>
            </div>
            <div class="stat-card">
                <h3>Oldest Release</h3>
                <div class="value" id="oldestDate" style="font-size: 18px;">-</div>
            </div>
            <div class="stat-card">
                <h3>Last Scraped</h3>
                <div class="value" id="lastScraped" style="font-size: 18px;">-</div>
            </div>
        </div>

        <div class="table-container">
            <div class="table-header">
                <h2>Press Releases</h2>
                <input type="text" class="search-box" placeholder="Search..." id="searchBox" onkeyup="filterTable()">
            </div>
            <table id="pressTable">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Title</th>
                        <th>Date</th>
                        <th>Category</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        let pressReleases = [];

        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                pressReleases = data.press_releases || [];
                renderTable(pressReleases);
                updateStats(data);
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        function renderTable(data) {
            const tbody = document.getElementById('tableBody');

            if (data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5">
                            <div class="empty-state">
                                <h3>No press releases found</h3>
                                <p>Click "Run Scraper" to fetch press releases from Opsera</p>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = data.map((pr, i) => `
                <tr>
                    <td>${i + 1}</td>
                    <td class="title-cell">
                        <a href="${pr.link}" target="_blank">${pr.title}</a>
                    </td>
                    <td class="date-cell">${formatDate(pr.date)}</td>
                    <td><span class="category-badge">${pr.category || 'Press Release'}</span></td>
                    <td class="desc-cell" title="${pr.description || ''}">${pr.description || '-'}</td>
                </tr>
            `).join('');
        }

        function updateStats(data) {
            document.getElementById('totalCount').textContent = data.press_releases?.length || 0;

            if (data.press_releases?.length > 0) {
                const dates = data.press_releases
                    .map(pr => pr.date)
                    .filter(d => d)
                    .sort();

                if (dates.length > 0) {
                    document.getElementById('latestDate').textContent = formatDate(dates[dates.length - 1]);
                    document.getElementById('oldestDate').textContent = formatDate(dates[0]);
                }
            }

            if (data.last_modified) {
                document.getElementById('lastScraped').textContent = data.last_modified;
            }
        }

        function formatDate(dateStr) {
            if (!dateStr) return '-';
            try {
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });
            } catch {
                return dateStr.split('T')[0] || dateStr;
            }
        }

        function filterTable() {
            const search = document.getElementById('searchBox').value.toLowerCase();
            const filtered = pressReleases.filter(pr =>
                pr.title?.toLowerCase().includes(search) ||
                pr.description?.toLowerCase().includes(search) ||
                pr.date?.includes(search)
            );
            renderTable(filtered);
        }

        async function runScraper() {
            const btn = document.getElementById('runBtn');
            const status = document.getElementById('status');

            btn.disabled = true;
            btn.textContent = 'Running...';
            status.innerHTML = '<span class="status-indicator status-running"></span>Scraping...';

            try {
                const response = await fetch('/api/scrape', { method: 'POST' });
                const result = await response.json();

                showToast(result.message);
                await loadData();
            } catch (error) {
                showToast('Error running scraper: ' + error.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Run Scraper';
                status.innerHTML = '<span class="status-indicator status-ready"></span>Ready';
            }
        }

        function refreshData() {
            loadData();
            showToast('Data refreshed');
        }

        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        }

        // Load data on page load
        loadData();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    """Return the scraped press release data"""
    data = {'press_releases': [], 'last_modified': None}

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data['press_releases'] = json.load(f)

            # Get file modification time
            mtime = os.path.getmtime(DATA_FILE)
            data['last_modified'] = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            print(f"Error loading data: {e}")

    return jsonify(data)

@app.route('/api/scrape', methods=['POST'])
def run_scraper():
    """Run the scraper and return results"""
    global scraper_status

    if scraper_status['running']:
        return jsonify({'success': False, 'message': 'Scraper is already running'})

    scraper_status['running'] = True

    try:
        # Run the test scraper (doesn't require Google credentials)
        result = subprocess.run(
            ['python3', 'test_scraper.py'],
            capture_output=True,
            text=True,
            timeout=300
        )

        scraper_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if result.returncode == 0:
            # Count how many were scraped
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                count = len(data)
                return jsonify({
                    'success': True,
                    'message': f'Successfully scraped {count} press releases!'
                })
            return jsonify({'success': True, 'message': 'Scraper completed'})
        else:
            return jsonify({
                'success': False,
                'message': f'Scraper error: {result.stderr[:200]}'
            })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Scraper timed out'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        scraper_status['running'] = False

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Opsera Press Release Tracker")
    print("="*50)
    print("\nStarting web server...")
    print("Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
