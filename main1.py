import os
import json
import requests
from flask import Flask, redirect, request, url_for, session, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # Fixed key for development

# Google OAuth Config
CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID'
CLIENT_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'
CLIENT_ID = 'Angad'
CLIENT_SECRET = 'Angad'
REDIRECT_URI = 'http://localhost:5000/oauth2callback'
AUTH_URI = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URI = 'https://oauth2.googleapis.com/token'
SCOPE = 'openid email profile'

# Notion Config - Replace with your Notion Integration Token
NOTION_TOKEN = 'Angad'  # Get this from https://www.notion.so/my-integrations
NOTION_VERSION = '2022-06-28'

# Notion API Helper Functions
def get_notion_headers():
    return {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': NOTION_VERSION,
        'Content-Type': 'application/json'
    }

def search_notion_pages():
    """Search for all pages accessible to the integration"""
    url = 'https://api.notion.com/v1/search'
    headers = get_notion_headers()
    data = {
        "filter": {
            "property": "object",
            "value": "page"
        },
        "sort": {
            "direction": "descending",
            "timestamp": "last_edited_time"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Notion API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching Notion pages: {e}")
        return None

def get_page_content(page_id):
    """Get the content of a specific Notion page"""
    url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    headers = get_notion_headers()
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Notion API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching page content: {e}")
        return None

@app.route('/')
def index():
    if 'user_info' in session:
        return redirect(url_for('welcome'))
    return redirect(url_for('login'))

@app.route('/welcome')
def welcome():
    if 'user_info' not in session:
        return redirect(url_for('login'))
    
    user = session['user_info']
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
            .welcome-container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .user-info {{ 
                background: #e8f4fd; 
                padding: 20px; 
                border-radius: 5px; 
                margin: 20px 0; 
            }}
            .notion-section {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #000;
            }}
            .btn {{ 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                margin: 10px 10px 10px 0;
                cursor: pointer;
                border: none;
                font-size: 14px;
                transition: background 0.3s;
            }}
            .logout-btn {{ background: #dc3545; }}
            .logout-btn:hover {{ background: #c82333; }}
            .notion-btn {{ background: #000; }}
            .notion-btn:hover {{ background: #333; }}
            .loading {{ display: none; color: #666; }}
            img {{ border-radius: 50%; margin-right: 15px; }}
            #notion-content {{
                margin-top: 20px;
                padding: 20px;
                background: white;
                border-radius: 5px;
                border: 1px solid #ddd;
                display: none;
            }}
            .page-item {{
                padding: 15px;
                border-bottom: 1px solid #eee;
                margin-bottom: 10px;
            }}
            .page-title {{
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            .page-meta {{
                font-size: 12px;
                color: #666;
            }}
        </style>
        <script>
            async function fetchNotionData() {{
                const btn = document.getElementById('notion-btn');
                const loading = document.getElementById('loading');
                const content = document.getElementById('notion-content');
                
                btn.disabled = true;
                btn.textContent = 'Fetching...';
                loading.style.display = 'block';
                content.style.display = 'none';
                
                try {{
                    const response = await fetch('/fetch-notion');
                    const data = await response.json();
                    
                    if (data.success) {{
                        displayNotionData(data.pages);
                        content.style.display = 'block';
                    }} else {{
                        content.innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                        content.style.display = 'block';
                    }}
                }} catch (error) {{
                    content.innerHTML = '<p style="color: red;">Error fetching data: ' + error.message + '</p>';
                    content.style.display = 'block';
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = 'Fetch My Notion Pages';
                    loading.style.display = 'none';
                }}
            }}
            
            function displayNotionData(pages) {{
                const content = document.getElementById('notion-content');
                if (!pages || pages.length === 0) {{
                    content.innerHTML = '<p>No pages found. Make sure you have shared pages with your Notion integration.</p>';
                    return;
                }}
                
                let html = '<h3>Your Notion Pages (' + pages.length + ')</h3>';
                pages.forEach(page => {{
                    const title = page.properties?.title?.title?.[0]?.plain_text || 
                                 page.properties?.Name?.title?.[0]?.plain_text || 
                                 'Untitled';
                    const lastEdited = new Date(page.last_edited_time).toLocaleDateString();
                    
                    html += `
                        <div class="page-item">
                            <div class="page-title">${{title}}</div>
                            <div class="page-meta">
                                Last edited: ${{lastEdited}} | 
                                <a href="#" onclick="viewPageContent('${{page.id}}')">View Content</a>
                            </div>
                        </div>
                    `;
                }});
                content.innerHTML = html;
            }}
            
            async function viewPageContent(pageId) {{
                try {{
                    const response = await fetch(`/page-content/${{pageId}}`);
                    const data = await response.json();
                    
                    if (data.success) {{
                        const newWindow = window.open('', '_blank');
                        newWindow.document.write(`
                            <html>
                                <head><title>Page Content</title></head>
                                <body style="font-family: Arial, sans-serif; padding: 20px;">
                                    <h2>Page Content</h2>
                                    <pre>${{JSON.stringify(data.content, null, 2)}}</pre>
                                </body>
                            </html>
                        `);
                    }} else {{
                        alert('Error loading page content: ' + data.error);
                    }}
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
        </script>
    </head>
    <body>
        <div class="welcome-container">
            <h1>Welcome to Your Dashboard!</h1>
            <div class="user-info">
                <h2>User Information</h2>
                {"<img src='" + user.get('picture', '') + "' width='50' height='50' alt='Profile Picture'>" if user.get('picture') else ""}
                <p><strong>Name:</strong> {user.get('name', 'N/A')}</p>
                <p><strong>Email:</strong> {user.get('email', 'N/A')}</p>
                <p><strong>User ID:</strong> {user.get('sub', 'N/A')}</p>
            </div>
            
            <div class="notion-section">
                <h2>📝 Notion Integration</h2>
                <p>Click the button below to fetch your Notion pages:</p>
                <button id="notion-btn" class="btn notion-btn" onclick="fetchNotionData()">
                    Fetch My Notion Pages
                </button>
                <div id="loading" class="loading">Loading your Notion data...</div>
                <div id="notion-content"></div>
            </div>
            
            <a href="/logout" class="btn logout-btn">Logout</a>
        </div>
    </body>
    </html>
    """

@app.route('/login')
def login():
    # Check if user is already logged in
    if 'user_info' in session:
        print("User already logged in, redirecting to welcome")
        return redirect(url_for('welcome'))
    
    # Show login page
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-container { 
                background: white; 
                padding: 40px; 
                border-radius: 10px; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }
            .login-btn { 
                background: #4285f4; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block;
                margin-top: 20px;
                font-size: 16px;
                transition: background 0.3s;
            }
            .login-btn:hover { background: #3367d6; }
            h1 { color: #333; margin-bottom: 10px; }
            p { color: #666; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Welcome</h1>
            <p>Please sign in to continue to your dashboard</p>
            <a href="/auth/google" class="login-btn">Sign in with Google</a>
        </div>
    </body>
    </html>
    """

@app.route('/auth/google')
def auth_google():
    # Generate state and redirect to Google OAuth
    state = os.urandom(16).hex()
    session['state'] = state
    print(f"Generated new state for login: {state}")
    auth_url = (
        f"{AUTH_URI}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPE}"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    print(f"Redirecting to Google OAuth: {auth_url[:100]}...")
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    try:
        print(f"OAuth callback received with args: {request.args}")
        
        # Check state parameter to prevent CSRF
        state = request.args.get('state')
        session_state = session.get('state')
        print(f"State from request: {state}")
        print(f"State from session: {session_state}")
        
        if state != session_state:
            print("State mismatch error")
            print(f"This might be due to:")
            print(f"1. Browser cached an old OAuth redirect")
            print(f"2. Session expired or was cleared")
            print(f"3. Multiple browser tabs/windows")
            print(f"Clearing session and redirecting to login...")
            session.clear()
            return redirect(url_for('login'))

        code = request.args.get('code')
        if not code:
            print("No code provided error")
            return "No code provided", 400

        print(f"Authorization code received: {code[:50]}...")

        # Exchange code for tokens
        data = {
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
        print(f"Exchanging code for tokens...")
        print(f"Data being sent: {data}")
        
        token_response = requests.post(TOKEN_URI, data=data)
        print(f"Token response status: {token_response.status_code}")
        print(f"Token response content: {token_response.text}")
        
        if token_response.status_code != 200:
            print(f"Token exchange failed: {token_response.text}")
            return f"Failed to get token: {token_response.text}", 400
        
        tokens = token_response.json()
        print(f"Tokens received: {list(tokens.keys())}")

        # Verify ID token
        try:
            print("Verifying ID token...")
            idinfo = id_token.verify_oauth2_token(
                tokens['id_token'], google_requests.Request(), CLIENT_ID,
                clock_skew_in_seconds=60
            )
            print(f"ID token verified successfully: {idinfo}")
        except ValueError as e:
            print(f"ID token verification failed: {e}")
            return f"Invalid ID token: {e}", 400

        # Store user info in session
        session['user_info'] = {
            'sub': idinfo['sub'],
            'email': idinfo.get('email'),
            'name': idinfo.get('name'),
            'picture': idinfo.get('picture'),
        }
        # Clear the state since authentication is complete
        session.pop('state', None)
        print(f"Authentication successful for user: {idinfo.get('name')} ({idinfo.get('email')})")
        return redirect(url_for('welcome'))
    except Exception as e:
        print(f"Unexpected error in oauth callback: {e}")
        return f"Internal error: {e}", 500

@app.route('/fetch-notion')
def fetch_notion():
    """API endpoint to fetch Notion pages"""
    if 'user_info' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    if NOTION_TOKEN == 'YOUR_NOTION_INTEGRATION_TOKEN':
        return jsonify({
            'success': False, 
            'error': 'Notion integration token not configured. Please set NOTION_TOKEN in main.py'
        })
    
    pages_data = search_notion_pages()
    if pages_data:
        return jsonify({
            'success': True, 
            'pages': pages_data.get('results', []),
            'total': len(pages_data.get('results', []))
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch Notion pages. Check your integration token and permissions.'
        })

@app.route('/page-content/<page_id>')
def page_content(page_id):
    """API endpoint to fetch content of a specific Notion page"""
    if 'user_info' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    if NOTION_TOKEN == 'YOUR_NOTION_INTEGRATION_TOKEN':
        return jsonify({
            'success': False, 
            'error': 'Notion integration token not configured'
        })
    
    content_data = get_page_content(page_id)
    if content_data:
        return jsonify({
            'success': True, 
            'content': content_data
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Failed to fetch page content'
        })

@app.route('/logout')
def logout():
    session.clear()
    print("User logged out successfully")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
# Ensure the environment variables are set before running the app
