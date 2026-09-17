# Contributing to aeraforhome-api

An unofficial Python client for the Aera for Home smart fragrance diffuser
cloud API, reverse-engineered from the Android app. It's designed to power a
Home Assistant integration but has no dependency on Home Assistant.
Contributions — new endpoints, bug fixes, API changes upstream broke — are
welcome.

## Getting started

```
git clone https://github.com/zackwag/aeraforhome-api.git
cd aeraforhome-api
pip install -e .[dev]
```

## Development

The library lives in `aera/` (`api.py` for the client, `device.py` for
device state, `contentful.py` for the fragrance catalog lookup). `example.py`
is a minimal runnable usage example.

Run the test suite:

```
pytest
```

## Commit messages and pull requests

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, etc.). Pull requests are squash-merged, and the **PR title** becomes the commit on `main` — so PR titles must follow this format. This is enforced automatically by the "Conventional Commits" check.

Direct pushes to `main` are allowed but must also use a Conventional Commits-formatted commit message (validated by the same check).

## Opening a pull request

1. Fork the repo and create a branch off `main`.
2. Make your changes.
3. Open a pull request with a Conventional Commits-formatted title.
4. Wait for CI to pass — required checks must be green before merge.

## Reporting issues

Use [GitHub Issues](../../issues) for bugs and feature requests.
