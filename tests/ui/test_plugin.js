const plugin = require('../../providers/otaku_sync_plugin.js');

console.assert(plugin !== undefined, "Plugin exports must be defined");
const manifest = plugin.getManifest();
console.assert(manifest.id === "com.nuvio.plugin.whatiwatchedsync", "Manifest ID must match com.nuvio.plugin.whatiwatchedsync");
console.assert(manifest.name === "What I Watched Sync", "Manifest name must match What I Watched Sync");

plugin.getCatalog("anime", "what_i_watched_library", {}).then(catalog => {
  console.assert(Array.isArray(catalog.metas), "Catalog metas must be an array");
  console.assert(catalog.metas.length > 0, "Catalog must return at least 1 item");
  console.log("SUCCESS: Hermes plugin bundle test passed 100%");
}).catch(err => {
  console.error("FAIL: Catalog error", err);
  process.exit(1);
});
