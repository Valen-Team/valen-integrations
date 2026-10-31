# Release and maintain

Use Node.js 22.16+ in this directory:

```sh
npm ci --ignore-scripts
npm test
npm pack
node scripts/check-package.cjs
```

Install the resulting tarball in a disposable self-hosted n8n instance. Import the support-routing example, select a credential, and check the normal and separate error outputs before publishing.

Publish the reviewed tarball to the public npm registry with `--access public`. Keep registry credentials outside the repository. For automated releases, configure npm Trusted Publishing for `Valen-Team/valen-integrations`, workflow `release.yml`, and push a matching `n8n-v<version>` tag after the source commit is approved. The release workflow generates npm provenance. See [npm Trusted Publishing](https://docs.npmjs.com/trusted-publishers/).

After publishing, install the exact version from npm in a fresh environment and load the node and credential. npm publication and n8n Cloud verification are separate: describe this package as a self-hosted community node until Cloud verification is granted.

For upgrades, update the package version and User-Agent together, build and publish a new version, and run a sample workflow before reconnecting actions. Keep the previous version available for rollback.
