/**
 * Mobile Gestures Module
 * - Swipe left/right on agenda grid to change day
 * - Pull-to-refresh to reload agenda
 */

(() => {
  // Only run on mobile/touch devices
  if (!('ontouchstart' in window)) return;

  const grillaContainer = document.querySelector('#grilla-container');
  const agendaFilters = document.querySelector('#agenda-filters');
  const dateInput = document.querySelector('#agenda-fecha-input');

  if (!grillaContainer || !agendaFilters || !dateInput) return;

  // === Swipe Configuration ===
  const SWIPE_THRESHOLD = 80;   // Minimum horizontal distance
  const SWIPE_MAX_Y = 40;       // Maximum vertical deviation
  const SWIPE_MAX_TIME = 400;   // Maximum gesture duration (ms)

  // === Pull-to-Refresh Configuration ===
  const PULL_THRESHOLD = 80;    // Minimum pull distance to trigger refresh
  const PULL_MAX_X = 30;        // Maximum horizontal deviation
  const PULL_RESISTANCE = 0.4;  // Pull resistance factor

  // === State ===
  let touchStartX = null;
  let touchStartY = null;
  let touchStartTime = null;
  let isPulling = false;
  let pullDistance = 0;

  // === Create Swipe Indicator Element ===
  const swipeIndicator = document.createElement('div');
  swipeIndicator.className = 'swipe-indicator';
  const swipeArrow = document.createElement('span');
  swipeArrow.className = 'swipe-indicator-arrow';
  swipeIndicator.appendChild(swipeArrow);
  document.body.appendChild(swipeIndicator);

  // === Create Pull-to-Refresh Indicator ===
  const pullIndicator = document.createElement('div');
  pullIndicator.className = 'pull-indicator';
  const pullSpinner = document.createElement('span');
  pullSpinner.className = 'pull-indicator-spinner';
  const pullText = document.createElement('span');
  pullText.className = 'pull-indicator-text';
  pullText.textContent = 'Soltar para actualizar';
  pullIndicator.appendChild(pullSpinner);
  pullIndicator.appendChild(pullText);
  grillaContainer.parentElement.insertBefore(pullIndicator, grillaContainer);

  // === Helpers ===
  function parseIsoDate(value) {
    if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const [year, month, day] = value.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  function formatIsoDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function moveDay(offset) {
    const current = parseIsoDate(dateInput.value);
    if (!current) return;
    current.setDate(current.getDate() + offset);
    dateInput.value = formatIsoDate(current);
    dateInput.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function triggerRefresh() {
    // Trigger the HTMX request by dispatching change event
    dateInput.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function showSwipeIndicator(direction) {
    swipeIndicator.classList.add('is-visible', direction > 0 ? 'is-left' : 'is-right');
    setTimeout(() => {
      swipeIndicator.classList.remove('is-visible', 'is-left', 'is-right');
    }, 300);
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

  function isAtTop() {
    return window.scrollY <= 0;
  }

  // === Touch Event Handlers ===
  function handleTouchStart(event) {
    if (event.touches.length !== 1) return;

    const target = event.target;
    if (target instanceof Element && target.closest('a, button, input, select, label, .turno-chip')) {
      return;
    }

    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
    touchStartTime = Date.now();
    isPulling = isAtTop();
    pullDistance = 0;
  }

  function handleTouchMove(event) {
    if (touchStartX === null || touchStartY === null) return;

    const currentX = event.touches[0].clientX;
    const currentY = event.touches[0].clientY;
    const dx = currentX - touchStartX;
    const dy = currentY - touchStartY;

    // Check for pull-to-refresh (pulling down when at top)
    if (isPulling && dy > 0 && Math.abs(dx) < PULL_MAX_X) {
      pullDistance = dy * PULL_RESISTANCE;
      updatePullIndicator(pullDistance);

      if (pullDistance > 10) {
        event.preventDefault();
      }
    }
  }

  function handleTouchEnd(event) {
    if (touchStartX === null || touchStartY === null || touchStartTime === null) return;
    if (!event.changedTouches || event.changedTouches.length === 0) {
      resetState();
      return;
    }

    const dx = event.changedTouches[0].clientX - touchStartX;
    const dy = event.changedTouches[0].clientY - touchStartY;
    const dt = Date.now() - touchStartTime;

    // Check for pull-to-refresh
    if (isPulling && pullDistance >= PULL_THRESHOLD) {
      pullIndicator.classList.add('is-refreshing');
      triggerRefresh();
      setTimeout(resetPullIndicator, 800);
      resetState();
      return;
    }

    // Reset pull indicator
    resetPullIndicator();

    // Check for horizontal swipe
    if (Math.abs(dx) >= SWIPE_THRESHOLD && Math.abs(dy) <= SWIPE_MAX_Y && dt <= SWIPE_MAX_TIME) {
      const direction = dx > 0 ? -1 : 1;  // swipe right = previous day, swipe left = next day
      showSwipeIndicator(direction);
      moveDay(direction);
    }

    resetState();
  }

  function resetState() {
    touchStartX = null;
    touchStartY = null;
    touchStartTime = null;
    isPulling = false;
    pullDistance = 0;
  }

  // === Event Listeners ===
  grillaContainer.addEventListener('touchstart', handleTouchStart, { passive: true });
  grillaContainer.addEventListener('touchmove', handleTouchMove, { passive: false });
  grillaContainer.addEventListener('touchend', handleTouchEnd, { passive: true });

  // Reset on HTMX content swap
  document.body.addEventListener('htmx:afterSwap', (event) => {
    if (event.detail.target === grillaContainer) {
      resetPullIndicator();
    }
  });
})();
