let allItems = [];
let flaggedItems = [];
let filteredItems = [];
let currentTab = 'all';
let currentPage = 1;
const pageSize = 24;

const DEFAULT_NUVIO_APIKEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzgxNTIxMzQ2LCJleHAiOjE5MzkyMDEzNDZ9.tmQaj682pwzehpqlgCDMnySOqiUvpgRbrE43T4VJpDI";

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  setupDragAndDrop();
  await loadData();
});

async function loadData() {
  if (window.COMBINED_MEDIA_DATA && Array.isArray(window.COMBINED_MEDIA_DATA)) {
    allItems = window.COMBINED_MEDIA_DATA;
  }
  if (window.FLAGGED_MEDIA_DATA && Array.isArray(window.FLAGGED_MEDIA_DATA)) {
    flaggedItems = window.FLAGGED_MEDIA_DATA;
  }

  try {
    const resCombined = await fetch('data/export/combined_full.json');
    if (resCombined.ok) {
      allItems = await resCombined.json();
    }
    const resFlagged = await fetch('data/export/reconciliation_flagged.json');
    if (resFlagged.ok) {
      flaggedItems = await resFlagged.json();
    }
  } catch (e) {
    // Local file:// protocol fetch fallback
  }

  updateCounters();
  applyFilters();
}

function updateCounters() {
  const animeCount = allItems.filter(i => i.media_type === 'anime').length;
  const movieCount = allItems.filter(i => i.media_type === 'movie').length;
  const showCount = allItems.filter(i => i.media_type === 'show').length;

  document.getElementById('stat-total').textContent = allItems.length.toLocaleString();
  document.getElementById('stat-movies').textContent = movieCount.toLocaleString();
  document.getElementById('stat-shows').textContent = showCount.toLocaleString();
  document.getElementById('stat-anime').textContent = animeCount.toLocaleString();

  document.getElementById('count-all').textContent = allItems.length;
  document.getElementById('count-anime').textContent = animeCount;
  document.getElementById('count-movies').textContent = movieCount;
  document.getElementById('count-shows').textContent = showCount;
  document.getElementById('count-flagged').textContent = flaggedItems.length;
}

function setupEventListeners() {
  // Tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentTab = e.target.getAttribute('data-tab');
      currentPage = 1;
      applyFilters();
    });
  });

  // Search & Filter Inputs
  document.getElementById('search-input').addEventListener('input', () => {
    currentPage = 1;
    applyFilters();
  });

  document.getElementById('source-filter').addEventListener('change', () => {
    currentPage = 1;
    applyFilters();
  });

  document.getElementById('sort-filter').addEventListener('change', () => {
    applyFilters();
  });

  // Pagination
  document.getElementById('btn-prev').addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      renderGrid();
    }
  });

  document.getElementById('btn-next').addEventListener('click', () => {
    const totalPages = Math.ceil(filteredItems.length / pageSize);
    if (currentPage < totalPages) {
      currentPage++;
      renderGrid();
    }
  });

  // Export & Nuvio Modals
  const exportModal = document.getElementById('export-modal');
  document.getElementById('btn-export-all').addEventListener('click', () => {
    exportModal.classList.remove('hidden');
  });

  document.getElementById('modal-close').addEventListener('click', () => {
    exportModal.classList.add('hidden');
  });

  const nuvioModal = document.getElementById('nuvio-modal');
  document.getElementById('btn-quick-nuvio').addEventListener('click', () => {
    nuvioModal.classList.remove('hidden');
  });

  document.getElementById('nuvio-modal-close').addEventListener('click', () => {
    nuvioModal.classList.add('hidden');
  });

  // Copy Raw Watched Payload JSON (p_items)
  document.getElementById('btn-copy-nuvio-json').addEventListener('click', async () => {
    const watchedPayload = generateNuvioWatchedPayload();
    const jsonStr = JSON.stringify(watchedPayload, null, 2);
    try {
      await navigator.clipboard.writeText(jsonStr);
      const btn = document.getElementById('btn-copy-nuvio-json');
      const origText = btn.innerHTML;
      btn.innerHTML = '✅ Copied p_items JSON to Clipboard!';
      btn.style.background = '#059669';
      setTimeout(() => {
        btn.innerHTML = origText;
        btn.style.background = '';
      }, 2500);
    } catch (e) {
      alert('Copied! p_items JSON generated with ' + watchedPayload.p_items.length + ' items.');
    }
  });

  // Direct Sync Watched Items to Nuvio API
  document.getElementById('btn-run-nuvio-sync').addEventListener('click', async () => {
    await runNuvioDirectSync();
  });
}

