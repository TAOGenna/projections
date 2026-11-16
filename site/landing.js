// What every landing page shares: scaling the 1600 × 1000 page to the window, opening the issue over it at a
// spread (any element with data-s="N"), and the copy link.
const canvas = document.querySelector('.canvas');
const fit = () => {
  const s = Math.min(innerWidth / 1600, innerHeight / 1000);
  canvas.style.transform = `translate(-50%, -50%) scale(${s})`;
  document.documentElement.style.setProperty('--s', s);  // for what lies outside the page and still follows it
};
addEventListener('resize', fit);
fit();

const box = document.createElement('div');
box.className = 'lightbox';
box.innerHTML = '<button class="lb-close">Close</button><div class="lb-reader"><iframe title="Projections Nº 00, a sample issue"></iframe></div>'
  + '<div class="lb-hint">← → to turn · Esc to close</div>';
document.body.append(box);
const frame = box.querySelector('iframe');
const close = () => box.classList.remove('on');
function openIssue(n) {
  frame.onload = () => frame.focus();
  frame.src = 'sample/index.html#s' + n;
  box.classList.add('on');
}
document.addEventListener('click', e => {
  const t = e.target.closest('[data-s]');
  if (t) openIssue(t.dataset.s);
});
box.querySelector('.lb-close').onclick = close;
box.addEventListener('click', e => { if (e.target === box) close(); });
addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
addEventListener('message', e => { if (e.data === 'projections:close') close(); });  // Esc pressed inside the issue

for (const b of document.querySelectorAll('.copy')) b.onclick = async () => {
  const text = b.closest('.setup').querySelector('pre').textContent.replace(/^\$ /gm, '');  // the commands, not the prompts
  try { await navigator.clipboard.writeText(text); b.textContent = 'Copied'; }
  catch { b.textContent = 'Select it'; }
  setTimeout(() => { b.textContent = 'Copy'; }, 1600);
};
