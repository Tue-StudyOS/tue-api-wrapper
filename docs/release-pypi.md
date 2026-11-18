# PyPI Release Checklist

Python packages are published to PyPI as distribution artifacts: a source distribution and a wheel. This project should publish through PyPI Trusted Publishing from GitHub Actions, not through a long-lived PyPI token.

Official references:

- Python Packaging User Guide: <https://packaging.python.org/en/latest/flow/>
- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/>

## One-time setup

- [ ] Create or claim the `tue-api-wrapper` project on PyPI.
- [ ] Add a PyPI Trusted Publisher for GitHub repository `SebastianBoehler/tue-api-wrapper`.
- [ ] Configure the PyPI publisher workflow as `publish-python.yml`.
- [ ] Configure the PyPI publisher environment as `pypi`.
- [ ] In GitHub, create an environment named `pypi`.
- [ ] Add a required reviewer to the GitHub `pypi` environment.
- [ ] Confirm the package metadata in `package/pyproject.toml`.
- [ ] Confirm the package README renders correctly on PyPI.

## Before every release

- [ ] Update `package/pyproject.toml` version.
- [ ] Run `cd package && pytest`.
- [ ] Run `cd package && python -m compileall src`.
- [ ] Run `cd package && rm -rf dist && python -m build`.
- [ ] Inspect `package/dist/` and confirm it contains one `.tar.gz` and one `.whl`.
- [ ] Install the built wheel in a fresh virtual environment.
- [ ] Test `python -c "from tue_api_wrapper import TuebingenPublicClient"`.
- [ ] Test `tue mcp --help`.
- [ ] Commit the release changes.
- [ ] Push to `main`.
- [ ] Create a GitHub release or run the `Publish Python package` workflow manually.
- [ ] Approve the `pypi` environment deployment in GitHub Actions.
- [ ] Confirm the new version appears on PyPI.

## Local build commands

```bash
cd package
python3 -m pip install --upgrade build
rm -rf dist
python3 -m build
```

## Fresh install smoke test

```bash
python3 -m venv /tmp/tue-api-wrapper-smoke
source /tmp/tue-api-wrapper-smoke/bin/activate
pip install package/dist/*.whl
python -c "from tue_api_wrapper import TuebingenPublicClient; print(TuebingenPublicClient)"
tue mcp --help
deactivate
```

## Notes

- Do not upload from a developer laptop unless Trusted Publishing is unavailable and there is a deliberate token-handling plan.
- Do not include `.env`, HAR captures, build folders, or private student data in release artifacts.
- Use TestPyPI first if the release process changes or package metadata was heavily edited.
