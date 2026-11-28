/* Greco Arcana: dropdown menus (Investigations, Study the Mysteries).
   Hover and keyboard focus already open the menus through CSS (nav-v2.css).
   This adds: aria-expanded state for screen readers, Escape to close,
   and tap-to-open on touch screens wide enough to show the desktop menu. */
(function () {
  var items = document.querySelectorAll('.nav-links .nav-has-menu');
  if (!items.length) return;
  var wide = window.matchMedia('(min-width: 961px)');
  var coarse = window.matchMedia('(hover: none)');

  function setOpen(li, open) {
    li.classList.toggle('is-open', open);
    var a = li.querySelector(':scope > a');
    if (a) a.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function closeAll(except) {
    items.forEach(function (li) { if (li !== except) setOpen(li, false); });
  }

  items.forEach(function (li) {
    var a = li.querySelector(':scope > a');
    var menu = li.querySelector('.nav-submenu');
    if (!a || !menu) return;
    if (!menu.id) menu.id = 'submenu-' + Math.random().toString(36).slice(2, 8);
    a.setAttribute('aria-haspopup', 'true');
    a.setAttribute('aria-controls', menu.id);
    a.setAttribute('aria-expanded', 'false');

    li.addEventListener('mouseenter', function () { if (wide.matches) setOpen(li, true); });
    li.addEventListener('mouseleave', function () { if (wide.matches) setOpen(li, false); });
    li.addEventListener('focusin', function () { if (wide.matches) { closeAll(li); setOpen(li, true); } });
    li.addEventListener('focusout', function (ev) {
      if (!li.contains(ev.relatedTarget)) setOpen(li, false);
    });
    a.addEventListener('click', function (ev) {
      // On a touch screen showing the desktop menu, the first tap opens the menu.
      if (wide.matches && coarse.matches && !li.classList.contains('is-open')) {
        ev.preventDefault();
        closeAll(li);
        setOpen(li, true);
      }
    });
    li.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') {
        setOpen(li, false);
        a.focus();
        // keep focus on the parent link but hide the menu until the user moves on
        li.classList.add('is-dismissed');
      } else if (ev.key === 'ArrowDown' && ev.target === a) {
        ev.preventDefault();
        setOpen(li, true);
        var first = menu.querySelector('a');
        if (first) first.focus();
      }
    });
    li.addEventListener('focusout', function () { li.classList.remove('is-dismissed'); });
  });
  document.addEventListener('click', function (ev) {
    if (!ev.target.closest('.nav-has-menu')) closeAll(null);
  });
})();
