# Reproduce platform acceptance

Use disposable self-hosted instances and synthetic tickets/images. These scripts refuse
non-loopback platform URLs. They create test workflows and executions in the configured
workspace; they do not send business messages or modify production workflows. Provider
requests still go to the Valen endpoint configured in that test instance.

Install Python 3.12 dependencies with the Dify requirements plus the LangChain test extra
and PyYAML. Build and install the package under test before running acceptance. A source
checkout test does not establish that the installed package works.

## n8n

Set `VALEN_ACCEPTANCE_N8N_EMAIL` and `VALEN_ACCEPTANCE_N8N_PASSWORD` to the disposable
owner login. The default URL is `http://127.0.0.1:15678`; override it using
`VALEN_ACCEPTANCE_N8N_URL`. Then run:

```sh
python acceptance/n8n_runtime.py
python -m acceptance.n8n_live
```

The script hosts controlled replies on loopback and runs the actual n8n execution engine.
It checks branch destinations, source preservation, images, boundaries, errors, retries and
malformed replies. The real timeout case takes about six minutes: three 120-second attempts.
It is a transport/adapter test, not a model accuracy benchmark. The separate imported
support-routing example must also be run against the real API.

## Dify

Set `VALEN_ACCEPTANCE_DIFY_EMAIL` and `VALEN_ACCEPTANCE_DIFY_PASSWORD`. The default URL is
`http://127.0.0.1:18980`; override with `VALEN_ACCEPTANCE_DIFY_URL`. Authorize the Valen
provider with a synthetic test credential. Uploaded files require correctly configured
container-reachable `FILES_URL` / `INTERNAL_FILES_URL` in self-hosted Dify.

```sh
VALEN_ACCEPTANCE_DIFY_PACKAGE=/absolute/path/valen.difypkg python -m acceptance.dify_package
python -m acceptance.dify_runtime
python -m acceptance.dify_tools_runtime
python -m acceptance.dify_limits_runtime
```

The installer replaces only Valen in the disposable instance and preserves its provider
credentials. It verifies the exact installed identifier, because installing a package with
the same version can silently retain the previous build. Runtime tests import the checked-in
example into a fresh app, assert the executed end nodes and outputs, and restore the original
graph after temporary test configurations. API failure must reach the error output without
an answer. The middle-band case changes thresholds to exercise the workflow path; it does
not claim that the model is uncertain on that ticket.

## Evidence and distribution

Reports go to `validation/`. Keep current reports paired with package checksums and installed
versions; never include secrets. These local checks do not establish npm/PyPI publication,
marketplace approval, n8n Cloud verification, or Coze workflow acceptance. Each has its own
release gate in the acceptance record.

## Installed LangChain wheel

Use a separate environment with the built wheel and LangGraph installed. From the repository
root run the following with that environment's Python:

```sh
VALEN_ACCEPTANCE_WHEEL=/absolute/path/langchain_valen-0.1.0-py3-none-any.whl /path/to/clean-env/bin/python -m acceptance.langchain_live
```

The script compares installed Python files to the wheel, sends a synthetic image and tickets
to the real free API, checks tool and async calls and three actual LangGraph destinations,
and checks the hosted question-limit error.

## Local generated Coze code

```sh
VALEN_API_KEY_FILE=/secure/location/valen-key.txt python -m acceptance.coze_live
```

Only Coze runtime typing imports are stubbed. All API requests are real, including image
download and a hosted-limit failure. The key is read from the named file and never printed.
This remains separate from Coze IDE cloud tests and published workflow acceptance.
