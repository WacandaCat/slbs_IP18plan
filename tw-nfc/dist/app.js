/* tw-nfc-guide renderer
 * - loads data.json (same directory), picks language, renders DOM.
 * - language priority: ?lang=  > localStorage('lang') > navigator.language > zh
 * - all Google Maps links are text-query based (place name + address), no coordinates in URLs.
 */
(function () {
  'use strict';
  var LANGS = ['zh', 'en', 'ko'];
  var LABEL = { zh: '中文', en: 'EN', ko: '한국어' };
  var slug = document.body.getAttribute('data-slug');
  var root = document.getElementById('app');

  function pickLang(fallback) {
    var q = new URLSearchParams(location.search).get('lang');
    if (q && LANGS.indexOf(q) >= 0) return q;
    try { var s = localStorage.getItem('lang'); if (s && LANGS.indexOf(s) >= 0) return s; } catch (e) {}
    var nav = (navigator.languages && navigator.languages[0]) || navigator.language || '';
    nav = nav.toLowerCase();
    if (nav.indexOf('ko') === 0) return 'ko';
    if (nav.indexOf('zh') === 0) return 'zh';
    if (nav.indexOf('en') === 0) return 'en';
    return fallback || 'zh';
  }

  var lang = pickLang();
  var DATA = null;

  /* t(): pull current language from a {zh,en,ko} dict; plain strings pass through; fallback zh -> en. */
  function t(v) {
    if (v == null) return '';
    if (typeof v === 'string' || typeof v === 'number') return String(v);
    return v[lang] || v.zh || v.en || v.ko || '';
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  /* ---- Google Maps URL builders (text queries, per handoff) ---- */
  function q(v) { return encodeURIComponent(v); }
  function placeQuery(p) {
    // Always query in Chinese: name + address gives the most reliable match in Taiwan.
    var name = (p.name && (p.name.zh || t(p.name))) || '';
    var addr = (p.address && (p.address.zh || t(p.address))) || '';
    return addr ? name + ' ' + addr : name;
  }
  function mapsSearch(p) {
    return 'https://www.google.com/maps/search/?api=1&query=' + q(placeQuery(p));
  }
  function mapsDir(origin, dest, mode) {
    var u = 'https://www.google.com/maps/dir/?api=1&destination=' + q(placeQuery(dest));
    if (origin) u += '&origin=' + q(placeQuery(origin));
    if (mode) u += '&travelmode=' + mode; // walking | driving | transit | bicycling
    return u;
  }

  var ICON = {
    pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    walk: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="13" cy="4" r="1.6"/><path d="M10 22l2-7-3-2 1-5 4 1 2 3 3 1M9 12l-2 4-3 2M13 15l3 3 1 4"/></svg>',
    car: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 16l1.5-6A2 2 0 0 1 7.4 8.5h9.2a2 2 0 0 1 1.9 1.5L20 16"/><rect x="3" y="16" width="18" height="4" rx="1"/><circle cx="7.5" cy="20" r="1.5"/><circle cx="16.5" cy="20" r="1.5"/></svg>',
    bus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="3" width="16" height="15" rx="2"/><path d="M4 10h16M8 21v-3M16 21v-3"/><circle cx="8" cy="14.5" r="1"/><circle cx="16" cy="14.5" r="1"/></svg>',
    taxi: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 6h6l1 2.5M4 16l1.5-6A2 2 0 0 1 7.4 8.5h9.2a2 2 0 0 1 1.9 1.5L20 16"/><rect x="3" y="16" width="18" height="4" rx="1"/><circle cx="7.5" cy="20" r="1.5"/><circle cx="16.5" cy="20" r="1.5"/></svg>',
    train: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="3" width="14" height="14" rx="3"/><path d="M5 10h14M8 21l2-4M16 21l-2-4"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/></svg>',
    phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>'
  };
  var UI = {
    info:     { zh: '店家資訊', en: 'Details', ko: '상세 정보' },
    walk:     { zh: '步行路線', en: 'Walk', ko: '도보 길찾기' },
    drive:    { zh: '開車路線', en: 'Drive', ko: '자동차 길찾기' },
    transit:  { zh: '大眾運輸', en: 'Transit', ko: '대중교통' },
    taxi:     { zh: '計程車 / 開車', en: 'Taxi / Car', ko: '택시 / 자동차' },
    map:      { zh: '在 Google 地圖開啟', en: 'Open in Google Maps', ko: '구글맵에서 열기' },
    dirHere:  { zh: '導航到這裡', en: 'Directions', ko: '여기로 길찾기' },
    call:     { zh: '撥打電話', en: 'Call', ko: '전화 걸기' },
    approx:   { zh: '約', en: '~', ko: '약 ' },
    min:      { zh: '分鐘', en: ' min', ko: '분' },
    km:       { zh: ' 公里', en: ' km', ko: ' km' },
    walkLbl:  { zh: '步行', en: 'walk', ko: '도보' },
    carLbl:   { zh: '車程', en: 'drive', ko: '차량' },
    estimate: { zh: '距離與時間為估計值，實際以 Google 地圖為準。', en: 'Distances and times are estimates; check Google Maps for live routing.', ko: '거리·시간은 추정치입니다. 실제 경로는 구글맵을 확인하세요.' },
    loadErr:  { zh: '資料載入失敗，請重新整理。', en: 'Could not load page data. Please refresh.', ko: '데이터를 불러오지 못했습니다. 새로고침해 주세요.' }
  };
  function ui(k) { return t(UI[k]); }

  function fmtDist(item) {
    var parts = [];
    if (item.km != null) parts.push('<span>' + ui('approx') + item.km + ui('km') + '</span>');
    if (item.walk_min != null) parts.push('<span>' + ui('walkLbl') + ' ' + ui('approx') + item.walk_min + ui('min') + '</span>');
    if (item.drive_min != null) parts.push('<span>' + ui('carLbl') + ' ' + ui('approx') + item.drive_min + ui('min') + '</span>');
    return parts.join('');
  }
  function btn(href, icon, label, pri) {
    var a = el('a', 'btn' + (pri ? ' pri' : ''), ICON[icon] + '<span>' + esc(label) + '</span>');
    a.href = href; a.target = '_blank'; a.rel = 'noopener';
    return a;
  }

  /* ---- renderers per item kind ---- */
  function renderPoi(item, page) {
    var c = el('div', 'card poi');
    var top = el('div', 'top');
    var h = el('div');
    h.appendChild(el('h3', null, esc(t(item.name))));
    var alt = altName(item.name);
    if (alt) h.appendChild(el('div', 'alt', esc(alt)));
    top.appendChild(h);
    if (item.tag) top.appendChild(el('span', 'tag', esc(t(item.tag))));
    c.appendChild(top);
    if (item.desc) c.appendChild(el('p', null, esc(t(item.desc))));
    var meta = fmtDist(item);
    if (item.hours) meta += '<span>' + esc(t(item.hours)) + '</span>';
    if (meta) c.appendChild(el('div', 'meta', meta));
    var b = el('div', 'btns');
    b.appendChild(btn(mapsSearch(item), 'pin', ui('info')));
    var modes = item.modes || (item.walk_min != null && item.walk_min <= 25 ? ['walking', 'driving'] : ['driving']);
    modes.forEach(function (m, i) {
      var icon = m === 'walking' ? 'walk' : m === 'transit' ? 'bus' : 'car';
      var lbl = m === 'walking' ? ui('walk') : m === 'transit' ? ui('transit') : ui('drive');
      b.appendChild(btn(mapsDir(page.origin, item, m), icon, lbl, i === 0));
    });
    c.appendChild(b);
    return c;
  }
  function altName(name) {
    // show the Chinese name under a translated title (helps taxi drivers / locals)
    if (!name || typeof name === 'string') return '';
    if (lang === 'zh') return name.en || '';
    return name.zh || '';
  }
  function renderRoute(item, page) {
    // item: {from:{...}, name, desc, steps:[T], modes:['transit','driving'], dest?: place}
    var c = el('div', 'card route');
    var top = el('div', 'top');
    var h = el('div');
    h.appendChild(el('h3', null, esc(t(item.name))));
    var alt = altName(item.name);
    if (alt) h.appendChild(el('div', 'alt', esc(alt)));
    top.appendChild(h);
    if (item.tag) top.appendChild(el('span', 'tag', esc(t(item.tag))));
    c.appendChild(top);
    if (item.desc) c.appendChild(el('p', null, esc(t(item.desc))));
    if (item.steps && item.steps.length) {
      var ul = el('ul', 'step');
      item.steps.forEach(function (s) { ul.appendChild(el('li', null, esc(t(s)))); });
      c.appendChild(ul);
    }
    var meta = fmtDist(item);
    if (meta) c.appendChild(el('div', 'meta', meta));
    var dest = item.dest || page.dest || page.origin;
    var b = el('div', 'btns');
    (item.modes || ['transit', 'driving']).forEach(function (m, i) {
      var icon = m === 'transit' ? 'bus' : m === 'walking' ? 'walk' : 'taxi';
      var lbl = m === 'transit' ? ui('transit') : m === 'walking' ? ui('walk') : ui('taxi');
      b.appendChild(btn(mapsDir(item.from || null, dest, m), icon, lbl, i === 0));
    });
    c.appendChild(b);
    return c;
  }
  function renderTip(item) {
    var d = el('div', 'tip');
    var html = '';
    if (item.tip) html += '<b>' + esc(t(item.tip)) + '</b>';
    if (item.html) html += t(item.html); else if (item.text) html += esc(t(item.text));
    d.innerHTML = html;
    return d;
  }
  function renderInfo(item) {
    // item: {rows:[{k:T,v:T,href?}]}
    var c = el('div', 'card');
    var dl = el('dl', 'info');
    item.rows.forEach(function (r) {
      dl.appendChild(el('dt', null, esc(t(r.k))));
      var dd = el('dd');
      if (r.href) { var a = el('a', null, esc(t(r.v))); a.href = t(r.href); if (/^https?:/.test(a.href)) { a.target = '_blank'; a.rel = 'noopener'; } dd.appendChild(a); }
      else dd.innerHTML = esc(t(r.v)).replace(/\n/g, '<br>');
      dl.appendChild(dd);
    });
    c.appendChild(dl);
    return c;
  }

  function render() {
    var page = DATA.pages[slug];
    document.documentElement.lang = lang === 'zh' ? 'zh-Hant-TW' : lang;
    document.title = t(page.title) + ' · ' + t(page.client.name);
    root.innerHTML = '';

    /* header */
    var hdr = el('header', 'hdr');
    var hin = el('div', 'hdr-in');
    var brand = el('div', 'brand');
    if (page.client.logo) { var img = el('img'); img.src = page.client.logo; img.alt = t(page.client.name); brand.appendChild(img); }
    brand.appendChild(el('span', 'nm', esc(t(page.client.short || page.client.name))));
    hin.appendChild(brand);
    var langs = el('nav', 'langs');
    LANGS.forEach(function (l) {
      var bt = el('button', null, LABEL[l]);
      bt.type = 'button'; bt.setAttribute('aria-pressed', String(l === lang));
      bt.addEventListener('click', function () {
        lang = l; try { localStorage.setItem('lang', l); } catch (e) {}
        var u = new URL(location.href); u.searchParams.set('lang', l); history.replaceState(null, '', u);
        render();
      });
      langs.appendChild(bt);
    });
    hin.appendChild(langs);
    hdr.appendChild(hin);
    root.appendChild(hdr);

    var wrap = el('div', 'wrap');
    /* hero */
    var hero = el('section', 'hero');
    if (page.kicker) hero.appendChild(el('div', 'kick', esc(t(page.kicker))));
    hero.appendChild(el('h1', null, esc(t(page.title))));
    if (page.subtitle) hero.appendChild(el('p', 'sub', esc(t(page.subtitle))));
    var addr = el('p', 'addr', ICON.pin + '<span>' + esc(t(page.client.address)) + '</span>');
    var ma = el('a', null, esc(ui('map'))); ma.href = mapsSearch(page.client); ma.target = '_blank'; ma.rel = 'noopener';
    addr.appendChild(ma);
    hero.appendChild(addr);
    wrap.appendChild(hero);

    /* sections */
    page.sections.forEach(function (sec) {
      var s = el('section', 'sec');
      var count = sec.items.filter(function (i) { return i.kind === 'poi' || i.kind === 'route'; }).length;
      s.appendChild(el('h2', null, esc(t(sec.title)) + (count > 1 ? ' <span class="n">' + count + '</span>' : '')));
      var list = el('div', 'list');
      sec.items.forEach(function (item) {
        if (item.kind === 'poi') list.appendChild(renderPoi(item, page));
        else if (item.kind === 'route') list.appendChild(renderRoute(item, page));
        else if (item.kind === 'info') list.appendChild(renderInfo(item));
        else list.appendChild(renderTip(item));
      });
      s.appendChild(list);
      wrap.appendChild(s);
    });

    var foot = el('p', 'foot', esc(ui('estimate')) + (page.footer ? '<br>' + esc(t(page.footer)) : ''));
    wrap.appendChild(foot);
    root.appendChild(wrap);
    window.scrollTo(0, 0);
  }

  fetch('data.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (d) {
      DATA = d;
      if (!d.pages[slug]) throw new Error('unknown slug ' + slug);
      render();
    })
    .catch(function (e) {
      root.innerHTML = '<div class="wrap"><div class="err">' + esc(ui('loadErr')) + ' (' + esc(e.message) + ')</div></div>';
    });
})();
