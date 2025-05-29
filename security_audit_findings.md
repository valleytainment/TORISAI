# TORIS AI Security Audit Findings & Implementation Plan

## Overview

This document summarizes the critical findings from the security audit of the TORIS AI codebase and outlines our implementation plan to address these issues. The audit identified several high-priority security vulnerabilities, architectural weaknesses, and code quality issues that must be addressed to create a production-ready system.

## Critical Security Findings

| Issue | Severity | Description | Mitigation |
|-------|----------|-------------|------------|
| Arbitrary Code Execution | Critical | `execute_code()` forwards user input directly to `subprocess` without sandboxing | Implement Docker-based sandboxing with resource limits |
| Naive Tool Parsing | High | String matching (`if "web_search(" in call:`) creates injection vulnerabilities | Switch to structured JSON tool calls with Pydantic validation |
| Blocking HTTP Calls | Medium | Synchronous `requests` to Ollama blocks the Gradio UI thread | Replace with async HTTP client (`httpx.AsyncClient`) |
| Memory Leakage | Medium | Chroma client never closed, vectors written on every turn | Implement singletons with proper cleanup and TTL |
| Missing Authentication | High | No rate-limiting or auth on FastAPI endpoints | Add bearer token auth and CORS host allow-list |
| Exception Handling | Medium | Missing exception logging and proper error responses | Implement structured logging and proper HTTP exceptions |
| Dependency Management | Medium | Unpinned dependencies in setup.py | Pin specific version ranges for all dependencies |

## Architecture Improvements

1. **Structured Tool Protocol**
   - Replace string-based tool detection with Pydantic models
   - Implement proper validation and type checking for all tool calls
   - Create a registry of available tools with documentation

2. **Secure Code Execution**
   - Implement Docker-based sandboxing for all code execution
   - Add resource limits (memory, CPU, network)
   - Implement timeouts and output size limits

3. **Async Architecture**
   - Replace synchronous HTTP calls with async alternatives
   - Implement proper background task handling
   - Ensure UI remains responsive during long-running operations

4. **Repository Reorganization**
   - Restructure into proper Python packages
   - Separate UI and backend logic
   - Create dedicated modules for agents, tools, memory, and API

5. **CI/CD Pipeline**
   - Implement GitHub Actions for testing and deployment
   - Add dependency scanning and security checks
   - Enforce code quality with linters and formatters

## Implementation Plan

### Phase 1: Core Security Hardening

1. **Implement Structured Tool Protocol**
   - Create Pydantic models for all tool calls
   - Update agent logic to use structured tool calls
   - Add validation for all tool inputs

2. **Secure Code Execution**
   - Implement Docker-based sandboxing
   - Add resource limits and timeouts
   - Create secure execution environment

3. **Fix Memory Management**
   - Implement proper cleanup for Chroma client
   - Add TTL for vector storage
   - Optimize memory retrieval

### Phase 2: Architecture Improvements

1. **Async Architecture**
   - Replace synchronous HTTP calls with async alternatives
   - Update agent logic to support async operations
   - Implement proper background task handling

2. **Repository Reorganization**
   - Restructure into proper Python packages
   - Separate UI and backend logic
   - Create dedicated modules for agents, tools, memory, and API

3. **Improve Error Handling**
   - Implement structured logging
   - Add proper exception handling
   - Create user-friendly error messages

### Phase 3: Quality & CI/CD

1. **Code Quality**
   - Add type hints and docstrings
   - Implement linting and formatting
   - Improve test coverage

2. **CI/CD Pipeline**
   - Set up GitHub Actions
   - Add dependency scanning
   - Implement automated testing

3. **Documentation**
   - Create comprehensive API documentation
   - Update user guides
   - Document security practices

## New Repository Structure

```
torisai/
├─ torisai/
│  ├─ agents/                 # planner.py, coder.py, researcher.py
│  ├─ tools/                  # web.py, browser.py, secure_code.py
│  ├─ memory/manager.py
│  ├─ api/                    # FastAPI app (ws + REST)
│  ├─ core/settings.py        # pydantic BaseSettings, .env
│  └─ __init__.py
├─ ui/                         # Gradio or React front-end
├─ tests/
│  ├─ unit/
│  └─ integration/
├─ docker-compose.yml
├─ pyproject.toml
└─ README.md
```

## Conclusion

Implementing these changes will significantly improve the security, reliability, and maintainability of the TORIS AI system. By addressing the critical security vulnerabilities and architectural weaknesses identified in the audit, we will create a production-ready system that follows industry best practices.
