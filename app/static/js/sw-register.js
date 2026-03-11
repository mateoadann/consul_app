// Service Worker Registration + Push Subscription

// Convert URL-safe base64 VAPID key to Uint8Array for PushManager
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Send push subscription to server
async function sendSubscriptionToServer(subscription) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
  if (!csrfToken) return;

  try {
    await fetch('/notifications/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify(subscription.toJSON()),
    });
  } catch (err) {
    console.error('Failed to send subscription to server:', err);
  }
}

// Subscribe to push notifications via PushManager
async function subscribeToPush(registration) {
  const vapidMeta = document.querySelector('meta[name="vapid-public-key"]');
  if (!vapidMeta || !vapidMeta.content) return;

  try {
    const existingSub = await registration.pushManager.getSubscription();
    if (existingSub) {
      // Already subscribed — ensure server knows
      await sendSubscriptionToServer(existingSub);
      return;
    }

    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidMeta.content),
    });

    await sendSubscriptionToServer(subscription);
  } catch (err) {
    console.error('Push subscription failed:', err);
  }
}

// Request notification permission
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

// Main: register SW, then handle push subscription if permission granted
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/sw.js')
      .then(async (registration) => {
        console.log('SW registered:', registration.scope);

        // Check for updates periodically
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);

        // If permission already granted, subscribe to push
        if ('Notification' in window && Notification.permission === 'granted') {
          await subscribeToPush(registration);
        }
      })
      .catch((error) => {
        console.error('SW registration failed:', error);
      });
  });
}

// Export for use by notification button
window.requestNotificationPermission = requestNotificationPermission;
window.subscribeToPush = subscribeToPush;
