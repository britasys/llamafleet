from app.services.request_transformer import transform_body


def test_chat_completions_injects_model(base_config):
    backend = base_config.backends[0]
    body = transform_body("/v1/chat/completions",
                          {"messages": [{"role": "user", "content": "hi"}]}, backend)
    assert body["model"] == backend.model


def test_chat_completions_preserves_caller_messages(base_config):
    backend = base_config.backends[0]
    backend.prompt = "SYS"
    original = [{"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"}]
    body = transform_body("/v1/chat/completions",
                          {"messages": list(original)}, backend)
    assert body["messages"][-2:] == original


def test_chat_completions_injects_system_prompt_once(base_config):
    backend = base_config.backends[0]
    backend.prompt = "SYS"
    body = transform_body("/v1/chat/completions",
                          {"messages": [{"role": "user", "content": "hi"}]}, backend)
    assert body["messages"][0] == {"role": "system", "content": "SYS"}
    assert len(body["messages"]) == 2


def test_chat_completions_does_not_duplicate_system_prompt(base_config):
    backend = base_config.backends[0]
    backend.prompt = "SYS"
    body = transform_body(
        "/v1/chat/completions",
        {"messages": [{"role": "system", "content": "SYS"},
                      {"role": "user", "content": "hi"}]},
        backend,
    )
    assert len([m for m in body["messages"] if m["role"] == "system"]) == 1


def test_completions_prefixes_prompt(base_config):
    backend = base_config.backends[0]
    backend.prompt = "SYS"
    body = transform_body("/v1/completions", {"prompt": "hello"}, backend)
    assert body["prompt"] == "SYS\n\nhello"
    assert body["model"] == backend.model


def test_embeddings_does_not_inject_messages(base_config):
    backend = base_config.backends[3]
    backend.prompt = "SYS"
    body = transform_body("/v1/embeddings", {"input": ["a", "b"]}, backend)
    assert "messages" not in body
    assert "prompt" not in body
    assert body["model"] == backend.model


def test_rerank_does_not_inject_messages(base_config):
    backend = base_config.backends[3]
    backend.prompt = "SYS"
    body = transform_body(
        "/v1/rerank", {"query": "q", "documents": ["a"]}, backend)
    assert "messages" not in body
    assert body["model"] == backend.model


def test_original_body_not_mutated(base_config):
    backend = base_config.backends[0]
    backend.prompt = "SYS"
    original = {"messages": [{"role": "user", "content": "hi"}]}
    transform_body("/v1/chat/completions", original, backend)
    assert original == {"messages": [{"role": "user", "content": "hi"}]}
