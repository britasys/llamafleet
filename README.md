Here is a complete `README.md` you can put in the repo:

# LlamaFleet

Open-source gateway middleware for `llama.cpp` servers.

LlamaFleet gives you one OpenAI-compatible endpoint for multiple local `llama.cpp` backends. It adds routing, API-key authentication, health checks, backend discovery, streaming proxy support, and a clean foundation for future production features such as metrics, fallback routing, caching, RAG, and tool execution.

## Why LlamaFleet?

`llama.cpp` is excellent for running GGUF models locally, on servers, edge machines, laptops, and private infrastructure. However, real applications often need more than a single model server.

LlamaFleet sits in front of one or more `llama-server` instances and acts as a lightweight control layer.

```text
Client App
   ↓
LlamaFleet Gateway
   ↓
llama.cpp Server A
llama.cpp Server B
llama.cpp Server C
```

Instead of connecting each app directly to a specific `llama.cpp` server, your applications connect to LlamaFleet.

## Features

* OpenAI-compatible `/v1/chat/completions` proxy
* OpenAI-compatible `/v1/completions` proxy
* OpenAI-compatible `/v1/embeddings` proxy
* OpenAI-compatible `/v1/models` endpoint
* Multiple backend support
* Model-based routing
* Default backend routing
* Bearer token API-key authentication
* Streaming response proxying
* Backend health checks
* Simple YAML configuration
* FastAPI-based API server
* Clean structure for future extensions

## Roadmap

Planned features:

* Backend fallback routing
* Per-backend load balancing
* Request and response logging
* SQLite usage database
* Prometheus metrics
* Token usage tracking
* Latency tracking
* Prompt and embedding cache
* RAG injection layer
* Tool execution layer
* Per-user API keys
* Rate limiting
* Web dashboard
* GGUF model registry
* Docker Compose examples
* Kubernetes deployment examples

## Project Status

LlamaFleet is currently in early MVP stage.

The first goal is simple:

> Provide one OpenAI-compatible gateway that can route requests to multiple `llama.cpp` servers.

## Requirements

* Python 3.11+
* One or more running `llama-server` instances
* A GGUF model loaded by each `llama.cpp` backend

## Installation

Clone the repository:

```bash
git clone https://github.com/your-username/llamafleet.git
cd llamafleet
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quickstart

Start a `llama.cpp` server first.

Example:

```bash
llama-server -m models/model.gguf --host 127.0.0.1 --port 8081
```

Create a config file:

```bash
cp configs/config.example.yaml configs/config.yaml
```

Run LlamaFleet:

```bash
LLAMA_GATEWAY_CONFIG=configs/config.yaml uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Test the health endpoint:

```bash
curl http://localhost:4000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Configuration

Example `configs/config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 4000

auth:
  api_keys:
    - local-key

backends:
  - name: llama-small
    url: http://127.0.0.1:8081
    models:
      - auto
      - llama-small

  - name: qwen-coder
    url: http://127.0.0.1:8082
    models:
      - qwen-coder

routing:
  default_backend: llama-small
```

### Server

```yaml
server:
  host: 0.0.0.0
  port: 4000
```

Defines where LlamaFleet should run.

### Authentication

```yaml
auth:
  api_keys:
    - local-key
```

Defines valid API keys.

Clients must send:

```http
Authorization: Bearer local-key
```

### Backends

```yaml
backends:
  - name: llama-small
    url: http://127.0.0.1:8081
    models:
      - auto
      - llama-small
```

Each backend represents one running `llama-server` instance.

### Routing

```yaml
routing:
  default_backend: llama-small
