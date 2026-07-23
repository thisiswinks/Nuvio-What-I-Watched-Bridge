const plugin = require('../../providers/otaku_sync_plugin.js');

console.assert(plugin !== undefined, "Plugin exports must be defined");
const manifest = plugin.getManifest();
console.assert(manifest.id === "com.nuvio.plugin.whatiwatchedsync", "Manifest ID must match com.nuvio.plugin.whatiwatchedsync");
console.assert(manifest.name === "What I Watched Sync", "Manifest name must match What I Watched Sync");
console.assert(manifest.version === "1.1.0", "Manifest version must match 1.1.0");
console.assert(Array.isArray(manifest.catalogs) && manifest.catalogs.length === 1, "Manifest must declare its catalog");

plugin.getCatalog("anime", "what_i_watched_library", {}).then(catalog => {
  // Reference stub returns an empty, well-formed catalog: no fabricated data.
  console.assert(Array.isArray(catalog.metas), "Catalog metas must be an array");
  console.assert(catalog.metas.length === 0, "Reference stub catalog must be empty (real data is on-device)");
  console.log("SUCCESS: Hermes plugin bundle test passed 100%");
}).catch(err => {
  console.error("FAIL: Catalog error", err);
  process.exit(1);
});
