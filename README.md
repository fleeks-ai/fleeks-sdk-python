<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/fleeks-ai/fleeks-sdk-python/main/assets/fleeks-logo.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/fleeks-ai/fleeks-sdk-python/main/assets/fleeks-logo.png">
    <img alt="Fleeks Logo" src="https://raw.githubusercontent.com/fleeks-ai/fleeks-sdk-python/main/assets/fleeks-logo.png" width="600"/>
  </picture>
  
  # Fleeks Python SDK
  
  **Production-ready Python SDK for the Fleeks AI Development Platform**
  
  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
  [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
  [![GitHub Stars](https://img.shields.io/github/stars/fleeks-ai/fleeks-sdk-python?style=social)](https://github.com/fleeks-ai/fleeks-sdk-python)
  
  [Documentation](https://docs.fleeks.ai) | [Website](https://fleeks.ai) | [API Reference](https://api.fleeks.ai/docs)
  
</div>

---

Fleeks is a revolutionary AI-powered development platform that provides instant polyglot workspaces with 11+ languages, AI agents, and complete development environments.

## ✨ Key Features

- 🏃 **Sub-Second Workspaces** - Create complete dev environments in <200ms
- 🌐 **11+ Languages** - Python, Node, Go, Rust, Java, Ruby, PHP, and more
- 🤖 **AI Agents** - Code generation, debugging, testing, research
- 📁 **Full File System** - Complete CRUD operations with safety features
- 💻 **Terminal Control** - Sync/async command execution, background jobs
- 📦 **Container Management** - Real-time stats, process control
- 🔄 **Real-time Streaming** - WebSocket file watching and agent streaming
- ⚡ **Async/Await** - Built for high performance
- 🔐 **Enterprise Security** - API key auth with scopes

## 📦 Installation

```bash
pip install fleeks-sdk
```

## 🚀 Quick Start

```python
import asyncio
from fleeks_sdk import FleeksClient

async def main():
    # Initialize client
    client = FleeksClient(api_key="fleeks_sk_your_key_here")
    
    # Create workspace with Python
    workspace = await client.workspaces.create(
        project_id="my-project",
        template="python"
    )
    
    # Execute command
    result = await workspace.terminal.execute("python --version")
    print(result.stdout)  # Python 3.11.5
    
    # Create and run file
    await workspace.files.create(
        path="hello.py",
        content="print('Hello from Fleeks!')"
    )
    result = await workspace.terminal.execute("python hello.py")
    print(result.stdout)  # Hello from Fleeks!
    
    # Use AI agent
    agent = await workspace.agents.execute(
        task="Add unit tests",
        agent_type="test"
    )
    await workspace.agents.wait_for_completion(agent.agent_id)
    
    # Cleanup
    await workspace.delete()

asyncio.run(main())
```

## 📖 Core Features

### Workspaces

```python
# Create with specific languages
workspace = await client.workspaces.create(
    "my-app",
    template="python",
    pinned_versions={"python": "3.11", "node": "20"}
)

# Check health
health = await workspace.get_health()
print(f"Status: {health.status}, Uptime: {health.uptime_seconds}s")
```

### Files

```python
# Create, read, update, delete
await workspace.files.create("src/main.py", content="...")
content = await workspace.files.read("src/main.py")
await workspace.files.update("src/main.py", content="...")
await workspace.files.delete("src/main.py")

# Directories
await workspace.files.mkdir("src/utils")
listing = await workspace.files.list("/", recursive=True)
```

### Terminal

```python
# Sync execution
result = await workspace.terminal.execute("npm test")

# Background jobs
job = await workspace.terminal.start_background_job("npm run dev")
await workspace.terminal.wait_for_job(job.job_id)
```

### AI Agents

```python
# Execute agent task
agent = await workspace.agents.execute(
    task="Create REST API with auth",
    agent_type="code",
    context={"framework": "FastAPI"}
)

# Monitor progress
status = await workspace.agents.get_status(agent.agent_id)
print(f"Progress: {status.progress}%")

# Get results
output = await workspace.agents.get_output(agent.agent_id)
print(f"Files created: {len(output.files_created)}")
```

## 📚 Documentation

- **Full Documentation**: See [`SDK_IMPLEMENTATION_PLAN_VERIFIED.md`](SDK_IMPLEMENTATION_PLAN_VERIFIED.md)
- **Examples**: Check [`examples/complete_examples.py`](examples/complete_examples.py)
- **API Reference**: All modules are fully documented with docstrings

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black fleeks_sdk tests
isort fleeks_sdk tests
```

### Type Checking

```bash
mypy fleeks_sdk
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Support

For support, email support@fleeks.com or create an issue on GitHub.