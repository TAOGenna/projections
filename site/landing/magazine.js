// A printed issue as an object you can open and leaf through. Every page surface is a leaf: a band of thin strips
// following the curve paper makes out of the spine, with a face on each side (a right page in front, the next
// spread's left page behind), shaded by its angle to one light. Closed, the cover lies flat on a thick block; a turn
// carries one leaf over the spine, bending as it goes, its fore-edge trailing.
const W = 800, H = 1000, N = 26, RISE = 64, BLOCK = 9, CLOSED = 16;
const LIGHT = norm([-0.5, -0.32, 0.8]);
const ease = p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;

function norm(v) { const l = Math.hypot(...v); return v.map(c => c / l); }

// the resting curve of a right page: arc lengths and angles of its strips (angle 0 lies flat, pi/2 stands up)
const REST = (() => {
  const pts = [];
  for (let i = 0; i <= N; i++) {
    const t = Math.pow(i / N, 1.7);
    pts.push([t * W, RISE * (1 - Math.exp(-t / 0.11)) - 10 * t]);
  }
  const len = [], ang = [];
  for (let i = 0; i < N; i++) {
    const dx = pts[i + 1][0] - pts[i][0], dz = pts[i + 1][1] - pts[i][1];
    len.push(Math.hypot(dx, dz)); ang.push(Math.atan2(dz, dx));
  }
  const S = len.reduce((a, b) => a + b, 0), at = [];
  len.reduce((u, l) => (at.push(u), u + l), 0);
  return { len, ang, S, at };
})();
const RIGHT = REST.ang, LEFT = REST.ang.map(a => Math.PI - a), FLAT = REST.ang.map(() => 0);

class Leaf {
  constructor(parent, block = 0) {
    this.front = []; this.back = []; this.edges = [];
    for (let i = 0; i < N; i++) {
      const f = document.createElement('div'), b = document.createElement('div');
      f.className = 'strip'; b.className = 'strip';
      parent.append(f, b);
      this.front.push(f); this.back.push(b);
      if (block) for (const y of [0, H]) {  // the page block's edge beneath this strip, top and bottom
        const e = document.createElement('div');
        e.className = 'block';
        parent.append(e);
        this.edges.push([e, i, y]);
      }
    }
    this.block = block;
    if (block) { this.fore = document.createElement('div'); this.fore.className = 'block fore'; parent.append(this.fore); }
  }

  set(front, back) {  // the images on each side: a right page in front, a left page behind
    for (let i = 0; i < N; i++) { this.strip(i, 'f', front); this.strip(i, 'b', back); }
  }

  strip(i, face, src) {  // one strip's image, painted only when it changes; no image hides the strip
    const { len, S, at } = REST, el = (face === 'f' ? this.front : this.back)[i];
    if (el.dataset.src === (src || '')) return;
    el.dataset.src = src || '';
    el.style.visibility = src ? '' : 'hidden';
    el.style.backgroundImage = src ? `url(${src})` : 'none';
    el.style.backgroundSize = `${S}px ${H}px`;
    el.style.backgroundPosition = `${face === 'f' ? -at[i] : -(S - at[i] - len[i])}px 0`;
  }

  show(on) {
    for (const el of [...this.front, ...this.back, ...this.edges.map(e => e[0]), this.fore].filter(Boolean)) el.style.display = on ? '' : 'none';
  }

  // tau: each strip's angle; shadow: extra darkness near the spine (a page lifting over this one); lift: how far above
  // the stacks this leaf rides, so a turning page never fights the page beneath it for the same depth
  pose(tau, { shadow = 0, block = this.block, side = 1, lift = 0 } = {}) {
    const { len, S, at } = REST;
    const tone = v => v >= 0 ? `rgba(255,252,246,${Math.min(.3, v).toFixed(3)})` : `rgba(14,11,8,${Math.min(.7, -v).toFixed(3)})`;
    // the light on each strip's front face, then taken at the edges between strips, so the shading runs smooth
    const light = tau.map((t, i) => {
      const lit = -Math.sin(t) * LIGHT[0] + Math.cos(t) * LIGHT[2], s = at[i] / S;
      const gut = .45 * Math.max(0, 1 - s / .06) ** 1.5 + .05 * s + shadow * Math.max(0, 1 - s) ** 2;
      return [(lit - LIGHT[2]) * 1.25 - gut, (-lit - LIGHT[2]) * 1.25 - gut];  // front, and the back facing the other way
    });
    const edge = (j, f) => (light[Math.max(0, j - 1)][f] + light[Math.min(N - 1, j)][f]) / 2;
    let x = 0, z = lift;
    for (let i = 0; i < N; i++) {
      const t = tau[i], L = len[i] + 1.6;  // overlap so no seam shows between strips
      const base = `translate3d(${x.toFixed(2)}px,0,${z.toFixed(2)}px) rotateY(${(-t).toFixed(4)}rad)`;
      const f = this.front[i], b = this.back[i];
      f.style.width = b.style.width = L + 'px';
      f.style.transform = base;
      b.style.transform = `${base} translateX(${L}px) rotateY(180deg)`;
      f.style.setProperty('--t0', tone(edge(i, 0))); f.style.setProperty('--t1', tone(edge(i + 1, 0)));
      b.style.setProperty('--t0', tone(edge(i + 1, 1))); b.style.setProperty('--t1', tone(edge(i, 1)));  // the back runs the other way
      for (const [e, j, y] of this.edges) if (j === i) {
        e.style.width = L + 'px';
        e.style.height = block + 'px';
        e.style.transform = `${base} translateY(${y}px) rotateX(${side > 0 ? -90 : 90}deg)`;
      }
      x += Math.cos(t) * len[i]; z += Math.sin(t) * len[i];
    }
    if (this.fore) {
      this.fore.style.width = block + 'px';
      this.fore.style.transform = `translate3d(${x.toFixed(2)}px,0,${z.toFixed(2)}px) rotateY(90deg)`;
    }
  }
}

