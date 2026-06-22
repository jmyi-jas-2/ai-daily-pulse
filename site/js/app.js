// AI Daily Pulse - Main App Logic (Phase 3: Real Data Integration)

(function() {
  'use strict';

  // DATA_BASE_PATH: relative path from site/index.html to project root data/
  const DATA_BASE_PATH = '../data/';

  let currentFeaturedIndex = 0;
  let currentFilter = 'all';
  let autoRotateInterval = null;

  // Live data holders
  let featuredData = [];
  let allNewsData = [];
  let currentDataDate = '';

  // ===== Utility: Text cleanup / escaping =====
  function decodeEntities(str) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = String(str || '');
    return textarea.value;
  }

  function cleanText(str) {
    if (!str) return '';
    return decodeEntities(str).replace(/<[^>]*>/g, '')
              .replace(/<[^>]*$/g, '')
              .replace(/https?:\/\/\S+/g, '')
              .replace(/\s+/g, ' ')
              .trim();
  }

  function escapeHtml(str) {
    return cleanText(str).replace(/[&<>'"]/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[char]));
  }

  function escapeAttribute(str) {
    return String(str || '').replace(/[&<>'"]/g, char => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[char]));
  }

  function normalizeSources(sources) {
    if (!Array.isArray(sources)) return [];
    return sources.map(source => ({
      name: cleanText(source.name),
      title: cleanText(source.title) || cleanText(source.name),
      url: source.url || ''
    })).filter(source => source.title || source.name || source.url);
  }

  // ===== Initialize =====
  async function init() {
    const targetDate = getRequestedDate();
    const loaded = await loadDayData(targetDate);

    if (!loaded) {
      console.log('[App] No real data found, falling back to mock data');
      useMockData();
    }

    renderHero();
    renderNews();
    startAutoRotate();
    bindEvents();
  }

  // ===== Date Helpers =====
  function getBeijingDate(offsetDays = 0) {
    // Use timezone-aware formatting to avoid double offset bugs.
    const todayInBeijing = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(new Date());

    if (offsetDays === 0) return todayInBeijing;

    const d = new Date(`${todayInBeijing}T00:00:00Z`);
    d.setUTCDate(d.getUTCDate() + offsetDays);
    return d.toISOString().slice(0, 10);
  }

  function getYesterday() {
    return getBeijingDate(-1);
  }

  function getRequestedDate() {
    const params = new URLSearchParams(window.location.search);
    const dateParam = params.get('date');
    return /^\d{4}-\d{2}-\d{2}$/.test(dateParam || '') ? dateParam : getYesterday();
  }

  function formatTime(timestamp) {
    if (!timestamp) return '';
    try {
      const d = new Date(timestamp);
      const h = d.getHours().toString().padStart(2, '0');
      const m = d.getMinutes().toString().padStart(2, '0');
      return `${h}:${m}`;
    } catch {
      return '';
    }
  }

  // ===== Load Real Data =====
  async function loadDayData(dateStr) {
    const url = DATA_BASE_PATH + dateStr + '.json';
    try {
      const res = await fetch(url);
      if (!res.ok) return false;

      const data = await res.json();
      const top3 = data.top3 || [];
      const allNews = data.all_news || [];
      currentDataDate = cleanText(data.date) || dateStr;

      if (top3.length === 0 && allNews.length === 0) return false;

      // Transform top3 into featured format
      featuredData = top3.map(item => ({
        quote: `"${cleanText(item.summary)}"`,
        author: item.sources && item.sources[0] ? cleanText(item.sources[0].name) : '',
        source: item.sources && item.sources.length > 1 ? `${item.sources.length} sources` : '',
        time: formatTime(item.timestamp) || '',
        tag: cleanText(item.category),
        category: item.categoryKey,
        // Extra fields for bracket
        trendScore: item.importance_score,
        mentionCount: item.mention_count,
        title: cleanText(item.title),
        summary: cleanText(item.summary) || cleanText(item.title),
        url: item.sources && item.sources[0] ? item.sources[0].url : '',
        sources: normalizeSources(item.sources)
      }));

      // Transform all_news into grid format
      allNewsData = allNews.map(item => ({
        category: cleanText(item.category),
        categoryKey: item.categoryKey,
        time: formatTime(item.timestamp),
        title: cleanText(item.title),
        summary: cleanText(item.summary) || cleanText(item.title),
        mentions: item.mention_count,
        score: item.importance_score,
        url: item.sources && item.sources[0] ? item.sources[0].url : '',
        sources: normalizeSources(item.sources)
      }));

      console.log(`[App] Loaded real data for ${dateStr}: ${top3.length} top, ${allNews.length} total`);
      return true;
    } catch (e) {
      console.log(`[App] Failed to load ${url}:`, e.message);
      return false;
    }
  }

  // ===== Fallback to Mock =====
  function useMockData() {
    currentDataDate = getYesterday();
    featuredData = (typeof MOCK_FEATURED !== 'undefined') ? MOCK_FEATURED.map(item => ({
      ...item,
      trendScore: 0,
      mentionCount: 0,
      title: '',
      summary: ''
    })) : [];

    allNewsData = (typeof MOCK_NEWS !== 'undefined') ? MOCK_NEWS : [];

    // Merge timeline data if available
    if (typeof MOCK_TIMELINE !== 'undefined') {
      featuredData.forEach((item, i) => {
        if (MOCK_TIMELINE[i]) {
          item.trendScore = MOCK_TIMELINE[i].trendScore;
          item.mentionCount = MOCK_TIMELINE[i].mentionCount;
          item.title = MOCK_TIMELINE[i].title;
          item.summary = MOCK_TIMELINE[i].summary;
        }
      });
    }
  }

  // ===== Render Hero Section =====
  function renderHero() {
    if (featuredData.length === 0) return;

    // Render first featured item
    updateFeaturedContent(0);

    // Rebuild timeline
    const timeline = document.getElementById('timeline');
    const lineHTML = '<div class="timeline-line"></div>';
    const itemsHTML = featuredData.slice(0, 3).map((item, i) => `
      <div class="timeline-item ${i === 0 ? 'active' : ''}" data-index="${i}">
        <div class="timeline-dot"></div>
        <div class="timeline-card">
          <div class="card-time">${item.time ? item.time.replace('今日 ', '') : ''}</div>
          <div class="card-title">${escapeHtml(item.title)}</div>
          <div class="card-source">来源: ${escapeHtml(item.author)}${item.mentionCount ? ' 等 ' + item.mentionCount + ' 处提及' : ''}</div>
        </div>
      </div>
    `).join('');
    timeline.innerHTML = lineHTML + itemsHTML;

    // Rebuild indicators
    const indicatorsEl = document.getElementById('quoteIndicators');
    indicatorsEl.innerHTML = featuredData.slice(0, 3).map((_, i) =>
      `<span class="indicator ${i === 0 ? 'active' : ''}"></span>`
    ).join('');

    // Update bracket
    updateBracket(0);
  }

  function updateFeaturedContent(index) {
    const data = featuredData[index];
    if (!data) return;

    const quoteEl = document.getElementById('featuredQuote');
    quoteEl.querySelector('.quote-text').textContent = data.quote;
    quoteEl.querySelector('.quote-author').textContent = data.author;
    quoteEl.querySelector('.quote-source').textContent = data.source;
    quoteEl.querySelector('.quote-time').textContent = data.time;
    quoteEl.querySelector('.tag').textContent = data.tag;
  }

  // ===== Auto Rotate =====
  function startAutoRotate() {
    if (featuredData.length <= 1) return;
    autoRotateInterval = setInterval(() => {
      const max = Math.min(featuredData.length, 3);
      const nextIndex = (currentFeaturedIndex + 1) % max;
      switchFeatured(nextIndex);
    }, 8000);
  }

  function switchFeatured(index) {
    if (index === currentFeaturedIndex) return;

    const quoteEl = document.getElementById('featuredQuote');
    const indicators = document.querySelectorAll('.indicator');
    const timelineItems = document.querySelectorAll('.timeline-item');

    quoteEl.classList.add('fade-out');

    setTimeout(() => {
      updateFeaturedContent(index);

      indicators.forEach((ind, i) => {
        ind.classList.toggle('active', i === index);
      });

      timelineItems.forEach((item, i) => {
        item.classList.toggle('active', i === index);
      });

      updateBracket(index);
      quoteEl.classList.remove('fade-out');
      currentFeaturedIndex = index;
    }, 400);
  }

  function updateBracket(index) {
    const data = featuredData[index];
    if (!data) return;

    const bracket = document.getElementById('dataBracket');
    const values = bracket.querySelectorAll('.bracket-value');

    values[0].textContent = data.trendScore || 0;
    values[1].textContent = data.mentionCount || 0;
    values[2].textContent = data.summary || '';
  }

  // ===== Render News Grid =====
  function renderNews() {
    const grid = document.getElementById('newsGrid');
    const filtered = currentFilter === 'all'
      ? allNewsData
      : allNewsData.filter(item => item.categoryKey === currentFilter);

    if (filtered.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-secondary); padding: 2rem;">暂无数据</div>';
      return;
    }

    // Normalize scores for bar display (max score = 100%)
    const maxScore = Math.max(...filtered.map(item => item.score || 0), 1);

    grid.innerHTML = filtered.map(item => {
      const barWidth = Math.round((item.score / maxScore) * 100);
      const sources = item.sources && item.sources.length ? item.sources : [{
        name: '',
        title: item.title,
        url: item.url
      }];
      const sourcesHTML = sources.map((source, index) => `
        <a class="source-link" href="${escapeAttribute(source.url)}" target="_blank" rel="noopener noreferrer">
          <span class="source-index">${index + 1}</span>
          <span class="source-link-main">
            <span class="source-link-title">${escapeHtml(source.title || source.name)}</span>
            ${source.name ? `<span class="source-link-name">${escapeHtml(source.name)}</span>` : ''}
          </span>
        </a>
      `).join('');
      return `
        <div class="news-item" data-category="${item.categoryKey}" data-url="${escapeAttribute(item.url)}">
          <div class="news-item-header">
            <span class="news-item-category">${escapeHtml(item.category)}</span>
            <span class="news-item-time">${item.time}</span>
          </div>
          <div class="news-item-title">${escapeHtml(item.title)}</div>
          <div class="news-item-summary">${escapeHtml(item.summary)}</div>
          <div class="news-item-footer">
            <span class="news-item-mentions">${item.mentions} 处提及</span>
            <div class="news-item-score">
              <div class="score-bar">
                <div class="score-fill" style="width: ${barWidth}%"></div>
              </div>
              <span class="score-num">${item.score}</span>
            </div>
          </div>
          <div class="source-drawer" aria-label="提及来源">
            <div class="source-drawer-title">提及来源</div>
            <div class="source-list">${sourcesHTML}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ===== Event Bindings =====
  function bindEvents() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderNews();
      });
    });

    // Timeline items click (event delegation)
    document.getElementById('timeline').addEventListener('click', (e) => {
      const item = e.target.closest('.timeline-item');
      if (!item) return;
      const index = parseInt(item.dataset.index);
      clearInterval(autoRotateInterval);
      switchFeatured(index);
      startAutoRotate();
    });

    // Indicators click (event delegation)
    document.getElementById('quoteIndicators').addEventListener('click', (e) => {
      const ind = e.target.closest('.indicator');
      if (!ind) return;
      const index = [...ind.parentElement.children].indexOf(ind);
      clearInterval(autoRotateInterval);
      switchFeatured(index);
      startAutoRotate();
    });

    document.getElementById('newsGrid').addEventListener('contextmenu', (e) => {
      const item = e.target.closest('.news-item');
      if (!item) return;
      e.preventDefault();
      item.classList.toggle('sources-open');
    });

    document.getElementById('newsGrid').addEventListener('click', (e) => {
      if (e.target.closest('.source-link')) return;
      const item = e.target.closest('.news-item');
      if (!item || !item.dataset.url) return;
      window.open(item.dataset.url, '_blank', 'noopener');
    });

    // Refresh: reload selected data date
    document.getElementById('refreshBtn').addEventListener('click', async () => {
      const btn = document.getElementById('refreshBtn');
      btn.textContent = '刷新中...';
      btn.style.borderColor = 'var(--accent)';
      btn.style.color = 'var(--accent)';

      const targetDate = currentDataDate || getRequestedDate();
      const loaded = await loadDayData(targetDate);
      if (loaded) {
        renderHero();
        renderNews();
      }

      btn.textContent = '已更新';
      setTimeout(() => {
        btn.textContent = '刷新';
        btn.style.borderColor = '';
        btn.style.color = '';
      }, 1500);
    });

    // Export button
    document.getElementById('exportBtn').addEventListener('click', exportToCSV);

    // Language toggle (placeholder)
    document.getElementById('langBtn').addEventListener('click', () => {
      const btn = document.getElementById('langBtn');
      btn.textContent = btn.textContent === 'EN' ? '中文' : 'EN';
    });
  }

  // ===== Export to CSV =====
  function exportToCSV() {
    const headers = ['日期', '时间', '分类', '标题', '摘要', '提及来源数', '热度指数'];
    const exportDate = currentDataDate || getYesterday();
    const rows = allNewsData.map(item => [
      exportDate,
      item.time,
      item.category,
      item.title,
      item.summary,
      item.mentions,
      item.score
    ]);

    let csv = '\uFEFF'; // BOM for Chinese support in Excel
    csv += headers.join(',') + '\n';
    rows.forEach(row => {
      csv += row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `ai-daily-pulse_${exportDate}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  // ===== Start =====
  document.addEventListener('DOMContentLoaded', init);
})();