```

If no backend matches the requested model, LlamaFleet sends the request to the default backend.

## API

### Health Check

```http
GET /health
```

Example:

```bash
curl http://localhost:4000/health
```

Response:

```json
{
  "status": "ok"
}
```

## Backend Status

```http
GET /backends
```

Example:

```bash
curl http://localhost:4000/backends
```

Response:

```json
{
  "llama-small": {
    "url": "http://127.0.0.1:8081",
    "status": "healthy"
  },
  "qwen-coder": {
    "url": "http://127.0.0.1:8082",
    "status": "offline"
  }
}
```

## List Models

```http
GET /v1/models
```

Example:

```bash
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer local-key"
```

Response:

```json
{
  "object": "list",
  "data": [
    {
      "id": "auto",
      "object": "model",
      "owned_by": "llamafleet"
    },
    {
      "id": "llama-small",
      "object": "model",
      "owned_by": "llamafleet"
    },
    {
      "id": "qwen-coder",
      "object": "model",
      "owned_by": "llamafleet"
    }
  ]
}
```

## Chat Completions

```http
POST /v1/chat/completions
```

Example:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "Say hello in one sentence."
      }
    ]
  }'
```

Example with streaming:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": "Write a short poem about local AI."
      }
    ]
  }'
```

## Text Completions

```http
POST /v1/completions
```

Example:

```bash
curl http://localhost:4000/v1/completions \
  -H "Authorization: Bearer local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "prompt": "Local AI is",
    "max_tokens": 64
  }'
```

## Embeddings

```http
POST /v1/embeddings
```

Example:

```bash
curl http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "embedding-model",
    "input": "LlamaFleet is a gateway for llama.cpp."
  }'
```

## Using with the OpenAI Python SDK

Install the SDK:

```bash
pip install openai
```

Example:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="local-key",
)

response = client.chat.completions.create(
    model="auto",
    messages=[
        {
            "role": "user",
            "content": "Explain local-first AI in one paragraph.",
        }
    ],
)

print(response.choices[0].message.content)
```

## Using with JavaScript

Install the SDK:

```bash
npm install openai
```

Example:

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "http://localhost:4000/v1",
  apiKey: "local-key"
});

const response = await client.chat.completions.create({
  model: "auto",
  messages: [
    {
      role: "user",
      content: "Explain GGUF models in simple terms."
    }
  ]
});

console.log(response.choices[0].message.content);
```

## How Routing Works

LlamaFleet checks the `model` field in the request.

Example request:

```json
{
  "model": "qwen-coder",
  "messages": [
    {
      "role": "user",
      "content": "Write a Python function."
    }
  ]
}
```

If `qwen-coder` exists in a backend config, the request is sent to that backend.

Example:

```yaml
backends:
  - name: qwen-coder-backend
    url: http://127.0.0.1:8082
    models:
      - qwen-coder
```

If no model matches, the request is sent to:

```yaml
routing:
  default_backend: llama-small
```

## Example Multi-Backend Setup

Run two `llama.cpp` servers:

```bash
llama-server -m models/llama-small.gguf --host 127.0.0.1 --port 8081
```

```bash
llama-server -m models/qwen-coder.gguf --host 127.0.0.1 --port 8082
```

Configure LlamaFleet:

```yaml
server:
  host: 0.0.0.0
  port: 4000

auth:
  api_keys:
    - local-key

backends:
  - name: llama-small
    url: http://127.0.0.1:8081
    models:
      - auto
      - llama-small

  - name: qwen-coder
    url: http://127.0.0.1:8082
    models:
      - qwen-coder

routing:
  default_backend: llama-small
```

Send a general chat request:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {
        "role": "user",
        "content": "What is local AI?"
      }
    ]
  }'
```

Send a coding request:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer local-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-coder",
    "messages": [
      {
        "role": "user",
        "content": "Write a FastAPI health endpoint."
      }
    ]
  }'
```

## Environment Variables

LlamaFleet uses this environment variable:

```bash
LLAMAFLEET_CONFIG=configs/config.yaml
```

If not provided, it uses:

```bash
configs/config.example.yaml
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run the server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 4000
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

Format code:

```bash
ruff format .
```

## Suggested Repository Structure

```text
llamafleet/
  app/
    __init__.py
    main.py
    config.py
    auth.py
    router.py
    proxy.py
    health.py
  configs/
    config.example.yaml
  tests/
    test_auth.py
  pyproject.toml
  README.md
  LICENSE
  .gitignore
```

