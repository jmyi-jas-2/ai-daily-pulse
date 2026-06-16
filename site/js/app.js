// AI Daily Pulse - Main App Logic

(function() {
  'use strict';

  let currentFeaturedIndex = 0;
  let currentTimelineIndex = 0;
  let currentFilter = 'all';
  let autoRotateInterval = null;

  // ===== Initialize =====
  function init() {
    renderNews(MOCK_NEWS);
    startAutoRotate();
    bindEvents();
  }

  // ===== Auto Rotate (every 8 seconds) =====
  function startAutoRotate() {
    autoRotateInterval = setInterval(() => {
      const nextIndex = (currentFeaturedIndex + 1) % MOCK_FEATURED.length;
      switchFeatured(nextIndex);
    }, 8000);
  }

  function switchFeatured(index) {
    if (index === currentFeaturedIndex) return;
    
    const quoteEl = document.getElementById('featuredQuote');
    const indicators = document.querySelectorAll('.indicator');
    const timelineItems = document.querySelectorAll('.timeline-item');

    // Fade out
    quoteEl.classList.add('fade-out');

    setTimeout(() => {
      // Update quote
      const data = MOCK_FEATURED[index];
      quoteEl.querySelector('.quote-text').textContent = data.quote;
      quoteEl.querySelector('.quote-author').textContent = data.author;
      quoteEl.querySelector('.quote-source').textContent = data.source;
      quoteEl.querySelector('.quote-time').textContent = data.time;
      quoteEl.querySelector('.tag').textContent = data.tag;

      // Update indicators
      indicators.forEach((ind, i) => {
        ind.classList.toggle('active', i === index);
      });

      // Update timeline
      timelineItems.forEach((item, i) => {
        item.classList.toggle('active', i === index);
      });

      // Update data bracket
      updateBracket(index);

      // Fade in
      quoteEl.classList.remove('fade-out');
      
      currentFeaturedIndex = index;
      currentTimelineIndex = index;
    }, 400);
  }

  function updateBracket(index) {
    const data = MOCK_TIMELINE[index];
    const bracket = document.getElementById('dataBracket');
    const values = bracket.querySelectorAll('.bracket-value');
    
    values[0].textContent = data.trendScore;
    values[1].textContent = data.mentionCount;
    values[2].textContent = data.summary;
  }

  // ===== Render News Grid =====
  function renderNews(newsData) {
    const grid = document.getElementById('newsGrid');
    const filtered = currentFilter === 'all' 
      ? newsData 
      : newsData.filter(item => item.categoryKey === currentFilter);

    grid.innerHTML = filtered.map(item => `
      <div class="news-item" data-category="${item.categoryKey}">
        <div class="news-item-header">
          <span class="news-item-category">${item.category}</span>
          <span class="news-item-time">${item.time}</span>
        </div>
        <div class="news-item-title">${item.title}</div>
        <div class="news-item-summary">${item.summary}</div>
        <div class="news-item-footer">
          <span class="news-item-mentions">${item.mentions} 处提及</span>
          <div class="news-item-score">
            <div class="score-bar">
              <div class="score-fill" style="width: ${item.score}%"></div>
            </div>
            <span class="score-num">${item.score}</span>
          </div>
        </div>
      </div>
    `).join('');
  }

  // ===== Event Bindings =====
  function bindEvents() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderNews(MOCK_NEWS);
      });
    });

    // Timeline items click
    document.querySelectorAll('.timeline-item').forEach((item, index) => {
      item.addEventListener('click', () => {
        clearInterval(autoRotateInterval);
        switchFeatured(index);
        startAutoRotate();
      });
    });

    // Indicators click
    document.querySelectorAll('.indicator').forEach((ind, index) => {
      ind.addEventListener('click', () => {
        clearInterval(autoRotateInterval);
        switchFeatured(index);
        startAutoRotate();
      });
    });

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
      const btn = document.getElementById('refreshBtn');
      btn.textContent = '刷新中...';
      btn.style.borderColor = 'var(--accent)';
      btn.style.color = 'var(--accent)';
      setTimeout(() => {
        btn.textContent = '已更新';
        setTimeout(() => {
          btn.textContent = '刷新';
          btn.style.borderColor = '';
          btn.style.color = '';
        }, 1500);
      }, 1200);
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
    const rows = MOCK_NEWS.map(item => [
      '2026-06-16',
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
    link.download = `ai-daily-pulse_2026-06-16.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  // ===== Start =====
  document.addEventListener('DOMContentLoaded', init);
})();
