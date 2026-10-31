// Install the actual tarball in a disposable host and load its n8n entry points.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const host = fs.mkdtempSync(path.join(os.tmpdir(), 'valen-n8n-package-'));
try {
 const tarball = path.resolve(process.argv[2] || 'valen-team-n8n-nodes-valen-0.1.0.tgz');
 execFileSync('npm', ['install', '--prefix', host, '--cache', path.join(host, 'cache'), '--offline', '--ignore-scripts', '--legacy-peer-deps', '--no-audit', '--no-fund', tarball], {stdio:'pipe'});
 // A real n8n host supplies this peer. Use the pinned development host for this smoke check.
 fs.symlinkSync(path.resolve('node_modules/n8n-workflow'), path.join(host, 'node_modules/n8n-workflow'), 'junction');
 const root = path.join(host,'node_modules/@valen-team/n8n-nodes-valen');
 const pkg = require(path.join(root,'package.json'));
 for (const file of [...pkg.n8n.nodes, ...pkg.n8n.credentials]) {
  const exports = require(path.join(root,file));
  const Constructor = exports[Object.keys(exports)[0]];
  assert.ok(new Constructor());
 }
 for (const file of ['dist/nodes/Valen/valen.png','README.md','README_zh.md','RELEASING.md','examples/support-routing.json']) assert.ok(fs.existsSync(path.join(root,file)), file);
 const example = require(path.join(root,'examples/support-routing.json'));
 assert.equal(example.active,false);
 assert.equal(example.connections['Route tickets'].main.length,4);
 console.log('Tarball installation and entry-point smoke check passed.');
} finally {
 fs.rmSync(host,{recursive:true,force:true});
}
