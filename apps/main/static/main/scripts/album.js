/* Весільний фотоальбом: потрушування карток перед переходом + лайтбокс */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* —— Картки розділів: при натисканні легко трусяться, потім переходимо —— */
  document.querySelectorAll('.album-card').forEach(function (card) {
    card.addEventListener('click', function (e) {
      // Ctrl/Cmd/Shift-клік і середня кнопка — стандартна поведінка (нова вкладка)
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      if (reduceMotion) return;
      e.preventDefault();
      if (card.classList.contains('is-shaking')) return;
      card.classList.add('is-shaking');
      var href = card.href;
      setTimeout(function () { window.location.href = href; }, 480);
    });
  });

  // Повернення кнопкою «Назад» зі збереженої сторінки (bfcache) — прибираємо стан анімації
  window.addEventListener('pageshow', function () {
    document.querySelectorAll('.album-card.is-shaking').forEach(function (c) { c.classList.remove('is-shaking'); });
  });

  /* —— Кнопки ZIP: коротка позначка, що завантаження почалось —— */
  document.querySelectorAll('[data-download]').forEach(function (btn) {
    var label = btn.querySelector('.album-download__label');
    var initial = label ? label.textContent : '';
    btn.addEventListener('click', function () {
      if (!label || btn.classList.contains('is-started')) return;
      btn.classList.add('is-started');
      label.textContent = 'Завантаження почалось';
      setTimeout(function () {
        btn.classList.remove('is-started');
        label.textContent = initial;
      }, 3500);
    });
  });

  /* —— Лайтбокс —— */
  var box = document.querySelector('[data-lightbox]');
  var items = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox-item]'));
  if (!box || !items.length) return;

  var img = box.querySelector('.lightbox__img');
  var counter = box.querySelector('[data-lightbox-counter]');
  var download = box.querySelector('[data-lightbox-download]');
  var index = 0;
  var lastFocus = null;

  function show(i) {
    index = (i + items.length) % items.length;
    var src = items[index].getAttribute('href');
    img.classList.remove('is-loaded');
    img.onload = img.onerror = function () { img.classList.add('is-loaded'); };
    img.src = src;
    img.alt = items[index].querySelector('img').alt;
    if (img.complete && img.naturalWidth) img.classList.add('is-loaded');
    counter.textContent = (index + 1) + ' / ' + items.length;
    // завантажується оригінал у повній якості, з його початковою назвою
    download.href = items[index].dataset.original || src;
    download.setAttribute('download', items[index].dataset.name || '');
    // заздалегідь завантажуємо сусідні фото
    [index + 1, index - 1].forEach(function (n) {
      var pre = new Image();
      pre.src = items[(n + items.length) % items.length].getAttribute('href');
    });
  }

  function open(i) {
    lastFocus = document.activeElement;
    box.hidden = false;
    document.documentElement.classList.add('lightbox-open');
    show(i);
    // подвійний rAF — щоб анімація появи спрацювала після зняття hidden
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { box.classList.add('is-open'); });
    });
    box.querySelector('[data-lightbox-next]').focus({ preventScroll: true });
    // запис в історії: кнопка «Назад» (Android, свайп в iOS) закриває фото, а не сторінку
    history.pushState({ lightbox: true }, '');
  }

  function hide() {
    if (box.hidden) return;
    box.classList.remove('is-open');
    document.documentElement.classList.remove('lightbox-open');
    setTimeout(function () { box.hidden = true; img.removeAttribute('src'); }, 300);
    if (lastFocus) lastFocus.focus({ preventScroll: true });
  }

  function close() {
    if (history.state && history.state.lightbox) history.back(); // hide() викличе popstate
    else hide();
  }

  window.addEventListener('popstate', hide);

  items.forEach(function (item, i) {
    item.addEventListener('click', function (e) {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      open(i);
    });
  });

  box.querySelectorAll('[data-lightbox-close]').forEach(function (el) { el.addEventListener('click', close); });
  box.querySelector('[data-lightbox-prev]').addEventListener('click', function () { show(index - 1); });
  box.querySelector('[data-lightbox-next]').addEventListener('click', function () { show(index + 1); });

  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(index - 1);
    else if (e.key === 'ArrowRight') show(index + 1);
    else if (e.key === 'Tab') {
      // фокус лишається всередині лайтбокса
      var focusable = box.querySelectorAll('a[href], button');
      var first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  // Свайп на телефонах: вліво/вправо — гортання, вниз — закрити.
  // Щипок (2 пальці) і рух по збільшеному фото свайпом не вважаються.
  var startX = null, startY = null, multiTouch = false;
  box.addEventListener('touchstart', function (e) {
    if (e.touches.length > 1) { multiTouch = true; return; }
    multiTouch = false;
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
  }, { passive: true });
  box.addEventListener('touchend', function (e) {
    if (startX === null || e.touches.length) return;
    var zoomed = window.visualViewport && window.visualViewport.scale > 1.05;
    if (!multiTouch && !zoomed) {
      var dx = e.changedTouches[0].clientX - startX;
      var dy = e.changedTouches[0].clientY - startY;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(index + (dx < 0 ? 1 : -1));
      else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close();
    }
    startX = null;
  }, { passive: true });
})();
