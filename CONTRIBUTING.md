# Contributing to LlamaFleet

Thank you for your interest in contributing to LlamaFleet!

Whether you're fixing a bug, improving the documentation, or implementing a new feature, your contributions are welcome.

## Before You Start

If you're planning to work on a significant feature or make a large architectural change, please open an issue first so we can discuss the approach before you start coding.

For smaller improvements, feel free to submit a pull request directly.

## Getting Started

1. Fork the repository.
2. Clone your fork.

```bash
git clone https://github.com/<your-username>/llamafleet.git
cd llamafleet
```

3. Create a virtual environment.

```bash
python -m venv .venv
```

4. Activate it.

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

5. Install development dependencies.

```bash
pip install -e ".[dev]"
```

6. Run the development server.

```bash
uvicorn app.main:app --reload
```

## Development Guidelines

Please keep pull requests focused and easy to review.

When contributing:

- Keep changes small and focused.
- Prefer simple, readable code.
- Follow the existing project structure and coding style.
- Add or update tests when appropriate.
- Update documentation if your change affects users.

## Running Checks

Before submitting a pull request, run:

```bash
ruff format .
ruff check .
pytest
```

Please ensure all checks pass.

## Pull Requests

When opening a pull request:

- Clearly describe what changed and why.
- Reference related issues when applicable.
- Keep pull requests focused on a single topic.

## Project Philosophy

LlamaFleet aims to remain:

- Lightweight
- Easy to understand
- OpenAI-compatible
- Simple to configure
- Production-friendly
- Easy to extend

When adding new features, prefer simple solutions over complex abstractions. Advanced functionality should remain optional whenever possible.

## Good First Contributions

Some ideas for new contributors include:

- Improving documentation
- Adding unit tests
- Improving error messages
- Expanding API examples
- Improving health checks
- Adding new OpenAI-compatible endpoints
- Improving logging and metrics

## Questions

If you have questions or would like feedback on an idea, open an issue and start a discussion.

Thanks for helping make LlamaFleet better!
