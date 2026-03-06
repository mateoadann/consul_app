// Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/sw.js')
      .then((registration) => {
        console.log('SW registered:', registration.scope);

        // Check for updates periodically
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000); // Check every hour
      })
      .catch((error) => {
        console.error('SW registration failed:', error);
      });
  });
}

// Request notification permission when user interacts
function requestNotificationPermission() {
  if (!('Notification' in window)) {
    console.log('Notifications not supported');
    return Promise.resolve('unsupported');
  }

  if (Notification.permission === 'granted') {
    return Promise.resolve('granted');
  }

  if (Notification.permission === 'denied') {
    return Promise.resolve('denied');
  }

  return Notification.requestPermission();
}

// Export for use in app.js if needed
window.requestNotificationPermission = requestNotificationPermission;