function parseNuvioAuth(inputStr) {
  let bearerToken = "";
  let apiKey = DEFAULT_NUVIO_APIKEY;

  if (!inputStr) return { bearerToken: "", apiKey };

  // Parse cURL header lines if user pasted full cURL
  const authMatch = inputStr.match(/authorization:\s*Bearer\s+([A-Za-z0-9._\-\+]+)/i) || inputStr.match(/Bearer\s+([A-Za-z0-9._\-\+]+)/i);
  if (authMatch) {
    bearerToken = authMatch[1];
  } else if (inputStr.trim().startsWith("eyJ")) {
    bearerToken = inputStr.trim();
  }

  const apiMatch = inputStr.match(/apikey:\s*([A-Za-z0-9._\-\+]+)/i);
  if (apiMatch) {
    apiKey = apiMatch[1];
  }

  return { bearerToken, apiKey };
}

function generateNuvioWatchedPayload() {
  const pItems = [];
  const profileId = parseInt(document.getElementById('nuvio-profile-id').value) || 1;

  allItems.forEach(item => {
    const ids = item.ids || {};
    const contentId = ids.imdb || ids.tmdb || ids.tvdb || ids.trakt || item.title;
    const isSeries = item.media_type === 'show' || item.media_type === 'anime';
    const contentType = isSeries ? 'series' : 'movie';
    const nowMs = Date.now();

    if (contentType === 'series') {
      if (item.episodes && item.episodes.length > 0) {
        item.episodes.forEach(ep => {
          pItems.push({
            content_id: String(contentId),
            content_type: 'series',
            title: item.title,
            season: ep.season || 1,
            episode: ep.episode || 1,
            watched_at: ep.watched_at ? new Date(ep.watched_at).getTime() : nowMs,
            ids: ids
          });
        });
      } else {
        pItems.push({
          content_id: String(contentId),
          content_type: 'series',
          title: item.title,
          season: 1,
          episode: 1,
          watched_at: nowMs,
          ids: ids
        });
      }
    } else {
      pItems.push({
        content_id: String(contentId),
        content_type: 'movie',
        title: item.title,
        season: null,
        episode: null,
        watched_at: nowMs,
        ids: ids
      });
    }

  });

  return {
    p_items: pItems,
    p_profile_id: profileId
  };
}

