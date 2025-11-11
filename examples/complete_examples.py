"""
Complete examples demonstrating Fleeks SDK usage.

This file contains real-world examples for all SDK features.
"""

import asyncio
from fleeks_sdk import FleeksClient, Config, AgentType


# ============================================================================
# EXAMPLE 1: Basic Workspace Creation
# ============================================================================

async def example_basic_workspace():
    """Create a workspace and execute a simple command."""
    print("\n=== Example 1: Basic Workspace ===")
    
    # Initialize client with API key
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    
    # Create workspace with Python template
    workspace = await client.workspaces.create(
        project_id="my-python-project",
        template="python",
        pinned_versions={"python": "3.11"}
    )
    
    print(f"✓ Workspace created: {workspace.project_id}")
    print(f"  Container ID: {workspace.container_id}")
    print(f"  Languages: {', '.join(workspace.info.languages)}")
    
    # Execute a command
    result = await workspace.terminal.execute("python --version")
    print(f"✓ Python version: {result.stdout.strip()}")
    
    # Clean up
    await workspace.delete()
    print("✓ Workspace deleted")


# ============================================================================
# EXAMPLE 2: File Operations
# ============================================================================

async def example_file_operations():
    """Demonstrate file CRUD operations."""
    print("\n=== Example 2: File Operations ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("file-demo", template="default")
    
    # Create directory
    await workspace.files.mkdir("src/utils")
    print("✓ Created directory: src/utils")
    
    # Create file with content
    file = await workspace.files.create(
        path="src/main.py",
        content="""
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
""".strip()
    )
    print(f"✓ Created file: {file.path} ({file.size_bytes} bytes)")
    
    # Read file
    content = await workspace.files.read("src/main.py")
    print(f"✓ Read file content ({len(content)} chars)")
    
    # Update file
    updated = await workspace.files.update(
        path="src/main.py",
        content=content.replace("World", "Fleeks")
    )
    print(f"✓ Updated file (modified at: {updated.modified_at})")
    
    # List files
    listing = await workspace.files.list(path="/", recursive=True)
    print(f"✓ Found {listing.total_count} files:")
    for f in listing.files:
        print(f"    {f.path} ({f.type})")
    
    # Execute the Python file
    result = await workspace.terminal.execute("python src/main.py")
    print(f"✓ Execution output: {result.stdout.strip()}")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 3: Container Operations
# ============================================================================

async def example_container_operations():
    """Demonstrate container management."""
    print("\n=== Example 3: Container Operations ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("container-demo")
    
    # Get container info
    info = await workspace.containers.get_info()
    print(f"✓ Container: {info.container_id}")
    print(f"  Template: {info.template}")
    print(f"  Languages: {', '.join(info.languages)}")
    print(f"  Status: {info.status}")
    
    # Get real-time stats
    stats = await workspace.containers.get_stats()
    print(f"✓ Resource usage:")
    print(f"  CPU: {stats.cpu_percent}%")
    print(f"  Memory: {stats.memory_mb}MB ({stats.memory_percent}%)")
    print(f"  Processes: {stats.process_count}")
    
    # List processes
    processes = await workspace.containers.get_processes()
    print(f"✓ Running {processes.process_count} processes:")
    for proc in processes.processes[:5]:  # Show first 5
        print(f"  PID {proc.pid}: {proc.command[:50]}")
    
    # Execute command in container
    result = await workspace.containers.exec(
        command="ls -la /workspace",
        working_dir="/workspace"
    )
    print(f"✓ Command executed (exit code: {result.exit_code})")
    print(f"  Output: {result.stdout[:100]}...")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 4: Background Jobs
# ============================================================================

async def example_background_jobs():
    """Demonstrate background job execution."""
    print("\n=== Example 4: Background Jobs ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("jobs-demo", template="node")
    
    # Create a simple server file
    await workspace.files.create(
        path="server.js",
        content="""
const http = require('http');
const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end('Hello from Fleeks!');
});
server.listen(3000, () => {
    console.log('Server running on port 3000');
});
"""
    )
    
    # Start server as background job
    job = await workspace.terminal.start_background_job(
        command="node server.js",
        working_dir="/workspace"
    )
    print(f"✓ Started background job: {job.job_id}")
    print(f"  Command: {job.command}")
    
    # Wait a moment for server to start
    await asyncio.sleep(2)
    
    # Check job status
    status = await workspace.terminal.get_job(job.job_id)
    print(f"✓ Job status: {status.status}")
    
    # Get job output
    output = await workspace.terminal.get_job_output(job.job_id, tail_lines=10)
    print(f"✓ Job output: {output['stdout']}")
    
    # List all jobs
    jobs = await workspace.terminal.list_jobs()
    print(f"✓ Total jobs: {jobs.total_count}")
    
    # Stop the job
    await workspace.terminal.stop_job(job.job_id)
    print("✓ Job stopped")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 5: Agent Execution
# ============================================================================

async def example_agent_execution():
    """Demonstrate AI agent usage."""
    print("\n=== Example 5: Agent Execution ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("agent-demo", template="python")
    
    # Execute code generation agent
    agent = await workspace.agents.execute(
        task="Create a FastAPI REST API with user CRUD endpoints",
        agent_type=AgentType.CODE,
        context={
            "framework": "FastAPI",
            "database": "SQLite",
            "features": ["create", "read", "update", "delete"]
        },
        max_iterations=5
    )
    
    print(f"✓ Agent started: {agent.agent_id}")
    print(f"  Task: {agent.task}")
    print(f"  Status: {agent.status}")
    
    # Monitor agent progress
    print("\n  Monitoring agent progress...")
    while True:
        status = await workspace.agents.get_status(agent.agent_id)
        print(f"  Progress: {status.progress}% - {status.current_step or 'Working...'}")
        
        if not status.is_running:
            break
        
        await asyncio.sleep(2)
    
    # Get agent output
    output = await workspace.agents.get_output(agent.agent_id)
    print(f"\n✓ Agent completed!")
    print(f"  Files created: {len(output.files_created)}")
    print(f"  Files modified: {len(output.files_modified)}")
    print(f"  Commands executed: {len(output.commands_executed)}")
    print(f"  Execution time: {output.execution_time_ms / 1000:.2f}s")
    
    # Show created files
    if output.files_created:
        print("\n  Created files:")
        for file_path in output.files_created:
            print(f"    - {file_path}")
    
    # Show reasoning
    if output.reasoning:
        print("\n  Agent reasoning:")
        for step in output.reasoning[:3]:  # Show first 3 steps
            print(f"    - {step}")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 6: CLI-to-Cloud Handoff
# ============================================================================

async def example_agent_handoff():
    """Demonstrate CLI-to-cloud agent handoff."""
    print("\n=== Example 6: Agent Handoff ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("handoff-demo")
    
    # Simulate CLI context
    local_context = {
        "task": "Refactor authentication module to use JWT",
        "current_file": "auth.py",
        "cursor_position": {"line": 45, "column": 12}
    }
    
    # Workspace snapshot (files to sync)
    workspace_snapshot = {
        "auth.py": "# Current authentication code...",
        "models.py": "# User models...",
        "requirements.txt": "flask\nbcrypt\n"
    }
    
    # Conversation history
    conversation_history = [
        {"role": "user", "content": "Can you help me implement JWT authentication?"},
        {"role": "assistant", "content": "I'll help you add JWT authentication. Let me analyze your current code..."}
    ]
    
    # Perform handoff
    handoff = await workspace.agents.handoff(
        task="Implement JWT authentication with refresh tokens",
        local_context=local_context,
        workspace_snapshot=workspace_snapshot,
        conversation_history=conversation_history
    )
    
    print(f"✓ Handoff successful!")
    print(f"  Agent ID: {handoff.agent_id}")
    print(f"  Handoff ID: {handoff.handoff_id}")
    print(f"  Workspace synced: {handoff.workspace_synced}")
    print(f"  Context preserved: {handoff.context_preserved}")
    
    # Monitor the handed-off agent
    print("\n  Agent is working in the cloud...")
    status = await workspace.agents.get_status(handoff.agent_id)
    print(f"  Status: {status.status}")
    print(f"  Progress: {status.progress}%")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 7: Real-time Streaming
# ============================================================================

async def example_streaming():
    """Demonstrate real-time streaming features."""
    print("\n=== Example 7: Real-time Streaming ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("streaming-demo")
    
    # Connect streaming client
    await client.streaming.connect()
    print("✓ Connected to streaming server")
    
    # Define callbacks
    def on_file_change(event):
        print(f"  File {event['type']}: {event['path']}")
    
    def on_agent_update(event):
        print(f"  Agent: {event.get('message', event.get('type'))}")
    
    def on_terminal_output(data):
        print(f"  Terminal: {data['output']}", end='')
    
    # Start file watching
    await client.streaming.watch_files(
        workspace_id=workspace.project_id,
        callback=on_file_change,
        path="/workspace"
    )
    print("✓ Watching files...")
    
    # Create a file (should trigger file watch)
    await workspace.files.create("test.txt", content="Hello!")
    await asyncio.sleep(1)
    
    # Start agent with streaming
    agent = await workspace.agents.execute(
        task="Create a simple README.md file",
        agent_type=AgentType.CODE
    )
    
    await client.streaming.stream_agent(
        agent_id=agent.agent_id,
        callback=on_agent_update
    )
    print("✓ Streaming agent execution...")
    
    # Wait for agent
    await asyncio.sleep(5)
    
    # Stop streaming
    await client.streaming.unwatch_files(workspace.project_id)
    await client.streaming.disconnect()
    print("✓ Disconnected from streaming")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 8: Multi-language Workspace
# ============================================================================

async def example_multi_language():
    """Demonstrate polyglot workspace with multiple languages."""
    print("\n=== Example 8: Multi-language Workspace ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    
    # Create workspace with specific language versions
    workspace = await client.workspaces.create(
        project_id="polyglot-demo",
        template="default",
        pinned_versions={
            "python": "3.11",
            "node": "20",
            "go": "1.21",
            "rust": "1.75"
        }
    )
    
    print(f"✓ Created polyglot workspace: {workspace.project_id}")
    print(f"  Languages: {', '.join(workspace.info.languages)}")
    
    # Test each language
    languages = [
        ("python", "python --version"),
        ("node", "node --version"),
        ("go", "go version"),
        ("rust", "rustc --version"),
        ("java", "java --version"),
        ("ruby", "ruby --version")
    ]
    
    for lang, command in languages:
        try:
            result = await workspace.terminal.execute(command)
            version = result.stdout.strip().split('\n')[0]
            print(f"  ✓ {lang.capitalize()}: {version}")
        except Exception as e:
            print(f"  ✗ {lang.capitalize()}: Not available")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 9: Error Handling
# ============================================================================

async def example_error_handling():
    """Demonstrate proper error handling."""
    print("\n=== Example 9: Error Handling ===")
    
    from fleeks_sdk.exceptions import (
        FleeksResourceNotFoundError,
        FleeksRateLimitError,
        FleeksTimeoutError
    )
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    workspace = await client.workspaces.create("error-demo")
    
    # Handle file not found
    try:
        content = await workspace.files.read("nonexistent.txt")
    except FleeksResourceNotFoundError as e:
        print(f"✓ Caught expected error: {e}")
    
    # Handle timeout
    try:
        result = await workspace.terminal.execute(
            "sleep 100",
            timeout_seconds=2
        )
    except FleeksTimeoutError as e:
        print(f"✓ Caught timeout: {e}")
    
    # Handle rate limiting (demonstrate retry)
    print("✓ SDK automatically handles rate limiting with retries")
    
    await workspace.delete()


# ============================================================================
# EXAMPLE 10: Advanced Workflow
# ============================================================================

async def example_advanced_workflow():
    """Demonstrate a complete development workflow."""
    print("\n=== Example 10: Advanced Workflow ===")
    
    client = FleeksClient(api_key="fleeks_sk_your_api_key_here")
    
    # 1. Create workspace
    workspace = await client.workspaces.create(
        "full-stack-app",
        template="node"
    )
    print("✓ Workspace created")
    
    # 2. Use agent to scaffold project
    agent = await workspace.agents.execute(
        task="Create a React + Express.js full-stack app with user authentication",
        agent_type=AgentType.CODE,
        context={
            "frontend": "React with TypeScript",
            "backend": "Express.js with JWT",
            "database": "PostgreSQL"
        }
    )
    print("✓ Agent scaffolding project...")
    
    # Wait for agent
    await workspace.agents.wait_for_completion(agent.agent_id, timeout=300)
    output = await workspace.agents.get_output(agent.agent_id)
    print(f"✓ Project scaffolded ({len(output.files_created)} files created)")
    
    # 3. Install dependencies
    print("  Installing dependencies...")
    install_job = await workspace.terminal.start_background_job(
        "npm install",
        working_dir="/workspace"
    )
    await workspace.terminal.wait_for_job(install_job.job_id, timeout=300)
    print("✓ Dependencies installed")
    
    # 4. Run tests
    test_result = await workspace.terminal.execute(
        "npm test",
        timeout_seconds=120
    )
    print(f"✓ Tests {'passed' if test_result.exit_code == 0 else 'failed'}")
    
    # 5. Start dev server
    server_job = await workspace.terminal.start_background_job("npm run dev")
    print(f"✓ Dev server started (Job ID: {server_job.job_id})")
    
    # 6. Monitor health
    health = await workspace.get_health()
    print(f"✓ Workspace health: {health.status}")
    print(f"  Uptime: {health.uptime_seconds}s")
    print(f"  Active agents: {health.agents['active_count']}")
    
    # Keep server running for demo
    print("\n  Server is running. Press Ctrl+C to stop...")
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    await workspace.terminal.stop_job(server_job.job_id)
    await workspace.delete()
    print("✓ Cleaned up")


# ============================================================================
# Run Examples
# ============================================================================

async def run_all_examples():
    """Run all examples."""
    examples = [
        example_basic_workspace,
        example_file_operations,
        example_container_operations,
        example_background_jobs,
        example_agent_execution,
        example_agent_handoff,
        example_streaming,
        example_multi_language,
        example_error_handling,
        example_advanced_workflow,
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"✗ Example failed: {e}")
        print()  # Blank line between examples


if __name__ == "__main__":
    print("=" * 60)
    print("Fleeks SDK - Complete Examples")
    print("=" * 60)
    
    # Run specific example or all
    import sys
    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        example_functions = [
            example_basic_workspace,
            example_file_operations,
            example_container_operations,
            example_background_jobs,
            example_agent_execution,
            example_agent_handoff,
            example_streaming,
            example_multi_language,
            example_error_handling,
            example_advanced_workflow,
        ]
        asyncio.run(example_functions[example_num - 1]())
    else:
        asyncio.run(run_all_examples())
