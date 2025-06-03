"""
TORIS AI - Tool and Model Selection
Implements optimal open-source components based on security audit
"""
# Tool and Model Selection for TORIS AI

## LLM Models

| Model | Size | RAM Required | Performance | Use Case |
|-------|------|--------------|-------------|----------|
| Llama 3 8B | 5GB | 8GB+ | Good general performance | Default model for most tasks |
| Qwen 7B | 4GB | 6GB+ | Fast, efficient | Lightweight alternative for resource-constrained systems |
| Mistral 7B | 4GB | 6GB+ | Strong reasoning | Complex planning tasks |
| CodeLlama 7B | 4GB | 6GB+ | Code-focused | Programming and development tasks |
| Llama 3 70B (quantized) | 20GB | 24GB+ | High performance | Optional for high-end systems |

## Vector Database

| Component | Description | Benefits |
|-----------|-------------|----------|
| ChromaDB | Local vector database | - Efficient memory storage<br>- No external dependencies<br>- Persistent storage<br>- Semantic search capabilities |

## Code Execution

| Component | Description | Security Features |
|-----------|-------------|------------------|
| Docker Sandbox | Containerized code execution | - Resource limits (memory, CPU)<br>- Network isolation<br>- Process limits<br>- Execution timeouts |
| Open Interpreter | Code interpretation framework | - Safe mode execution<br>- Structured output parsing<br>- Multi-language support |

## Tool Framework

| Component | Description | Benefits |
|-----------|-------------|----------|
| Pydantic Models | Structured tool definitions | - Type validation<br>- Schema enforcement<br>- Documentation generation |
| Tool Registry | Centralized tool management | - Dynamic tool discovery<br>- Permission management<br>- Execution logging |

## API and Backend

| Component | Description | Security Features |
|-----------|-------------|------------------|
| FastAPI | Modern async API framework | - OpenAPI documentation<br>- Dependency injection<br>- Authentication middleware |
| HTTPX | Async HTTP client | - Connection pooling<br>- Timeout management<br>- Retry capabilities |
| Slowapi | Rate limiting | - Request throttling<br>- Abuse prevention |

## UI Framework

| Component | Description | Benefits |
|-----------|-------------|----------|
| Gradio | Python-based UI framework | - Rapid development<br>- WebSocket support<br>- Responsive design |
| Custom CSS | Tailored styling | - Matches reference design<br>- Dark mode support<br>- Consistent branding |

## Deployment

| Component | Description | Benefits |
|-----------|-------------|----------|
| Docker Compose | Multi-container orchestration | - Service isolation<br>- Volume management<br>- Health checks |
| GitHub Actions | CI/CD automation | - Automated testing<br>- Security scanning<br>- Container publishing |

## Security Components

| Component | Description | Benefits |
|-----------|-------------|----------|
| Bearer Token Auth | API authentication | - Simple implementation<br>- Standard HTTP auth<br>- Minimal overhead |
| CORS Middleware | Cross-origin protection | - Controlled access<br>- Header validation |
| Dependency Scanning | Vulnerability detection | - Automated CVE checks<br>- Version pinning |

## Implementation Priorities

1. **Security First**: Implement all security hardening measures before adding features
2. **Modular Design**: Maintain clean separation between components
3. **Resource Efficiency**: Optimize for the target hardware (i5-8400, 12GB RAM)
4. **User Experience**: Ensure responsive UI and intuitive interactions
5. **Extensibility**: Design for easy addition of new tools and capabilities

## Hardware Compatibility

The selected components are specifically optimized for the user's hardware:
- Intel i5-8400 CPU (6 cores @ 2.80GHz)
- 12GB RAM
- 64-bit Windows operating system

This configuration can comfortably run Llama 3 8B or Qwen 7B models with the complete TORIS AI stack.
