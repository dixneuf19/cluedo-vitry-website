#!/usr/bin/env python3
"""
Simple HTTP server for the music blog with login form authentication for admin panel.
Run with: uv run python server.py
Then visit: http://localhost:8000
Admin panel: http://localhost:8000/admin/ (requires password via login form)

Environment variables:
- ADMIN_PASSWORD: Set the admin password (required for admin access)
"""

import http.server
import socketserver
import os
import json
import hashlib
import time
from urllib.parse import urlparse, parse_qs

class BlogHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves the blog files and handles admin routes with form authentication."""
    
    # Simple session storage (in production, use proper session management)
    sessions = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def do_GET(self):
        """Handle GET requests with authentication for admin routes."""
        parsed_path = urlparse(self.path)
        
        # Check if this is an admin route
        if parsed_path.path.startswith('/admin'):
            if parsed_path.path == '/admin/login':
                self.serve_login_page()
                return
            elif parsed_path.path == '/admin/logout':
                self.handle_logout()
                return
            elif not self.is_authenticated():
                self.redirect_to_login()
                return
            
            self.log_message("Admin panel accessed: %s", self.path)
        
        # Handle root directory - serve index.html
        if parsed_path.path == '/':
            self.path = '/index.html'
        
        # Serve the file
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests for login form."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/admin/login':
            self.handle_login()
        else:
            self.send_error(405, "Method not allowed")
    
    def is_authenticated(self):
        """Check if the current request is authenticated."""
        # Get session token from cookies
        cookies = self.parse_cookies()
        session_token = cookies.get('admin_session')
        
        if not session_token:
            return False
        
        # Check if session exists and is valid
        session_data = self.sessions.get(session_token)
        if not session_data:
            return False
        
        # Check if session hasn't expired (24 hours)
        if time.time() - session_data['created'] > 86400:
            del self.sessions[session_token]
            return False
        
        return True
    
    def parse_cookies(self):
        """Parse cookies from the request."""
        cookies = {}
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
        return cookies
    
    def create_session(self):
        """Create a new session and return the token."""
        session_token = hashlib.sha256(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()
        self.sessions[session_token] = {
            'created': time.time(),
            'authenticated': True
        }
        return session_token
    
    def handle_login(self):
        """Handle login form submission."""
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password:
            self.send_error(500, "Admin access requires ADMIN_PASSWORD environment variable to be set")
            return
        
        # Read form data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = parse_qs(post_data)
        
        submitted_password = form_data.get('password', [''])[0]
        
        if submitted_password == admin_password:
            # Create session and set cookie
            session_token = self.create_session()
            
            self.send_response(302)
            self.send_header('Location', '/admin/')
            self.send_header('Set-Cookie', f'admin_session={session_token}; Path=/; HttpOnly; SameSite=Strict')
            self.end_headers()
        else:
            # Redirect back to login with error
            self.send_response(302)
            self.send_header('Location', '/admin/login?error=1')
            self.end_headers()
    
    def handle_logout(self):
        """Handle logout request."""
        cookies = self.parse_cookies()
        session_token = cookies.get('admin_session')
        
        if session_token and session_token in self.sessions:
            del self.sessions[session_token]
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'admin_session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT')
        self.end_headers()
    
    def redirect_to_login(self):
        """Redirect to login page."""
        self.send_response(302)
        self.send_header('Location', '/admin/login')
        self.end_headers()
    
    def serve_login_page(self):
        """Serve the login form page."""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        show_error = 'error' in query_params
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🔐 Connexion Admin - Blog de Sam Marsalis</title>
            <style>
                body {{
                    font-family: 'Georgia', serif;
                    background: linear-gradient(135deg, #1a1a2e, #16213e);
                    color: #f5f5f5;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }}
                .login-container {{
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 15px;
                    padding: 40px;
                    text-align: center;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    max-width: 400px;
                    width: 90%;
                }}
                h1 {{
                    color: #f4d03f;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }}
                .trumpet-emoji {{
                    font-size: 3em;
                    margin-bottom: 20px;
                }}
                .form-group {{
                    margin-bottom: 20px;
                    text-align: left;
                }}
                label {{
                    display: block;
                    margin-bottom: 8px;
                    color: #f5f5f5;
                    font-weight: bold;
                }}
                input[type="password"] {{
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #85c1e9;
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.1);
                    color: #f5f5f5;
                    font-size: 16px;
                    box-sizing: border-box;
                }}
                input[type="password"]:focus {{
                    outline: none;
                    border-color: #f4d03f;
                    background: rgba(255, 255, 255, 0.2);
                }}
                .login-btn {{
                    background: linear-gradient(45deg, #f4d03f, #f7dc6f);
                    color: #1a1a2e;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    width: 100%;
                }}
                .login-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(244, 208, 63, 0.4);
                }}
                .error-message {{
                    background: rgba(231, 76, 60, 0.2);
                    border: 1px solid #e74c3c;
                    color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .back-link {{
                    color: #85c1e9;
                    text-decoration: none;
                    padding: 10px 20px;
                    border: 2px solid #85c1e9;
                    border-radius: 5px;
                    transition: all 0.3s ease;
                    display: inline-block;
                    margin-top: 20px;
                }}
                .back-link:hover {{
                    background-color: #85c1e9;
                    color: #1a1a2e;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="trumpet-emoji">🎺</div>
                <h1>🔐 Administration</h1>
                <p>Accès au panneau d'administration du blog de Sam Marsalis</p>
                
                {'<div class="error-message">❌ Mot de passe incorrect. Veuillez réessayer.</div>' if show_error else ''}
                
                <form method="POST" action="/admin/login">
                    <div class="form-group">
                        <label for="password">Mot de passe :</label>
                        <input type="password" id="password" name="password" required autofocus>
                    </div>
                    <button type="submit" class="login-btn">🔓 Se connecter</button>
                </form>
                
                <a href="/" class="back-link">← Retour au blog</a>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def end_headers(self):
        """Add custom headers."""
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def run_server(port=8000):
    """Start the HTTP server."""
    handler = BlogHTTPRequestHandler
    
    # Check if admin password is configured
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🎺 Blog de Sam Marsalis - Serveur")
            print(f"🌐 Disponible sur: http://localhost:{port}")
            print(f"🔐 Admin: http://localhost:{port}/admin/")
            
            if admin_password:
                print(f"✅ Authentification admin: activée (formulaire)")
                print(f"🔗 Connexion: http://localhost:{port}/admin/login")
            else:
                print(f"⚠️  Authentification admin: DÉSACTIVÉE (définir ADMIN_PASSWORD)")
            
            print(f"📁 Dossier: {os.getcwd()}")
            print(f"⏹️  Arrêt: Ctrl+C")
            print("-" * 60)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} déjà utilisé. Essayez:")
            print(f"   python server.py {port + 1}")
        else:
            print(f"❌ Erreur serveur: {e}")

def main():
    """Main entry point for the blog server."""
    import sys
    
    # Allow custom port via command line argument
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Port invalide. Utilisation du port 8000.")
    
    run_server(port)

if __name__ == "__main__":
    main() 
