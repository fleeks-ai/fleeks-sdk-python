"""
Comprehensive example usage of the Fleeks Python SDK.

This example demonstrates how to:
1. Create a workspace
2. Execute an agent
3. Watch for file changes
4. Stream terminal output
5. Manage files and containers
"""

import asyncio
import os
from fleeks_sdk import create_client, AgentRole


async def main():
    """Main example function."""
    
    # Set up your API key (alternatively, set FLEEKS_API_KEY environment variable)
    api_key = os.getenv('FLEEKS_API_KEY', 'fleeks_your_api_key_here')
    
    # Create client with context manager for automatic cleanup
    async with create_client(api_key=api_key, base_url='http://localhost:8000') as client:
        
        print("🚀 Fleeks SDK Example")
        print("====================")
        
        # 1. Check API health
        print("\n🏥 Checking API health...")
        health = await client.health_check()
        print(f"✅ API Status: {health.get('status', 'OK')}")
        
        # 2. Create a workspace
        print("\n📁 Creating workspace...")
        workspace = await client.workspaces.create(
            name="example-workspace",
            description="Example workspace for SDK demo",
            programming_language="python",
            framework="fastapi",
            auto_start=True
        )
        print(f"✅ Workspace created: {workspace.id} ({workspace.status})")
        
        # 3. Create and execute an agent
        print("\n🤖 Creating developer agent...")
        agent = await client.agents.create(
            role=AgentRole.DEVELOPER,
            workspace_id=workspace.id,
            task_description="Create a simple FastAPI hello world application with tests",
            auto_approve=False
        )
        print(f"✅ Agent created: {agent.id}")
        
        # 4. Execute the agent
        print("\n⚡ Executing agent...")
        await client.agents.execute(agent.id)
        
        # 5. Stream agent execution (would typically use streaming client)
        print("\n📡 Monitoring agent progress...")
        async for update in client.agents.stream_progress(agent.id):
            print(f"   🤖 {update.get('current_step', 'Working...')}")
            if update.get('status') in ['completed', 'failed']:
                break
        
        # 6. List files created by the agent
        print("\n📄 Files created by agent:")
        files = await client.files.list(workspace.id, recursive=True)
        for file in files:
            if file.type == 'file':
                print(f"   📄 {file.path} ({file.size} bytes)")
        
        # 7. Read a specific file
        if files:
            python_files = [f for f in files if f.path.endswith('.py')]
            if python_files:
                main_file = python_files[0]
                print(f"\n📖 Contents of {main_file.path}:")
                content = await client.files.read(workspace.id, main_file.path)
                lines = content.split('\n')[:10]  # First 10 lines
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2d}: {line}")
                if len(content.split('\n')) > 10:
                    print("       ... (truncated)")
        
        # 8. Execute terminal commands
        print("\n💻 Running commands in workspace...")
        commands = [
            "python --version",
            "pip list | head -5",
            "ls -la"
        ]
        
        for cmd in commands:
            result = await client.terminal.execute(
                workspace_id=workspace.id,
                command=cmd
            )
            print(f"   $ {result.command}")
            print(f"     {result.stdout.strip()}")
        
        # 9. Get container information
        print("\n🐳 Container information:")
        container = await client.containers.get_info(workspace.id)
        print(f"   ID: {container.id}")
        print(f"   Image: {container.image}")
        print(f"   Status: {container.status}")
        
        # 10. Get resource usage
        print("\n📊 Resource usage:")
        stats = await client.containers.get_stats(workspace.id)
        print(f"   CPU: {stats.cpu_usage:.1f}%")
        print(f"   Memory: {stats.memory_usage / 1024 / 1024:.1f} MB / {stats.memory_limit / 1024 / 1024:.1f} MB")
        
        # 11. Create a new file
        print("\n✍️  Creating a new file...")
        new_file = await client.files.write(
            workspace_id=workspace.id,
            file_path="/demo_file.py",
            content="""# Demo file created by SDK
print("Hello from Fleeks SDK!")
print("This file was created programmatically.")

def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("Developer"))
"""
        )
        print(f"✅ Created file: {new_file.path}")
        
        # 12. Execute the new file
        print("\n▶️  Executing the new file...")
        result = await client.terminal.execute(
            workspace_id=workspace.id,
            command="python /demo_file.py"
        )
        print(f"   Output: {result.stdout.strip()}")
        
        # 13. Get usage statistics
        print("\n📈 SDK Usage statistics:")
        usage_stats = await client.get_usage_stats()
        print(f"   Requests this hour: {usage_stats.get('requests_this_hour', 0)}")
        print(f"   Requests today: {usage_stats.get('requests_today', 0)}")
        
        # 14. Clean up
        print(f"\n🧹 Cleaning up workspace {workspace.id}...")
        await client.workspaces.delete(workspace.id)
        print("✅ Workspace deleted")
        
        print("\n🎉 Example completed successfully!")


