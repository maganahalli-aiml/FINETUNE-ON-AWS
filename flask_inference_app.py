#!/usr/bin/env python3
"""
Simple Flask Web Interface for LLM Inference API
Alternative to Streamlit that works with Python 3.14
"""
import os
import json
from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

# Load environment variables
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

# HTML template embedded in Python (to avoid file dependencies)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LLM Inference App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        textarea { width: 100%; height: 150px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; }
        button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        .response { margin-top: 20px; padding: 15px; border-radius: 5px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .loading { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 LLM Inference Application</h1>
        <form id="inferenceForm">
            <p><strong>Enter your prompt:</strong></p>
            <textarea id="prompt" name="prompt" placeholder="Type your question or prompt here..."></textarea>
            <br><br>
            <button type="submit">Generate Response</button>
        </form>
        
        <div id="response"></div>
    </div>

    <script>
        document.getElementById('inferenceForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const prompt = document.getElementById('prompt').value.trim();
            const responseDiv = document.getElementById('response');
            
            if (!prompt) {
                responseDiv.innerHTML = '<div class="error">Please enter a prompt!</div>';
                return;
            }
            
            responseDiv.innerHTML = '<div class="loading">🔄 Calling LLM API...</div>';
            
            try {
                const response = await fetch('/api/inference', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({prompt: prompt})
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    responseDiv.innerHTML = `
                        <div class="success">
                            <h3>✅ Model Response:</h3>
                            <p><strong>${result.result}</strong></p>
                            <small>Status: ${result.status} | Response time: ${result.response_time}</small>
                        </div>
                    `;
                } else {
                    responseDiv.innerHTML = `
                        <div class="error">
                            <h3>❌ Error:</h3>
                            <p>${result.error}</p>
                            <small>Status: ${result.status_code}</small>
                        </div>
                    `;
                }
            } catch (error) {
                responseDiv.innerHTML = `
                    <div class="error">
                        <h3>❌ Network Error:</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with the inference interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/inference', methods=['POST'])
def inference():
    """API endpoint to handle LLM inference requests"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({
                'error': 'No prompt provided',
                'status_code': 400
            }), 400
        
        if not API_URL:
            return jsonify({
                'error': 'API_URL not configured',
                'status_code': 500
            }), 500
        
        # Prepare the request
        payload = {"inputs": prompt}
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key if available
        if API_KEY:
            headers["x-api-key"] = API_KEY
        
        # Make the request to the LLM API
        import time
        start_time = time.time()
        
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        
        response_time = f"{time.time() - start_time:.2f}s"
        
        if response.status_code == 200:
            result_data = response.json()
            return jsonify({
                'result': result_data.get('result', str(result_data)),
                'status': 'success',
                'response_time': response_time,
                'status_code': response.status_code
            })
        else:
            return jsonify({
                'error': f"API returned {response.status_code}: {response.text}",
                'status_code': response.status_code,
                'response_time': response_time
            }), response.status_code
            
    except requests.RequestException as e:
        return jsonify({
            'error': f"Request failed: {str(e)}",
            'status_code': 500
        }), 500
    except Exception as e:
        return jsonify({
            'error': f"Unexpected error: {str(e)}",
            'status_code': 500
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'api_url_configured': bool(API_URL),
        'api_key_configured': bool(API_KEY)
    })

if __name__ == '__main__':
    print("🚀 Starting LLM Inference Web App...")
    print(f"📡 API URL: {API_URL or 'Not configured'}")
    print(f"🔑 API Key: {'Configured' if API_KEY else 'Not configured'}")
    print("🌐 Open your browser to: http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)