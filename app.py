#!/usr/bin/env python3
"""
eCourts Scraper - Web Interface (Bonus Feature)
Simple Flask-based web interface for the scraper
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from ecourts_scraper import ECourtsScraper
from datetime import datetime
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eCourts Scraper</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        
        h1 {
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            color: #718096;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            color: #4a5568;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .search-type-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 12px;
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            font-weight: 600;
            color: #4a5568;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .form-section {
            display: none;
        }
        
        .form-section.active {
            display: block;
        }
        
        .checkbox-group {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }
        
        .checkbox-label input[type="checkbox"] {
            width: auto;
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .results {
            margin-top: 30px;
            padding: 20px;
            background: #f7fafc;
            border-radius: 8px;
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .result-header {
            font-size: 20px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .result-item:last-child {
            border-bottom: none;
        }
        
        .result-label {
            font-weight: 600;
            color: #4a5568;
        }
        
        .result-value {
            color: #2d3748;
        }
        
        .success {
            color: #48bb78;
        }
        
        .error {
            color: #f56565;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        .alert-success {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .alert-error {
            background: #fed7d7;
            color: #742a2a;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚖️ eCourts Scraper</h1>
        <p class="subtitle">Search and track court case listings</p>
        
        <form id="searchForm">
            <div class="search-type-tabs">
                <div class="tab active" data-tab="cnr">CNR Search</div>
                <div class="tab" data-tab="case">Case Number Search</div>
            </div>
            
            <!-- CNR Search Form -->
            <div class="form-section active" id="cnr-section">
                <div class="form-group">
                    <label for="cnr">CNR Number</label>
                    <input type="text" id="cnr" name="cnr" placeholder="e.g., DLCT01-123456-2024">
                </div>
            </div>
            
            <!-- Case Number Search Form -->
            <div class="form-section" id="case-section">
                <div class="form-group">
                    <label for="caseType">Case Type</label>
                    <input type="text" id="caseType" name="caseType" placeholder="e.g., CS, CRL, CC">
                </div>
                
                <div class="form-group">
                    <label for="caseNo">Case Number</label>
                    <input type="text" id="caseNo" name="caseNo" placeholder="e.g., 123">
                </div>
                
                <div class="form-group">
                    <label for="caseYear">Case Year</label>
                    <input type="text" id="caseYear" name="caseYear" placeholder="e.g., 2024">
                </div>
            </div>
            
            <!-- Common Fields -->
            <div class="form-group">
                <label for="state">State Code</label>
                <input type="text" id="state" name="state" placeholder="e.g., DL, MH, KA" required>
            </div>
            
            <div class="form-group">
                <label for="dist">District Code (for case number search)</label>
                <input type="text" id="dist" name="dist" placeholder="e.g., 01, 02">
            </div>
            
            <div class="form-group">
                <label>Check Listing</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="radio" name="checkDate" value="today" checked>
                        Today
                    </label>
                    <label class="checkbox-label">
                        <input type="radio" name="checkDate" value="tomorrow">
                        Tomorrow
                    </label>
                </div>
            </div>
            
            <div class="form-group">
                <label>Additional Options</label>
                <div class="checkbox-group">
                    <label class="checkbox-label">
                        <input type="checkbox" name="downloadPdf" id="downloadPdf">
                        Download PDF
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" name="downloadCauseList" id="downloadCauseList">
                        Download Cause List
                    </label>
                </div>
            </div>
            
            <button type="submit" id="submitBtn">Search Case</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Searching eCourts database...</p>
        </div>
        
        <div class="results" id="results"></div>
    </div>
    
    <script>
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));
                
                this.classList.add('active');
                document.getElementById(this.dataset.tab + '-section').classList.add('active');
            });
        });
        
        // Form submission
        document.getElementById('searchForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {};
            
            // Get active tab
            const activeTab = document.querySelector('.tab.active').dataset.tab;
            data.searchType = activeTab;
            
            // Collect form data
            for (let [key, value] of formData.entries()) {
                if (key === 'checkDate' || key === 'downloadPdf' || key === 'downloadCauseList') {
                    data[key] = value;
                } else if (value.trim()) {
                    data[key] = value.trim();
                }
            }
            
            // Show loading
            document.getElementById('loading').classList.add('show');
            document.getElementById('results').classList.remove('show');
            document.getElementById('submitBtn').disabled = true;
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                // Hide loading
                document.getElementById('loading').classList.remove('show');
                document.getElementById('submitBtn').disabled = false;
                
                // Show results
                displayResults(result);
                
            } catch (error) {
                document.getElementById('loading').classList.remove('show');
                document.getElementById('submitBtn').disabled = false;
                displayError('Failed to connect to server: ' + error.message);
            }
        });
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            
            if (data.error) {
                resultsDiv.innerHTML = `
                    <div class="alert alert-error">
                        <strong>Error:</strong> ${data.error}
                    </div>
                `;
            } else {
                let html = '<div class="result-header">Search Results</div>';
                
                if (data.case_info) {
                    html += '<div class="result-item">';
                    html += '<span class="result-label">Case ID:</span>';
                    html += `<span class="result-value">${data.case_info.case_id}</span>`;
                    html += '</div>';
                    
                    html += '<div class="result-item">';
                    html += '<span class="result-label">Found:</span>';
                    html += `<span class="result-value ${data.case_info.found ? 'success' : 'error'}">${data.case_info.found ? '✓ Yes' : '✗ No'}</span>`;
                    html += '</div>';
                    
                    if (data.case_info.court_name) {
                        html += '<div class="result-item">';
                        html += '<span class="result-label">Court:</span>';
                        html += `<span class="result-value">${data.case_info.court_name}</span>`;
                        html += '</div>';
                    }
                    
                    if (data.case_info.serial_number) {
                        html += '<div class="result-item">';
                        html += '<span class="result-label">Serial Number:</span>';
                        html += `<span class="result-value">${data.case_info.serial_number}</span>`;
                        html += '</div>';
                    }
                }
                
                if (data.listing_info) {
                    html += '<div class="result-header" style="margin-top: 20px;">Listing Status</div>';
                    
                    html += '<div class="result-item">';
                    html += '<span class="result-label">Check Date:</span>';
                    html += `<span class="result-value">${data.listing_info.check_date}</span>`;
                    html += '</div>';
                    
                    html += '<div class="result-item">';
                    html += '<span class="result-label">Listed:</span>';
                    html += `<span class="result-value ${data.listing_info.is_listed ? 'success' : 'error'}">${data.listing_info.is_listed ? '✓ Yes' : '✗ No'}</span>`;
                    html += '</div>';
                }
                
                if (data.downloads && data.downloads.length > 0) {
                    html += '<div class="alert alert-success" style="margin-top: 20px;">';
                    html += '<strong>Downloads:</strong><br>';
                    data.downloads.forEach(d => {
                        html += `${d.type}: ${d.file}<br>`;
                    });
                    html += '</div>';
                }
                
                resultsDiv.innerHTML = html;
            }
            
            resultsDiv.classList.add('show');
        }
        
        function displayError(message) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = `
                <div class="alert alert-error">
                    <strong>Error:</strong> ${message}
                </div>
            `;
            resultsDiv.classList.add('show');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Render main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/search', methods=['POST'])
def search():
    """API endpoint for case search"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        scraper = ECourtsScraper()
        
        # Search case
        if data.get('searchType') == 'cnr':
            if not data.get('cnr'):
                return jsonify({'error': 'CNR number is required'}), 400
            
            case_info = scraper.search_by_cnr(
                data.get('state'),
                data.get('cnr')
            )
        else:
            if not all([data.get('caseType'), data.get('caseNo'), data.get('caseYear')]):
                return jsonify({'error': 'Case type, number, and year are required'}), 400
            
            if not data.get('dist'):
                return jsonify({'error': 'District code is required for case number search'}), 400
            
            case_info = scraper.search_by_case_number(
                data.get('state'),
                data.get('dist'),
                data.get('caseType'),
                data.get('caseNo'),
                data.get('caseYear')
            )
        
        if not case_info:
            return jsonify({'error': 'Failed to fetch case information'}), 500
        
        result = {
            'case_info': case_info,
            'downloads': []
        }
        
        # Check listing
        if data.get('checkDate'):
            listing_info = scraper.check_listing(case_info, data.get('checkDate'))
            result['listing_info'] = listing_info
        
        # Download PDF
        if data.get('downloadPdf') and case_info.get('found'):
            pdf_file = scraper.download_case_pdf(case_info['case_id'])
            if pdf_file:
                result['downloads'].append({'type': 'case_pdf', 'file': pdf_file})
        
        # Download cause list
        if data.get('downloadCauseList'):
            if data.get('dist') and data.get('court'):
                causelist_file = scraper.download_cause_list(
                    data.get('state'),
                    data.get('dist'),
                    data.get('court')
                )
                if causelist_file:
                    result['downloads'].append({'type': 'cause_list', 'file': causelist_file})
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download generated files"""
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("eCourts Scraper Web Interface")
    print("=" * 60)
    print("\nStarting server at http://localhost:3000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=3000)