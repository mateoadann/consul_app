/**
 * Mobile Gestures Module
 * - Pull-to-refresh on ALL pages (reload or HTMX refresh on agenda)
 * - Swipe left/right on agenda grid to change day
 */

(() => {
  // Only run on mobile/touch devices
  if (!('ontouchstart' in window)) return;

  // === Pull-to-Refresh Configuration ===
  const PULL_THRESHOLD = 80;
  const PULL_MAX_X = 30;
  const PULL_RESISTANCE = 0.4;

  // === Pull-to-Refresh State ===
  let pullStartY = null;
  let pullStartX = null;
  let isPulling = false;
  let pullDistance = 0;

  // === Create Pull-to-Refresh Indicator (global) ===
  const pullIndicator = document.createElement('div');
  pullIndicator.className = 'pull-indicator';
  const pullSpinner = document.createElement('span');
  pullSpinner.className = 'pull-indicator-spinner';
  const pullText = document.createElement('span');
  pullText.className = 'pull-indicator-text';
  pullText.textContent = 'Soltar para actualizar';
  pullIndicator.appendChild(pullSpinner);
  pullIndicator.appendChild(pullText);
  document.body.prepend(pullIndicator);

  function isAtTop() {
    return window.scrollY <= 0;
  }

  function updatePullIndicator(distance) {
    const progress = Math.min(distance / PULL_THRESHOLD, 1);
    pullIndicator.style.transform = 'translateY(' + distance + 'px)';
    pullIndicator.classList.toggle('is-visible', distance > 10);
    pullIndicator.classList.toggle('is-ready', progress >= 1);
    pullSpinner.style.transform = 'rotate(' + (progress * 360) + 'deg)';
  }

  function resetPullIndicator() {
    pullIndicator.style.transform = 'translateY(0)';
    pullIndicator.classList.remove('is-visible', 'is-ready', 'is-refreshing');
  }

  function triggerGlobalRefresh() {
    const dateInput = document.querySelector('#agenda-fecha-input');
    if (dateInput) {
      dateInput.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      location.reload();
    }
  }

  // === Global Pull-to-Refresh Touch Handlers ===
  document.addEventListener('touchstart', (event) => {
    if (event.touches.length !== 1) return;
    const target = event.target;
    if (target instanceof Element && target.closest('input, select, textarea')) return;

    pullStartY = event.touches[0].clientY;
    pullStartX = event.touches[0].clientX;
    isPulling = isAtTop();
    pullDistance = 0;
  }, { passive: true });

  document.addEventListener('touchmove', (event) => {
    if (pullStartY === null) return;

    const dy = event.touches[0].clientY - pullStartY;
    const dx = event.touches[0].clientX - pullStartX;

    if (isPulling && dy > 0 && Math.abs(dx) < PULL_MAX_X) {
      pullDistance = dy * PULL_RESISTANCE;
      updatePullIndicator(pullDistance);
      if (pullDistance > 10) {
        event.preventDefault();
      }
    }
  }, { passive: false });

  document.addEventListener('touchend', () => {
    if (isPulling && pullDistance >= PULL_THRESHOLD) {
      pullIndicator.classList.add('is-refreshing');
      triggerGlobalRefresh();
      setTimeout(resetPullIndicator, 800);
    } else {
      resetPullIndicator();
    }
    pullStartY = null;
    pullStartX = null;
    isPulling = false;
    pullDistance = 0;
  }, { passive: true });

  // Reset on HTMX content swap
  document.body.addEventListener('htmx:afterSwap', () => {
    resetPullIndicator();
  });

  // === Agenda-specific: Swipe left/right to change day ===
  const grillaContainer = document.querySelector('#grilla-container');
  const dateInput = document.querySelector('#agenda-fecha-input');

  if (grillaContainer && dateInput) {
    const SWIPE_THRESHOLD = 80;
    const SWIPE_MAX_Y = 40;
    const SWIPE_MAX_TIME = 400;

    let swipeStartX = null;
    let swipeStartY = null;
    let swipeStartTime = null;

    const swipeIndicator = document.createElement('div');
    swipeIndicator.className = 'swipe-indicator';
    const swipeArrow = document.createElement('span');
    swipeArrow.className = 'swipe-indicator-arrow';
    swipeIndicator.appendChild(swipeArrow);
    document.body.appendChild(swipeIndicator);

    function parseIsoDate(value) {
      if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
      const [year, month, day] = value.split('-').map(Number);
      return new Date(year, month - 1, day);
    }

    function formatIsoDate(d) {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }

    function moveDay(offset) {
      const current = parseIsoDate(dateInput.value);
      if (!current) return;
      current.setDate(current.getDate() + offset);
      dateInput.value = formatIsoDate(current);
      dateInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function showSwipeIndicator(direction) {
      swipeIndicator.classList.add('is-visible', direction > 0 ? 'is-left' : 'is-right');
      setTimeout(() => {
        swipeIndicator.classList.remove('is-visible', 'is-left', 'is-right');
      }, 300);
    }

    grillaContainer.addEventListener('touchstart', (event) => {
      if (event.touches.length !== 1) return;
      const target = event.target;
      if (target instanceof Element && target.closest('a, button, input, select, label, .turno-chip')) return;
      swipeStartX = event.touches[0].clientX;
      swipeStartY = event.touches[0].clientY;
      swipeStartTime = Date.now();
    }, { passive: true });

    grillaContainer.addEventListener('touchend', (event) => {
      if (swipeStartX === null || swipeStartY === null || swipeStartTime === null) return;
      if (!event.changedTouches || event.changedTouches.length === 0) {
        swipeStartX = null;
        swipeStartY = null;
        swipeStartTime = null;
        return;
      }

      const dx = event.changedTouches[0].clientX - swipeStartX;
      const dy = event.changedTouches[0].clientY - swipeStartY;
      const dt = Date.now() - swipeStartTime;

      if (Math.abs(dx) >= SWIPE_THRESHOLD && Math.abs(dy) <= SWIPE_MAX_Y && dt <= SWIPE_MAX_TIME) {
        const direction = dx > 0 ? -1 : 1;
        showSwipeIndicator(direction);
        moveDay(direction);
      }

      swipeStartX = null;
      swipeStartY = null;
      swipeStartTime = null;
    }, { passive: true });
  }
})();
