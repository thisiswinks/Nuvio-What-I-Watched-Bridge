/**
 * What I Watched Sync - reference plugin bundle
 *
 * NOTE: this is a reference/identity stub, NOT the sync runtime. NuvioTV's JS
 * plugin runtime (core/plugin/PluginRuntime.kt) is a stream scraper: it only
 * calls getStreams(tmdbId, mediaType, season, episode). It never calls
 * getManifest/getCatalog and never receives playback events, so watch-history
 * sync cannot run here. Sync lives in native NuvioTV Kotlin services; see
 * docs/NUVIO_INTEGRATION.md and docs/adr/0001-provider-runtime-in-nuviotv.md.
 *
 * getManifest/getCatalog below describe the addon's identity and the catalog
 * surface for a Stremio-style addon host; getCatalog returns an empty list
 * because real library data comes from the on-device store, not this bundle.
 */

(function () {
  var PLUGIN_ID = "com.nuvio.plugin.whatiwatchedsync";
  var PLUGIN_NAME = "What I Watched Sync";

  function getManifest() {
    return {
      id: PLUGIN_ID,
      name: PLUGIN_NAME,
      version: "1.1.0",
      description: "Outbound watch-history sync with Otaku-Mappings enrichment for Trakt, MyAnimeList, Simkl, and Nuvio Sync",
      types: ["anime", "movie", "series"],
      catalogs: [
        {
          type: "anime",
          id: "what_i_watched_library",
          name: "What I Watched Library & History"
        }
      ]
    };
  }

  function getCatalog(type, id, extra) {
    // Reference stub: the real library is served from the on-device store, not
    // fabricated here. Returns an empty catalog rather than placeholder data.
    return Promise.resolve({ metas: [] });
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = {
      getManifest: getManifest,
      getCatalog: getCatalog
    };
  } else if (typeof window !== "undefined") {
    window.WhatIWatchedSyncPlugin = {
      getManifest: getManifest,
      getCatalog: getCatalog
    };
  }
})();
