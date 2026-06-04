(() => {
  const postMetric = (url) => fetch(url, { method: 'POST', keepalive: true }).catch(() => undefined);
  const setText = (root, selector, value) => {
    const node = root.querySelector(selector);
    if (node) node.textContent = value;
  };
  const renderCandle = (candle) => {
    const panel = document.querySelector('#selected-candle');
    if (!panel || !candle) return;
    setText(panel, 'h2', `Selected Candle #${candle.id}`);
    const metrics = panel.querySelector('.market-metrics');
    if (metrics) {
      metrics.innerHTML = `<div><dt>OHLC</dt><dd>${candle.open} / ${candle.high} / ${candle.low} / ${candle.close}</dd></div><div><dt>Volume</dt><dd>${candle.volume ?? 0}</dd></div><div><dt>Price Change %</dt><dd>${Number(candle.price_change_pct || 0).toFixed(4)}</dd></div><div><dt>Attribution Confidence</dt><dd>${Number(candle.confidence || 0).toFixed(2)}</dd></div>`;
    }
    postMetric(`/web/market-time-machine/candle-click?timeframe=${encodeURIComponent(candle.timeframe || '1h')}`);
  };
  const renderMarker = (marker) => {
    const panel = document.querySelector('#selected-event');
    if (!panel || !marker) return;
    panel.innerHTML = `<h2>Related Events</h2><h3>${marker.title}</h3><dl class="market-metrics"><div><dt>Source</dt><dd>${marker.source}</dd></div><div><dt>Published Time</dt><dd>${marker.published_at}</dd></div><div><dt>BTC Price At Publish</dt><dd>${marker.btc_price_at_publish ?? 'unknown'}</dd></div><div><dt>15m Change</dt><dd>${marker.change_15m ?? 'n/a'}</dd></div><div><dt>1h Change</dt><dd>${marker.change_1h ?? 'n/a'}</dd></div><div><dt>4h Change</dt><dd>${marker.change_4h ?? 'n/a'}</dd></div><div><dt>24h Change</dt><dd>${marker.change_24h ?? 'n/a'}</dd></div><div><dt>Confidence</dt><dd>${Number(marker.confidence || 0).toFixed(2)}</dd></div><div><dt>Evidence Available</dt><dd>${marker.evidence_available}</dd></div><div><dt>Historical Matches</dt><dd>${(marker.similarity_preview || []).length}</dd></div></dl><div class="panel-actions"><a href="${marker.evidence_url || '#'}" data-evidence-link>Open Evidence</a><a href="${marker.replay_url || '#'}" data-replay-link>Replay</a><a href="${marker.similar_events_url || '#'}">Show Similar Events</a></div>`;
    postMetric(`/web/market-time-machine/marker-click?marker_type=${encodeURIComponent(marker.canonical_type || 'uncertain_news')}`);
  };
  document.querySelectorAll('.market-candle').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.market-candle').forEach((item) => item.classList.remove('is-selected'));
      button.classList.add('is-selected');
      renderCandle(JSON.parse(button.dataset.candle || '{}'));
    });
    button.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') button.click(); });
  });
  document.querySelectorAll('.market-marker').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.market-marker').forEach((item) => item.classList.remove('is-selected'));
      button.classList.add('is-selected');
      renderMarker(JSON.parse(button.dataset.marker || '{}'));
    });
    button.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') button.click(); });
  });
  document.querySelectorAll('[data-replay-link]').forEach((link) => link.addEventListener('click', () => postMetric('/web/market-time-machine/replay-open')));
  document.querySelectorAll('[data-evidence-link]').forEach((link) => link.addEventListener('click', () => postMetric('/web/market-time-machine/evidence-view')));
  let scale = 1;
  document.querySelectorAll('[data-market-zoom]').forEach((button) => button.addEventListener('click', () => {
    scale = button.dataset.marketZoom === 'in' ? Math.min(2.5, scale + 0.2) : Math.max(0.6, scale - 0.2);
    document.querySelectorAll('.candle-layer').forEach((layer) => { layer.style.transform = `scaleX(${scale})`; });
  }));
  document.querySelectorAll('[data-market-pan]').forEach((button) => button.addEventListener('click', () => {
    const chart = button.closest('.chart-card')?.querySelector('.market-chart');
    if (chart) chart.scrollBy({ left: button.dataset.marketPan === 'left' ? -180 : 180, behavior: 'smooth' });
  }));
})();
