/* Greco Arcana: The Occult Archives (v1)
   Reading progress, table-of-contents highlighting and catalogue filters.
   Everything works without this file; it only enhances. */
(function () {
  'use strict';

  /* ---------- reading progress ---------- */
  var bar = document.querySelector('.ga-progress span');
  var article = document.querySelector('[data-progress]');
  if (bar && article) {
    var ticking = false;
    var update = function () {
      var r = article.getBoundingClientRect();
      var total = r.height - window.innerHeight * 0.6;
      var done = Math.min(1, Math.max(0, -r.top / (total > 0 ? total : 1)));
      bar.style.transform = 'scaleX(' + done.toFixed(4) + ')';
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { window.requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* ---------- table of contents: mark the current section ---------- */
  var tocLinks = document.querySelectorAll('.ga-toc a');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          tocLinks.forEach(function (a) { a.classList.remove('is-current'); a.removeAttribute('aria-current'); });
          var link = map[en.target.id];
          if (link) { link.classList.add('is-current'); link.setAttribute('aria-current', 'location'); }
        }
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    Object.keys(map).forEach(function (id) { var h = document.getElementById(id); if (h) io.observe(h); });
  }

  /* ---------- catalogue filters ---------- */
  var form = document.querySelector('[data-filters]');
  if (form) {
    form.hidden = false;
    var items = Array.prototype.slice.call(document.querySelectorAll('.ga-item'));
    var groups = Array.prototype.slice.call(document.querySelectorAll('.ga-collection'));
    var out = form.querySelector('[data-shown]');
    var selects = form.querySelectorAll('select[data-filter]');
    var apply = function () {
      var want = {};
      selects.forEach(function (s) { want[s.getAttribute('data-filter')] = s.value; });
      var shown = 0;
      items.forEach(function (li) {
        var ok = (!want.type || li.dataset.type === want.type) &&
                 (!want.tradition || li.dataset.tradition === want.tradition) &&
                 (!want.status || li.dataset.status === want.status);
        li.hidden = !ok;
        if (ok) shown++;
      });
      groups.forEach(function (g) {
        var visible = g.querySelectorAll('.ga-item:not([hidden])').length;
        var count = g.querySelector('[data-count]');
        if (count) count.textContent = visible;
        var empty = g.querySelector('.ga-empty');
        if (empty) empty.hidden = visible !== 0;
      });
      if (out) out.textContent = 'Showing ' + shown + ' of ' + items.length;
    };
    selects.forEach(function (s) { s.addEventListener('change', apply); });
    form.addEventListener('reset', function () { setTimeout(apply, 0); });
  }
})();