export function book(el, { pages, count, onchange = () => {} }) {
  const scene = document.createElement('div'), body = document.createElement('div');
  scene.className = 'mag-scene'; body.className = 'mag';
  scene.append(body); el.append(scene);
  const left = new Leaf(body, BLOCK), right = new Leaf(body, BLOCK), turning = new Leaf(body);
  const page = (k, side) => pages(k, side);
  let k = 1, busy = false;

  const preload = n => {  // decode the neighbours' pages ahead, so a revealed page is ready to paint
    for (const j of [n - 1, n, n + 1, n + 2]) if (j >= 1 && j <= count) for (const s of 'lr') {
      const img = new Image(); img.src = page(j, s); img.decode?.().catch(() => {});
    }
  };

  function settle(after) {  // the issue at rest on spread k; the turning leaf leaves once the stacks have painted
    if (after) requestAnimationFrame(() => requestAnimationFrame(() => turning.show(false))); else turning.show(false);
    if (k === 1) {  // closed: the cover lies flat on the whole block
      left.show(false);
      right.set(page(1, 'r'), null); right.pose(FLAT, { block: CLOSED }); right.show(true);
      body.style.setProperty('--open', 0);
    } else {
      left.set(null, page(k, 'l')); left.pose(LEFT, { side: -1 }); left.show(true);
      right.set(page(k, 'r'), null); right.pose(RIGHT); right.show(true);
      body.style.setProperty('--open', 1);
    }
    preload(k);
    onchange(k);
  }

  function turn(d) {
    const to = k + d;
    if (busy || to < 1 || to > count) return;
    busy = true;
    const opening = k === 1 || to === 1;  // the cover's own turn: the block flattens or rises, the issue recentres
    const [a, b] = d > 0 ? [k, to] : [to, k];  // the leaf: front = right page of a, back = left page of b
    turning.set(page(a, 'r'), page(b, 'l'));
    turning.show(true);
    left.pose(LEFT, { side: -1 }); left.show(a > 1); right.show(true);
    const LAG = .35, rest = opening ? FLAT : RIGHT, start = performance.now(), ms = opening ? 1300 : 950;
    (function frame(now) {
      const p = Math.min(1, (now - start) / ms), q = d > 0 ? p : 1 - p;
      // each strip moves a little after the one nearer the spine (forward) or the fore-edge (back): the edge trails
      // the turn, and never dips below where the page rests
      const w = REST.at.map(u => {
        const delay = LAG * (d > 0 ? u / REST.S : 1 - u / REST.S);
        return ease(Math.min(1, Math.max(0, (q - delay) / (1 - LAG))));
      });
      // under each strip of the leaf, the stack shows the leaf's own image while the two touch, and the page being
      // revealed once it has lifted: they share a depth only where they show the same thing
      for (let i = 0; i < N; i++) {
        right.strip(i, 'f', page(w[i] > .002 ? b : a, 'r'));                           // lifted: the page beneath
        left.strip(i, 'b', w[i] > .998 ? page(b, 'l') : a > 1 ? page(a, 'l') : null);  // landed: the leaf's own back
      }
      if (a === 1) left.show(w.some(v => v > .998));  // closed, there is no left side until the cover lands on it
      const tau = rest.map((r, i) => (1 - w[i]) * r + w[i] * LEFT[i]);
      if (opening) {  // the open curve grows as the cover leaves, or flattens as it returns
        const o = ease(q);
        right.pose(RIGHT.map(r => r * o), { block: CLOSED + (BLOCK - CLOSED) * o, shadow: .3 * Math.sin(Math.PI * q) });
        body.style.setProperty('--open', o);
      } else right.pose(RIGHT, { shadow: .3 * Math.sin(Math.PI * q) });
      turning.pose(tau, { lift: .5 });
      if (p < 1) requestAnimationFrame(frame);
      else { k = to; busy = false; settle(true); }
    })(start);
  }

  settle();
  // turn a little toward the pointer, eased
  let tx = 0, ty = 0, x = 0, y = 0;
  addEventListener('pointermove', e => { tx = e.clientX / innerWidth - .5; ty = e.clientY / innerHeight - .5; });
  (function tick() {
    x += (tx - x) * .05; y += (ty - y) * .05;
    body.style.setProperty('--px', x.toFixed(4)); body.style.setProperty('--py', y.toFixed(4));
    requestAnimationFrame(tick);
  })();
  return {
    next: () => turn(1), prev: () => turn(-1), close: () => { if (k > 1) { k = 2; settle(); turn(-1); } },
    get spread() { return k; },
    spine: () => right.front[0].getBoundingClientRect().left,
  };
}
