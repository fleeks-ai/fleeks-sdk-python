"""
Preview URL Example - Deploy and Access Your Application

This example demonstrates the new Preview URL feature that provides
instant HTTPS access to your workspace applications with zero configuration.

Features:
- Automatic HTTPS URLs (https://preview.fleeks.ai/{project_id}/)
- WebSocket support (wss://ws.fleeks.ai/{project_id}/)
- SSL certificates (auto-renewing)
- Zero configuration required
"""

import asyncio
from fleeks_sdk import FleeksClient


async def flask_app_example():
    """Example: Deploy and access a Flask application"""
    
    async with FleeksClient(api_key="fleeks_sk_your_api_key") as client:
        print("🚀 Creating Python workspace for Flask app...")
        
        # 1. Create workspace - preview URLs are automatically included!
        workspace = await client.workspaces.create(
            project_id="my-flask-app",
            template="python"
        )
        
        print(f"\n✅ Workspace created!")
        print(f"📦 Container ID: {workspace.container_id}")
        print(f"🌐 Preview URL: {workspace.preview_url}")
        print(f"🔌 WebSocket URL: {workspace.websocket_url}")
        
        # 2. Create a simple Flask app
        flask_code = '''
from flask import Flask, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Hello from Fleeks!",
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
'''
        
        print("\n📝 Creating Flask application...")
        await workspace.files.create("app.py", flask_code)
        
        # 3. Install Flask
        print("📦 Installing Flask...")
        result = await workspace.terminal.execute("pip install flask")
        print(f"   Status: {result.status}")
        
        # 4. Start Flask server in background
        print("🚀 Starting Flask server...")
        job = await workspace.terminal.execute(
            "python app.py",
            background=True
        )
        print(f"   Job ID: {job.job_id}")
        
        # 5. Wait for server to start
        await asyncio.sleep(3)
        
        # 6. Get preview URL (with full details)
        print("\n🌐 Getting preview URL details...")
        preview = await workspace.get_preview_url()
        
        print(f"\n{'='*60}")
        print("🎉 Your Flask app is now live!")
        print(f"{'='*60}")
        print(f"📍 Preview URL: {preview.preview_url}")
        print(f"🔌 WebSocket URL: {preview.websocket_url}")
        print(f"📊 Status: {preview.status}")
        print(f"📦 Container: {preview.container_id}")
        print(f"\n💡 Try these endpoints:")
        print(f"   • Home: {preview.preview_url}")
        print(f"   • Health: {preview.preview_url}health")
        print(f"{'='*60}")
        
        # Keep the workspace running
        print("\n⏳ Server is running. Press Ctrl+C to stop...")
        try:
            await asyncio.sleep(300)  # Keep running for 5 minutes
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
        
        # Cleanup
        await workspace.delete()
        print("✅ Workspace deleted")


async def react_dev_server_example():
    """Example: Run React development server with hot reload"""
    
    async with FleeksClient(api_key="fleeks_sk_your_api_key") as client:
        print("🚀 Creating Node.js workspace for React app...")
        
        # Create workspace with Node.js template
        workspace = await client.workspaces.create(
            project_id="my-react-app",
            template="node"
        )
        
        print(f"\n✅ Workspace created!")
        print(f"🌐 Preview URL: {workspace.preview_url}")
        
        # Clone a React starter project (or use create-react-app)
        print("\n📦 Setting up React project...")
        await workspace.terminal.execute("npx create-react-app my-app")
        
        # Start React dev server (runs on port 3000)
        print("🚀 Starting React dev server...")
        await workspace.terminal.execute(
            "cd my-app && npm start",
            background=True
        )
        
        # Wait for dev server to start
        await asyncio.sleep(10)
        
        # Get preview URL
        preview = await workspace.get_preview_url()
        
        print(f"\n🎉 React app is live at: {preview.preview_url}")
        print(f"🔥 Hot reload is enabled!")
        print(f"📝 Edit files and see changes instantly")


