// The reader: shows one spread at a time, scaled to the window. The place is kept in the URL as #s{n}, and
// remembered per issue, so reopening an issue resumes where you left off.
// Stepping to the next or previous spread turns the page: the half sheet bends over the gutter like paper.
// An address can also name a page, #p{n} (the contents links this way), or any element by its id. Typing a page
// number and Enter goes there; Home goes back to the front.
(() => {
  const deck = document.querySelector('.deck');
  const spreads = [...deck.querySelectorAll('.spread')];  // the same spreads the check measures
  const still = matchMedia('(prefers-reduced-motion: reduce)');
  let i = 0, turn = null;
  // a page is found by the folio printed on it; a page with none lies on spread n/2, two pages to a spread
  const folios = {};
  spreads.forEach((el, k) => el.querySelectorAll('.folio').forEach(f => folios[f.textContent.trim()] ??= k));
  const ofPage = p => folios[p] ?? Math.floor(p / 2);
  function fromHash() {
    const h = decodeURIComponent(location.hash.slice(1)), m = h.match(/^([sp])(\d+)$/);
    if (m) return m[1] === 's' ? +m[2] - 1 : ofPage(+m[2]);
    const el = h && document.getElementById(h);
    return el && el.closest('.spread') ? spreads.indexOf(el.closest('.spread')) : 0;
  }

  // inside a page of the same site (the landing): no desk, no margin. A frame from elsewhere, like a viewer showing
  // the issue, can't be looked into, and the issue is read there as on its own.
  const embedded = (() => { try { return top !== self && top.location.origin === location.origin; } catch { return false; } })();
  if (embedded) document.documentElement.classList.add('embedded');
  const KEY = 'projections:' + location.pathname;  // one place kept per issue; an embedded issue keeps none
  const remembered = () => { try { return parseInt(localStorage.getItem(KEY), 10) || 0; } catch { return 0; } };
  const remember = n => { if (!embedded) try { localStorage.setItem(KEY, n); } catch {} };

  // ⌘+ and ⌘− zoom into the spread, ⌘0 fits it again; zoomed, the spread follows the mouse to show what it points at
  let zoom = 1, mx = .5, my = .5;
  function fit() {
    const m = embedded ? 0 : 48;
    const s = Math.min((innerWidth - m) / 1600, (innerHeight - m) / 1000) * zoom;
    const x = (.5 - mx) * Math.max(0, 1600 * s - innerWidth), y = (.5 - my) * Math.max(0, 1000 * s - innerHeight);
    deck.style.transform = `translate(${x}px, ${y}px) scale(${s}) translate(-800px, -500px)`;
  }
  addEventListener('mousemove', e => { mx = e.clientX / innerWidth; my = e.clientY / innerHeight; if (zoom > 1) fit(); });

  // Printing (or `magazine pdf`) lays the issue out as single pages: each spread is cut at the gutter into its left
  // and right page, in reading order. The cover keeps only its right half, the front a magazine shows when closed.
  addEventListener('beforeprint', () => {
    finish();
    document.querySelector('.pages')?.remove();
    const pages = div('pages');
    spreads.forEach(s => (s.dataset.item === '_cover' ? ['r'] : ['l', 'r']).forEach(side => {
      const half = div(side), page = s.cloneNode(true);
      page.querySelectorAll('img').forEach(img => img.loading = 'eager');
      half.append(page);
      pages.append(half);
    }));
    document.body.append(pages);
    document.documentElement.classList.add('paged');
  });
  addEventListener('afterprint', () => {
    document.querySelector('.pages')?.remove();
    document.documentElement.classList.remove('paged');
  });
  function show(n) {
    finish();
    i = Math.max(0, Math.min(spreads.length - 1, n));
    spreads.forEach((el, k) => el.classList.toggle('on', k === i));
    if (location.hash !== '#s' + (i + 1)) history.replaceState(null, '', '#s' + (i + 1));
    remember(i);
    warm(i);
  }
  // decode the neighbours' images in idle time, so a turn never waits on a picture being decoded
  function warm(n) {
    const go = () => [n + 1, n - 1, n + 2].forEach(k => spreads[k] && spreads[k].querySelectorAll('img').forEach(img => {
      img.loading = 'eager';
      if (img.decode) img.decode().catch(() => {});
    }));
    window.requestIdleCallback ? requestIdleCallback(go, {timeout: 400}) : setTimeout(go, 50);
  }

  // The turning half sheet is cut into vertical strips, each a clipped clone of the spread on its front and of the
  // spread underneath on its back. The strips are chained edge to edge, each at its own angle, so the sheet bends:
  // the outer edge lifts first and lands last. Strips narrow toward the outer edge, where the paper curls most.
  const EDGES = [0, 202, 364, 494, 598, 681, 747, 800];  // strip edges, px out from the gutter
  const MS = 800, P = 8000;                                 // turn length; perspective (deck px), as in reader.css
  const LX = -.34, LZ = .94;                                // light: from the viewer, a little toward the far page
  const div = cls => Object.assign(document.createElement('div'), {className: cls});
  const ease = (a, b, x) => (x = Math.min(1, Math.max(0, (x - a) / (b - a)))) * x * (3 - 2 * x);
  // the side of the sheet the viewer sees at angle a, against flat paper: darker turned away, lighter toward the light
  function tone(a, back) {
    const b = (back ? -1 : 1) * (Math.cos(a) - Math.sin(a) * LX / LZ);
    return b < 1 ? `rgba(0,0,0,${Math.min(.45, (1 - b) * .35).toFixed(3)})`
                 : `rgba(255,255,255,${Math.min(.12, (b - 1) * 1.5).toFixed(3)})`;
  }

  function step(d) {  // d = 1 forward (the right page turns), -1 back (the left page turns): mirror images
    finish();
    const to = i + d;
    if (to < 0 || to >= spreads.length) return;
    if (still.matches) return show(to);
    const from = spreads[i], under = spreads[to], layer = div('turn'), sheet = div('sheet');
    const spine = div('spine'), shadows = [div('cast'), div('cast')];  // on the uncovered page, on the far page
    shadows.forEach((s, k) => s.style.background =
      `linear-gradient(to ${(d > 0) === !k ? 'right' : 'left'}, #000, rgba(0,0,0,.3) 30%, transparent)`);
    layer.setAttribute('aria-hidden', 'true');
    layer.append(spine, ...shadows, sheet);
    const strips = EDGES.slice(1).map((b, k) => {
      const a = EDGES[k], w = b - a + (b < 800 ? 1 : 0);  // 1px overlap so no seam shows between strips
      const strip = div('strip'), near = 800 + a, far = 800 - a - w;  // where the strip lies flat, and after the turn
      strip.style.cssText = `left:${d > 0 ? 800 : 800 - w}px;width:${w}px;transform-origin:${d > 0 ? 'left' : 'right'}`;
      const shades = [[from, d > 0 ? near : far, 'face'], [under, d > 0 ? far : near, 'face back']].map(([src, x, cls]) => {
        const face = div(cls), page = src.cloneNode(true), shade = div('shade');
        page.classList.remove('on');
        page.style.left = -x + 'px';
        face.append(page, shade);
        strip.append(face);
        return shade;
      });
      sheet.append(strip);
      return {strip, shades, w: b - a, s: (a + b) / 1600};
    });
    under.classList.add(d > 0 ? 'under-r' : 'under-l');
    deck.append(layer);

    const pose = t => {
      // The outer edge lifts quickly and lands last; the gutter side follows late. So the sheet curls up from its
      // edge, arches over the gutter, and trails its edge as it settles.
      const near = ease(.2, .85, t), edge = .85 * (1 - (1 - Math.min(1, t / .55)) ** 2) + .15 * ease(.55, 1, t);
      const th = strips.map(p => Math.PI * (near + (edge - near) * p.s ** 1.3));
      const at = j => (th[Math.min(j, th.length - 1)] + th[Math.max(j - 1, 0)]) / 2;  // angle at strip edge j
      const crease = `rgba(0,0,0,${(.3 * Math.sin(th[0])).toFixed(3)}), `;           // the fold at the gutter
      let x = 0, z = 0, lo = [0, 0], hi = [0, 0];  // projected sheet extent, with the height there
      strips.forEach((p, k) => {
        p.strip.style.transform = `translate3d(${d * x}px,0,${z}px) rotateY(${-d * th[k]}rad)`;
        p.shades.forEach((sh, f) => {  // shading runs across each strip from its inner to its outer edge
          const out = (f === 0) === (d > 0) ? 'right' : 'left';
          sh.style.background = k ? `linear-gradient(to ${out}, ${tone(at(k), f)}, ${tone(at(k + 1), f)})`
                                  : `linear-gradient(to ${out}, ${crease}${tone(at(k), f)} 36px, ${tone(at(k + 1), f)})`;
        });
        x += p.w * Math.cos(th[k]); z += p.w * Math.sin(th[k]);
        const X = x * P / (P - z);
        if (X > hi[0]) hi = [X, z];
        if (X < lo[0]) lo = [X, z];
      });
      [hi, lo].forEach(([X, h], k) => {  // soft shadow beside the sheet, wider and fainter the higher it floats
        const w = 24 + h * .7, s = shadows[k].style;
        s.opacity = (Math.min(.45, h / 60) * (1 - Math.min(.6, h / 1200))).toFixed(3);
        s.width = w + 'px';
        s.left = (d * (k ? -1 : 1) > 0 ? 800 + d * X : 800 + d * X - w) + 'px';
      });
      spine.style.opacity = Math.sin(th[0]).toFixed(3);
    };
    pose(0);
    let t0;
    const tick = now => {
      const t = Math.min(1, (now - (t0 ??= now)) / MS);
      pose(t);
      if (t < 1) turn.raf = requestAnimationFrame(tick); else finish();
    };
    // the clock starts a frame late, once the clones are drawn, so their first paint doesn't eat into the turn
    turn = {to, layer, under, raf: requestAnimationFrame(() => turn.raf = requestAnimationFrame(tick))};
  }
  function finish() {  // ends a turn at once: its clones go and the new spread shows
    if (!turn) return;
    const {to, layer, under, raf} = turn;
    turn = null;
    cancelAnimationFrame(raf);
    layer.remove();
    under.classList.remove('under-r', 'under-l');
    show(to);
  }

  // typing a page number: the digits show at the foot of the window, Enter goes there, Escape lets it go
  const ask = Object.assign(div('goto'), {hidden: true});
  document.body.append(ask);
  let typed = '', idle;
  const type = s => {
    typed = s.slice(0, 4);
    ask.hidden = !typed;
    ask.textContent = `Page ${typed}`;
    clearTimeout(idle);
    if (typed) idle = setTimeout(() => type(''), 5000);
  };

  addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && ['=', '+', '-', '0'].includes(e.key)) {
      zoom = e.key === '0' ? 1 : Math.min(4, Math.max(1, zoom * (e.key === '-' ? 1 / 1.25 : 1.25)));
      fit();
      return e.preventDefault();
    }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (/^\d$/.test(e.key)) type(typed + e.key);
    else if (typed && e.key === 'Backspace') type(typed.slice(0, -1));
    else if (typed && e.key === 'Enter') { show(ofPage(+typed)); type(''); }
    else if (typed && e.key === 'Escape') type('');
    else if (['ArrowRight', ' ', 'PageDown'].includes(e.key)) step(1);
    else if (['ArrowLeft', 'PageUp'].includes(e.key)) step(-1);
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(spreads.length - 1);
    else if (e.key === 'Escape' && embedded) parent.postMessage('projections:close', '*');  // the page around it closes it
    else return;
    e.preventDefault();
  });
  addEventListener('click', e => {
    if (e.target.closest('.runhead.l')) {  // the masthead goes back to the contents; Back returns here
      location.hash = 's' + (spreads.findIndex(s => s.dataset.item === '_contents') + 1 || 1);
      return;
    }
    if (e.target.closest('a, button, input, summary, video')) return;
    if (getSelection().toString()) return;  // the end of a drag that selected text: the page stays
    step(e.clientX > innerWidth / 2 ? 1 : -1);
  });
  addEventListener('hashchange', () => show(fromHash()));
  addEventListener('resize', fit);
  fit();
  show(location.hash || embedded ? fromHash() : remembered());  // an address wins; otherwise where you left off
})();
