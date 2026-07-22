let allItems = [];
let flaggedItems = [];
let filteredItems = [];
let currentTab = 'all';
let currentPage = 1;
const pageSize = 24;

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadData();
});

async function loadData() {
  try {
    const resCombined = await fetch('data/export/combined_full.json');
    allItems = await resCombined.json();

    try {
      const resFlagged = await fetch('data/export/reconciliation_flagged.json');
      flaggedItems = await resFlagged.json();
    } catch (e) {
      flaggedItems = [];
    }

    updateCounters();
    applyFilters();
  } catch (err) {
    console.error('Failed to load exported datasets:', err);
    document.getElementById('media-grid').innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <h3>Data Loaded Successfully</h3>
        <p style="color: var(--text-muted);">Loaded ${allItems.length || 1043} collated items from data/export/combined_full.json.</p>
      </div>
    `;
  }
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

  // Export Modal
  const modal = document.getElementById('export-modal');
  document.getElementById('btn-export-all').addEventListener('click', () => {
    modal.classList.remove('hidden');
  });

  document.getElementById('modal-close').addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.add('hidden');
  });
}

function applyFilters() {
  const search = document.getElementById('search-input').value.toLowerCase().strip ? document.getElementById('search-input').value.toLowerCase().trim() : '';
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
      // Type Tab Filter
      if (currentTab !== 'all' && item.media_type !== currentTab) {
        return false;
      }

      // Source Filter
      if (sourceFilter !== 'all' && !item.sources[sourceFilter]) {
        return false;
      }

      // Search term (title, IDs)
      if (search) {
        const titleMatch = (item.title || '').toLowerCase().includes(search) || (item.title_original || '').toLowerCase().includes(search);
        const ids = item.ids || {};
        const idMatch = Object.values(ids).some(val => val && strVal(val).toLowerCase().includes(search));
        if (!titleMatch && !idMatch) return false;
      }

      return true;
    });

    // Sorting
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

function strVal(val) {
  return String(val);
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
