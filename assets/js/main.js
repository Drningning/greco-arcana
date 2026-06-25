// ============ Stars (hero) ============
(function makeStars(){
  const stars = document.getElementById('stars');
  if (!stars) return;
  const count = 80;
  for (let i = 0; i < count; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    s.style.left = Math.random() * 100 + '%';
    s.style.top = Math.random() * 100 + '%';
    s.style.animationDelay = (Math.random() * 4) + 's';
    s.style.animationDuration = (3 + Math.random() * 4) + 's';
    if (Math.random() > 0.7) {
      s.style.width = '3px';
      s.style.height = '3px';
    }
    stars.appendChild(s);
  }
})();

// ============ Nav scroll behavior ============
const nav = document.getElementById('nav');
if (nav) {
  window.addEventListener('scroll', () => {
    if (window.scrollY > 60) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  }, { passive: true });
}

// ============ Mobile nav toggle ============
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => navLinks.classList.toggle('mobile-open'));
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => navLinks.classList.remove('mobile-open'));
  });
}

// ============ Honors panel toggle ============
const honorsToggle = document.getElementById('honorsToggle');
const honorsPanel = document.getElementById('honorsPanel');
if (honorsToggle && honorsPanel) {
  honorsToggle.addEventListener('click', () => {
    honorsToggle.classList.toggle('open');
    honorsPanel.classList.toggle('open');
    honorsToggle.firstChild.textContent = honorsToggle.classList.contains('open')
      ? 'Hide Initiatory Honors '
      : 'View Initiatory Honors ';
  });
}

// ============ Scroll reveal ============
const reveals = document.querySelectorAll('.reveal');
if (reveals.length > 0) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
  reveals.forEach((r) => io.observe(r));
}

// ============ Form ============
function handleSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector('.form-submit');
  const original = btn.innerHTML;
  btn.innerHTML = 'Sending...';
  btn.disabled = true;
  setTimeout(() => {
    btn.innerHTML = '✓ Inquiry Received';
    setTimeout(() => {
      form.reset();
      btn.innerHTML = original;
      btn.disabled = false;
    }, 2500);
  }, 900);
  return false;
}
