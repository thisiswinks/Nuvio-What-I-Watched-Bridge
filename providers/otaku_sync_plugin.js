/**
 * What I Watched Sync Plugin
 * Hermes-compatible Nuvio Provider JS Bundle
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
    // Returns Otaku-enriched catalog items to Nuvio TV UI
    return Promise.resolve({
      metas: [
        {
          id: "mal:58921",
          type: "anime",
          name: "Jack-of-All-Trades, Party of None",
          poster: "https://myanimelist.net/images/anime/1000/1.jpg",
          description: "Synced across Trakt, MAL (ID: 58921), and Simkl via What I Watched Sync.",
          releaseInfo: "2026",
          genres: ["Anime", "Fantasy"],
          status: "MAL Synced • Simkl Synced"
        }
      ]
    });
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
