# Release and maintain

Use Python 3.12 from the repository root:

```sh
python scripts/build_shared.py --check
python -m pip install -r dify/requirements.txt -e './langchain[test]'
python -m pytest tests coze/tests
python -m build langchain --outdir artifacts/langchain
python -m twine check artifacts/langchain/*
```

Install the wheel outside the checkout and run the included example against your configured endpoint. Publish the reviewed wheel and source archive to PyPI. A new project requires an account-scoped upload token for its first release or a pending Trusted Publisher; use a project-scoped token thereafter and keep credentials outside the repository.

For automated releases, configure the PyPI Trusted Publisher for `Valen-Team/valen-integrations`, workflow `release.yml`, and push a matching `langchain-v<version>` tag after the source commit is approved. See [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

After publishing, install the exact version from the public PyPI index in a clean environment, import the public classes, and run a sample judgment. Keep the question set and threshold configuration with the application.

For upgrades, update the package version and User-Agent together and regenerate shared code. Run the application's sample workflow before deploying. Roll back by reinstalling the previous pinned version and restoring its question configuration.