async def streaming_example():
    """Example demonstrating real-time streaming features."""
    
    api_key = os.getenv('FLEEKS_API_KEY', 'fleeks_your_api_key_here')
    
    async with create_client(api_key=api_key) as client:
        
        print("🔄 Streaming Features Demo")
        print("==========================")
        
        # Create workspace for streaming demo
        workspace = await client.workspaces.create(
            name="streaming-demo",
            description="Demo of real-time streaming features"
        )
        
        print(f"📁 Created workspace: {workspace.id}")
        
        # Start file watching in background
        print("\n👀 Starting file watcher...")
        file_changes = []
        
        async def collect_file_changes():
            async for change in client.streaming.watch_files(
                workspace.id, 
                patterns=['**/*.py', '**/*.txt']
            ):
                file_changes.append(change)
                print(f"   📁 {change.get('event_type')}: {change.get('file_path')}")
                if len(file_changes) >= 5:  # Stop after 5 changes
                    break
        
        # Start the file watcher
        watcher_task = asyncio.create_task(collect_file_changes())
        
        # Create some files to trigger the watcher
        print("\n✍️  Creating files to trigger watcher...")
        
        files_to_create = [
            ("/test1.py", "print('File 1')"),
            ("/test2.py", "print('File 2')"),
            ("/readme.txt", "This is a readme file"),
            ("/test3.py", "print('File 3')"),
            ("/data.txt", "Some data content")
        ]
        
        for file_path, content in files_to_create:
            await asyncio.sleep(0.5)  # Small delay between files
            await client.files.write(
                workspace_id=workspace.id,
                file_path=file_path,
                content=content
            )
        
        # Wait for file watcher to complete
        await watcher_task
        
        print(f"\n✅ Captured {len(file_changes)} file changes")
        
        # Cleanup
        await client.workspaces.delete(workspace.id)
        print("🧹 Cleanup completed")


async def agent_collaboration_example():
    """Example showing agent handoff and collaboration."""
    
    api_key = os.getenv('FLEEKS_API_KEY', 'fleeks_your_api_key_here')
    
    async with create_client(api_key=api_key) as client:
        
        print("🤝 Agent Collaboration Demo")
        print("============================")
        
        # Create workspace
        workspace = await client.workspaces.create(
            name="agent-collab-demo",
            description="Demo of agent collaboration"
        )
        
        # 1. Start with architect agent
        print("\n🏗️  Creating architect agent...")
        architect = await client.agents.create(
            role=AgentRole.ARCHITECT,
            workspace_id=workspace.id,
            task_description="Design a microservices architecture for a task management app"
        )
        
        await client.agents.execute(architect.id)
        print(f"✅ Architect completed design: {architect.id}")
        
        # 2. Handoff to developer agent
        print("\n👨‍💻 Handing off to developer agent...")
        developer = await client.agents.handoff(
            from_agent_id=architect.id,
            to_role=AgentRole.DEVELOPER,
            task_description="Implement the task management API based on the architecture",
            workspace_id=workspace.id
        )
        
        await client.agents.execute(developer.id)
        print(f"✅ Developer completed implementation: {developer.id}")
        
        # 3. Handoff to QA tester
        print("\n🧪 Handing off to QA tester...")
        qa_tester = await client.agents.handoff(
            from_agent_id=developer.id,
            to_role=AgentRole.QA_TESTER,
            task_description="Create comprehensive tests for the task management API",
            workspace_id=workspace.id
        )
        
        await client.agents.execute(qa_tester.id)
        print(f"✅ QA tester completed testing: {qa_tester.id}")
        
        # Show final results
        print("\n📋 Final workspace contents:")
        files = await client.files.list(workspace.id, recursive=True)
        for file in files:
            if file.type == 'file':
                print(f"   📄 {file.path}")
        
        # Cleanup
        await client.workspaces.delete(workspace.id)
        print("\n🧹 Demo completed and cleaned up")


if __name__ == "__main__":
    print("Choose an example to run:")
    print("1. Basic SDK usage")
    print("2. Streaming features")
    print("3. Agent collaboration")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(main())
    elif choice == "2":
        asyncio.run(streaming_example())
    elif choice == "3":
        asyncio.run(agent_collaboration_example())
    else:
        print("Running basic example...")
        asyncio.run(main())