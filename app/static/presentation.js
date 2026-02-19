const slides = document.querySelectorAll('.slide');
let current = 0;
const total = slides.length;

function show(idx) {
  slides.forEach((s, i) => {
    s.classList.remove('active', 'prev');
    if (i === idx) s.classList.add('active');
    else if (i < idx) s.classList.add('prev');
  });
  current = idx;
  document.querySelector('.counter').textContent = `${idx + 1} / ${total}`;
  document.querySelector('.progress-bar').style.width = `${((idx + 1) / total) * 100}%`;
}

function next() { if (current < total - 1) show(current + 1); }
function prev() { if (current > 0) show(current - 1); }

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); next(); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
  if (e.key === 'Home') { e.preventDefault(); show(0); }
  if (e.key === 'End') { e.preventDefault(); show(total - 1); }
});

// Touch support
let touchStartX = 0;
document.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; });
document.addEventListener('touchend', e => {
  const diff = touchStartX - e.changedTouches[0].clientX;
  if (Math.abs(diff) > 50) { diff > 0 ? next() : prev(); }
});

show(0);