## Current Limitations

LlamaFleet is intentionally minimal in the first version.

Current limitations:

* No fallback routing yet
* No load balancing yet
* No request logging database yet
* No metrics endpoint yet
* No dashboard yet
* No RAG injection yet
* No tool execution layer yet
* No per-user permissions yet
* No rate limits yet
* No model lifecycle management yet

These features are planned for future releases.

## Security Notes

Do not expose LlamaFleet directly to the public internet without proper security controls.

For production use, place it behind:

* HTTPS
* Reverse proxy
* Strong API keys
* Firewall rules
* Rate limiting
* Access logs
* Monitoring

Example production stack:

```text
Client
  ↓
Nginx or Caddy with HTTPS
  ↓
LlamaFleet
  ↓
Private llama.cpp backends
```

## Docker

Docker support is planned.

Suggested future command:

```bash
docker compose up
```

Suggested future services:

```text
llamafleet
llama-server-small
llama-server-coder
prometheus
grafana
redis
```

## Use Cases

LlamaFleet is useful for:

* Local AI applications
* Private AI deployments
* Internal company assistants
* Developer tools
* Local coding assistants
* RAG applications
* Multi-model experiments
* Edge AI systems
* Offline AI environments
* Teams using multiple GGUF models
* OpenAI-compatible apps that need local backends

## Design Goals

LlamaFleet should be:

* Simple to run
* Easy to configure
* OpenAI-compatible
* Local-first
* Model-agnostic within `llama.cpp`
* Lightweight
* Production-friendly
* Extensible
* Easy to self-host
* Useful without requiring a full agent framework

## Non-Goals

LlamaFleet is not trying to be:

* A replacement for `llama.cpp`
* A replacement for `llama-server`
* A full agent framework
* A prompt-template framework
* A vector database
* A hosted SaaS platform
* A model training system

## Comparison with App Frameworks

Frameworks such as LangChain are mainly used inside applications for chains, agents, tools, memory, and RAG workflows.

LlamaFleet is different.

It runs as a standalone gateway in front of `llama.cpp` servers.

```text
LangChain app
   ↓
LlamaFleet
   ↓
llama.cpp backends
```

This means you can use LlamaFleet under LangChain, OpenAI SDKs, custom apps, internal tools, or any client that supports OpenAI-compatible APIs.

## Versioning

Before version `1.0.0`, configuration and internal APIs may change.

Suggested release plan:

```text
v0.1.0  Basic proxy, routing, auth, health checks
v0.2.0  Fallback routing and backend status improvements
v0.3.0  Request logging and usage tracking
v0.4.0  Metrics and Prometheus support
v0.5.0  Prompt and embedding cache
v0.6.0  RAG injection
v0.7.0  Tool execution
v1.0.0  Stable config and production deployment docs
```

## Contributing

Contributions are welcome.

Good first issues:

* Add tests for routing
* Add tests for config loading
* Add fallback backend support
* Add request latency logging
* Add Docker Compose example
* Add Prometheus metrics
* Improve streaming support
* Add `/v1/responses` proxy support
* Add better error handling
* Add documentation examples

## Development Principles

* Keep the core small
* Avoid unnecessary abstractions
* Prefer configuration over code
* Do not hide `llama.cpp`
* Keep OpenAI compatibility simple
* Make local deployment easy
* Add production features gradually
* Keep advanced features optional

## License

Apache-2.0 is recommended for this project.

You can also use MIT if you prefer a shorter and simpler license.

## Name

Current project name:

```text
LlamaFleet
```

Meaning:

> A lightweight gateway for managing a fleet of local `llama.cpp` model servers.

## Acknowledgements

LlamaFleet is designed to work with `llama.cpp` and GGUF-based local model deployments.

## Disclaimer

LlamaFleet is an independent open-source project and is not affiliated with the `llama.cpp` project.
