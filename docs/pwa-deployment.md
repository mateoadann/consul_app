# PWA Deployment Guide

ConsulApp is configured as a Progressive Web App (PWA), enabling installation on mobile devices and offline functionality.

## Features

- **Installable**: Users can add ConsulApp to their home screen
- **Offline Support**: Static assets are cached for offline access
- **Push Notifications**: Infrastructure ready for future push notifications

## Files

| File | Purpose |
|------|---------|
| `app/static/manifest.json` | Web App Manifest with app metadata |
| `app/static/sw.js` | Service Worker for caching and offline |
| `app/static/js/sw-register.js` | Service Worker registration |
| `app/static/icons/icon-192.png` | PWA icon (192x192) |
| `app/static/icons/icon-512.png` | PWA icon (512x512) |
| `app/static/icons/apple-touch-icon.png` | iOS home screen icon |

## Caching Strategy

The Service Worker uses different strategies based on content type:

- **HTML pages**: Network-first with cache fallback (ensures fresh content)
- **Static assets**: Cache-first with network fallback (fast loading)
- **Fonts**: Cached for offline use

## Installation

### Android (Chrome)
1. Visit the app in Chrome
2. Tap the "Add to Home Screen" prompt or menu option
3. App appears on home screen with full-screen experience

### iOS (Safari)
1. Visit the app in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. App appears on home screen

## Cache Versioning

To update cached assets, increment `CACHE_NAME` in `sw.js`:

```javascript
const CACHE_NAME = 'consulapp-v2';  // Was v1
```

The Service Worker will automatically clean old caches on activation.

## Testing PWA

### Lighthouse Audit
1. Open Chrome DevTools
2. Go to Lighthouse tab
3. Check "Progressive Web App"
4. Run audit

### Service Worker Status
1. Open Chrome DevTools
2. Go to Application tab
3. Check "Service Workers" section

### Cache Contents
1. Open Chrome DevTools > Application
2. Expand "Cache Storage"
3. View cached resources

## Push Notifications (Future)

The infrastructure is ready for push notifications:

1. `sw.js` has push event handler
2. `sw-register.js` exposes `requestNotificationPermission()`

To enable:
1. Set up a push notification service (e.g., Firebase Cloud Messaging)
2. Implement subscription endpoint in backend
3. Call `requestNotificationPermission()` on user action

## Icons

Current icons are placeholder solid-color images. Replace with actual branded icons:

- `icon-192.png`: 192x192 PNG, used for Android home screen
- `icon-512.png`: 512x512 PNG, used for splash screen
- `apple-touch-icon.png`: 180x180 PNG, used for iOS home screen

Icons should have `purpose: "any maskable"` support (safe zone in center).

## HTTPS Requirement

Service Workers require HTTPS in production. Development on `localhost` works without HTTPS.