async def websocket_chat_example():
    """Example: WebSocket chat server with real-time communication"""
    
    async with FleeksClient(api_key="fleeks_sk_your_api_key") as client:
        print("🚀 Creating workspace for WebSocket chat...")
        
        workspace = await client.workspaces.create(
            project_id="websocket-chat",
            template="python"
        )
        
        # Create WebSocket server using Flask-SocketIO
        server_code = '''
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected to chat server!'})

@socketio.on('chat_message')
def handle_message(data):
    print(f'Message: {data}')
    emit('message', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)
'''
        
        await workspace.files.create("chat_server.py", server_code)
        
        # Install dependencies
        print("📦 Installing dependencies...")
        await workspace.terminal.execute("pip install flask flask-socketio")
        
        # Start WebSocket server
        print("🚀 Starting WebSocket server...")
        await workspace.terminal.execute(
            "python chat_server.py",
            background=True
        )
        
        await asyncio.sleep(3)
        
        # Get URLs
        preview = await workspace.get_preview_url()
        
        print(f"\n{'='*60}")
        print("🎉 WebSocket Chat Server is live!")
        print(f"{'='*60}")
        print(f"🌐 HTTP URL: {preview.preview_url}")
        print(f"🔌 WebSocket URL: {preview.websocket_url}")
        print(f"\n💡 Connect your client to: {preview.websocket_url}")
        print(f"{'='*60}")


async def multi_service_example():
    """Example: Full-stack app with backend API and frontend"""
    
    async with FleeksClient(api_key="fleeks_sk_your_api_key") as client:
        print("🚀 Creating workspace for full-stack app...")
        
        workspace = await client.workspaces.create(
            project_id="fullstack-app",
            template="python"
        )
        
        # Backend API (Flask)
        backend_code = '''
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/data')
def get_data():
    return jsonify({
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
'''
        
        await workspace.files.create("backend/api.py", backend_code)
        
        # Frontend (simple HTML + JS)
        frontend_code = '''
<!DOCTYPE html>
<html>
<head>
    <title>Full-Stack App</title>
</head>
<body>
    <h1>Users</h1>
    <div id="users"></div>
    <script>
        fetch('/api/data')
            .then(r => r.json())
            .then(data => {
                document.getElementById('users').innerHTML = 
                    data.users.map(u => `<p>${u.name}</p>`).join('');
            });
    </script>
</body>
</html>
'''
        
        await workspace.files.create("frontend/index.html", frontend_code)
        
        # Install dependencies
        print("📦 Installing dependencies...")
        await workspace.terminal.execute("pip install flask flask-cors")
        
        # Start backend
        print("🚀 Starting backend API...")
        await workspace.terminal.execute(
            "cd backend && python api.py",
            background=True
        )
        
        # Start frontend server
        await asyncio.sleep(2)
        await workspace.terminal.execute(
            "cd frontend && python -m http.server 8080",
            background=True
        )
        
        await asyncio.sleep(2)
        
        preview = await workspace.get_preview_url()
        
        print(f"\n{'='*60}")
        print("🎉 Full-Stack App is live!")
        print(f"{'='*60}")
        print(f"🌐 Frontend: {preview.preview_url}")
        print(f"📡 Backend API: {preview.preview_url}api/data")
        print(f"{'='*60}")


async def quick_preview_check():
    """Quick example: Just get preview URL for existing workspace"""
    
    async with FleeksClient(api_key="fleeks_sk_your_api_key") as client:
        # Get existing workspace
        workspace = await client.workspaces.get("my-existing-project")
        
        # Method 1: Use cached preview URL
        print(f"🌐 Cached Preview URL: {workspace.preview_url}")
        print(f"🔌 Cached WebSocket URL: {workspace.websocket_url}")
        
        # Method 2: Get fresh preview URL with full details
        preview = await workspace.get_preview_url()
        print(f"\n📊 Fresh Preview Details:")
        print(f"   URL: {preview.preview_url}")
        print(f"   WebSocket: {preview.websocket_url}")
        print(f"   Status: {preview.status}")
        print(f"   Container: {preview.container_id}")


if __name__ == "__main__":
    # Run any example
    print("🎯 Fleeks Preview URL Examples\n")
    print("Choose an example:")
    print("1. Flask API Server")
    print("2. React Development Server")
    print("3. WebSocket Chat Server")
    print("4. Full-Stack Application")
    print("5. Quick Preview URL Check")
    
    choice = input("\nEnter choice (1-5): ")
    
    examples = {
        "1": flask_app_example,
        "2": react_dev_server_example,
        "3": websocket_chat_example,
        "4": multi_service_example,
        "5": quick_preview_check
    }
    
    example = examples.get(choice)
    if example:
        asyncio.run(example())
    else:
        print("Invalid choice!")
