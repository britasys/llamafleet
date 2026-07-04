import pytest
import yaml

from app.core.config import load_yaml


def write_yaml(tmp_path, data):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def minimal_data():
    return {
        "server": {},
        "auth": {"enabled": False},
        "prompts": {"default_prompt": "hi"},
        "rags": [],
        "backends": [
            {"name": "a", "url": "http://a", "model": "m",
                "prompt_name": "default_prompt"},
        ],
        "routing": {"default_backend": "a", "rules": []},
        "logging": {"enabled": True},
    }


def test_loads_valid_config(tmp_path):
    path = write_yaml(tmp_path, minimal_data())
    config = load_yaml(path)
    assert config.backends[0].prompt == "hi"


def test_unknown_prompt_name_raises(tmp_path):
    data = minimal_data()
    data["backends"][0]["prompt_name"] = "missing"
    path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError):
        load_yaml(path)


def test_unknown_rag_name_raises(tmp_path):
    data = minimal_data()
    data["backends"][0]["rag_name"] = "missing"
    path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError):
        load_yaml(path)


def test_duplicate_backend_names_raise(tmp_path):
    data = minimal_data()
    data["backends"].append(dict(data["backends"][0]))
    path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError):
        load_yaml(path)


def test_empty_backends_raise(tmp_path):
    data = minimal_data()
    data["backends"] = []
    path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError):
        load_yaml(path)


def test_rule_pointing_to_unknown_backend_raises(tmp_path):
    data = minimal_data()
    data["routing"]["rules"] = [{"name": "x", "backend": "ghost"}]
    path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError):
        load_yaml(path)


def test_rag_resolved_onto_backend(tmp_path):
    data = minimal_data()
    data["rags"] = [{"name": "r1", "url": "http://q",
                     "type": "qdrant", "collection": "c"}]
    data["backends"][0]["rag_name"] = "r1"
    path = write_yaml(tmp_path, data)
    config = load_yaml(path)
    assert config.backends[0].rag.name == "r1"
