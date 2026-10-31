# Build and release

Use Python 3.12 and the official Dify CLI 0.6.12. From the repository root:

```sh
python scripts/build_shared.py --check
python -m pytest tests
cd dify
python -m pip install -r requirements.txt
dify plugin package .
```

Install the resulting package in the disposable Dify instance, authorize the provider,
import the example into a fresh app and execute it. Check the variable picker, all routing
paths, errors and an image. Packaging does not validate SDK registration or workflow output.
Use the same package for installation checks and distribution.

For marketplace submission follow the current `langgenius/dify-plugins` contribution process,
including license, privacy statement and source review. GitHub distribution uses a public Release with the `.difypkg`, starter workflow, corresponding source archive, setup guides and checksums. Marketplace listing requires its own reviewed submission. Never include provider keys or tenant-specific exports.

For changes, regenerate shared protocol files with `python scripts/build_shared.py`, update
manifest version and `valen_client.py` User-Agent together, rebuild, install and repeat platform
acceptance. Keep the previous artifact and exported workflows for rollback.

## Self-hosted signature policy

The GitHub package is unsigned. Only an administrator who has reviewed the plugin should allow it. Setting `FORCE_VERIFYING_SIGNATURE=false` on the plugin daemon permits unsigned plugins across the instance; restart that service after changing the configuration. Do not change this setting on someone else’s instance. Environments requiring marketplace signatures must wait for a signed distribution.
