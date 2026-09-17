# AGENTS.md

## Project overview

aeraforhome-api is an unofficial async Python client (`aiohttp`-based) for
the Aera for Home smart fragrance diffuser cloud API (Ayla Networks IoT
platform), reverse-engineered from the Android app. No Home Assistant
dependency; designed to be used standalone or to back an HA integration.

## Setup

```
pip install -e .[dev]
```

## Build / Run

No build step (pure Python library). `example.py` shows minimal usage:

```
python example.py
```

## Test

```
pytest
```

`pyproject.toml` configures `asyncio_mode = "auto"` and `testpaths =
["tests"]`. CI (`.github/workflows/test.yml`) installs with `pip install
.[dev]` then runs `pytest` on Python 3.13.

## Repository structure

- `aera/` — the library: `api.py` (HTTP client + auth), `device.py` (device
  state model), `contentful.py` (fragrance catalog via Contentful CMS),
  `const.py`
- `tests/` — pytest test suite
- `example.py` — minimal runnable usage example
- `openapi.yaml` — API surface documentation

## Commit and PR conventions

- Commit messages and PR titles must follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `build:`, `perf:`, `style:`, `revert:`), optionally with a scope, e.g. `fix(api): handle null response`.
- This repo squash-merges pull requests only; the PR title becomes the final commit message on `main`.
- A "Conventional Commits" CI check enforces this on both PR titles and direct-push commit messages.
- Branch protection on `main`: no force-pushes, no branch deletion, required status checks must pass.