async function runNuvioDirectSync() {
  const tokenInput = document.getElementById('nuvio-token-input').value.trim();
  const { bearerToken, apiKey } = parseNuvioAuth(tokenInput);

  if (!bearerToken) {
    alert("Please paste your Nuvio Authorization Token (eyJ...) or cURL command from your Nuvio session into Step 1.");
    return;
  }

  const payload = generateNuvioWatchedPayload();
  const totalItems = payload.p_items.length;
  const profileId = payload.p_profile_id;
  const batchSize = 100;
  const totalBatches = Math.ceil(totalItems / batchSize);

  const progressContainer = document.getElementById('nuvio-sync-progress');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const syncStatusText = document.getElementById('sync-status-text');

  progressContainer.classList.remove('hidden');
  syncStatusText.style.color = "#10b981";

  const btnSync = document.getElementById('btn-run-nuvio-sync');
  btnSync.disabled = true;

  try {
    for (let b = 0; b < totalBatches; b++) {
      const start = b * batchSize;
      const batchItems = payload.p_items.slice(start, start + batchSize);
      const percent = Math.round(((b + 1) / totalBatches) * 100);

      syncStatusText.textContent = `Syncing items ${start + 1} to ${Math.min(start + batchSize, totalItems)} of ${totalItems} (${percent}%)...`;
      progressBarFill.style.width = `${percent}%`;

      const response = await fetch('https://api.nuvio.tv/rest/v1/rpc/sync_push_watched_items', {
        method: 'POST',
        headers: {
          'accept': '*/*',
          'apikey': apiKey,
          'authorization': `Bearer ${bearerToken}`,
          'content-type': 'application/json',
          'x-client-info': 'NuvioWebsite/1.4.23'
        },
        body: JSON.stringify({
          p_items: batchItems,
          p_profile_id: profileId
        })
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Nuvio API HTTP ${response.status}: ${errText}`);
      }

      // Short delay between batches
      await new Promise(r => setTimeout(r, 200));
    }

    syncStatusText.textContent = `🎉 Success! Imported all ${totalItems} watched items directly to Nuvio!`;
    progressBarFill.style.width = "100%";
  } catch (err) {
    console.error("Nuvio API Sync Error:", err);
    syncStatusText.style.color = "#f43f5e";
    syncStatusText.textContent = `Sync Error: ${err.message}`;
  } finally {
    btnSync.disabled = false;
  }
}

function setupDragAndDrop() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUploadedFiles(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUploadedFiles(e.target.files);
    }
  });
}

async function handleUploadedFiles(files) {
  const dropText = document.querySelector('.drop-text h3');
  dropText.textContent = `Processing ${files.length} file(s)...`;

  for (let file of files) {
    if (file.name.endsWith('.zip')) {
      try {
        const zip = await JSZip.loadAsync(file);
        let count = 0;
        zip.forEach(() => count++);
        dropText.textContent = `Extracted ${count} files from ${file.name}! Ready to sync to Nuvio API below.`;
      } catch (e) {
        dropText.textContent = `Uploaded ${file.name}.`;
      }
    } else {
      dropText.textContent = `Uploaded ${file.name}. Processing library...`;
    }
  }

  setTimeout(() => {
    document.getElementById('nuvio-modal').classList.remove('hidden');
  }, 800);
}

function applyFilters() {
  const searchInput = document.getElementById('search-input');
  const search = searchInput.value ? searchInput.value.toLowerCase().trim() : '';
  const sourceFilter = document.getElementById('source-filter').value;
  const sortFilter = document.getElementById('sort-filter').value;

  if (currentTab === 'flagged') {
    filteredItems = flaggedItems.filter(f => {
      if (!search) return true;
      const t1 = (f.item1_title || '').toLowerCase();
      const t2 = (f.item2_title || '').toLowerCase();
      return t1.includes(search) || t2.includes(search);
    });
  } else {
    filteredItems = allItems.filter(item => {
      if (currentTab !== 'all' && item.media_type !== currentTab) {
        return false;
      }

      if (sourceFilter !== 'all' && !item.sources[sourceFilter]) {
        return false;
      }

      if (search) {
        const titleMatch = (item.title || '').toLowerCase().includes(search) || (item.title_original || '').toLowerCase().includes(search);
        const ids = item.ids || {};
        const idMatch = Object.values(ids).some(val => val && String(val).toLowerCase().includes(search));
        if (!titleMatch && !idMatch) return false;
      }

      return true;
    });

    filteredItems.sort((a, b) => {
      if (sortFilter === 'title-asc') {
        return (a.title || '').localeCompare(b.title || '');
      } else if (sortFilter === 'rating-desc') {
        return (b.aggregated_rating || 0) - (a.aggregated_rating || 0);
      } else if (sortFilter === 'year-desc') {
        return (b.year || 0) - (a.year || 0);
      }
      return 0;
    });
  }

  renderGrid();
}

function renderGrid() {
  const grid = document.getElementById('media-grid');
  grid.innerHTML = '';

  if (filteredItems.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
        <h3>No media items match your search.</h3>
      </div>
    `;
    document.getElementById('pagination-controls').style.display = 'none';
    return;
  }

  document.getElementById('pagination-controls').style.display = 'flex';
  const totalPages = Math.ceil(filteredItems.length / pageSize);
  document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages || 1}`;

  const startIdx = (currentPage - 1) * pageSize;
  const pageItems = filteredItems.slice(startIdx, startIdx + pageSize);

  pageItems.forEach(item => {
    if (currentTab === 'flagged') {
      const card = document.createElement('div');
      card.className = 'media-card glass-card';
      card.innerHTML = `
        <div class="card-header">
          <span class="type-badge badge-anime">Flagged Conflict</span>
        </div>
        <div>
          <h4 class="media-title">${item.item1_title || 'Item 1'}</h4>
          <p style="font-size: 0.8rem; color: var(--accent-amber); margin: 0.25rem 0;">vs</p>
          <h4 class="media-title">${item.item2_title || 'Item 2'}</h4>
          <p class="media-year">Reason: ${item.reason}</p>
        </div>
      `;
      grid.appendChild(card);
    } else {
      const card = document.createElement('div');
      card.className = 'media-card glass-card';
      const mtype = item.media_type || 'movie';
      const badgeClass = mtype === 'anime' ? 'badge-anime' : (mtype === 'show' ? 'badge-show' : 'badge-movie');
      const ratingText = item.aggregated_rating ? `★ ${item.aggregated_rating}` : 'Unrated';
      const ids = item.ids || {};

      card.innerHTML = `
        <div>
          <div class="card-header">
            <span class="type-badge ${badgeClass}">${mtype}</span>
            <span class="rating-tag">${ratingText}</span>
          </div>
          <h3 class="media-title" style="margin-top: 0.75rem;">${escapeHtml(item.title)}</h3>
          ${item.year ? `<p class="media-year">${item.year}</p>` : ''}
        </div>

        <div class="id-pills">
          ${ids.imdb ? `<span class="id-pill has-val">IMDB: ${ids.imdb}</span>` : ''}
          ${ids.tmdb ? `<span class="id-pill has-val">TMDB: ${ids.tmdb}</span>` : ''}
          ${ids.tvdb ? `<span class="id-pill has-val">TVDB: ${ids.tvdb}</span>` : ''}
          ${ids.mal ? `<span class="id-pill has-val">MAL: ${ids.mal}</span>` : ''}
          ${ids.kitsu ? `<span class="id-pill has-val">Kitsu: ${ids.kitsu}</span>` : ''}
          ${ids.simkl ? `<span class="id-pill has-val">Simkl: ${ids.simkl}</span>` : ''}
        </div>
      `;
      grid.appendChild(card);
    }
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
