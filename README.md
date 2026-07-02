# llama-gateway

OpenAI-compatible gateway for llama.cpp backends.

## Quickstart

```bash
cp configs/config.example.yaml config.yaml
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

```bash
curl http://localhost:4000/v1/chat/completions \
  -H 'Authorization: Bearer local-key' \
  -H 'Content-Type: application/json' \
  -d '{"model":"auto","messages":[{"role":"user","content":"Hello"}]}'
```
# LlamaMesh
