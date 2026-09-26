# Agent notes

## PWA constraints (iOS home screen)

Both frontends run as installed iOS home-screen web apps. Full background and
reasoning: [docs/PWA.md](docs/PWA.md). The load-bearing rules:

- `installInAppLinkGuard()` in `shared/pwaStandalone.js` must keep running
  unconditionally. Do not gate it on standalone detection
  (`navigator.standalone` / `display-mode: standalone`); icons that iOS launched
  with browser chrome report themselves as non-standalone, which is exactly when
  the guard is needed.
- The guard routes every same-origin `<a href>` through `vue-router`. A link
  that must reach the server needs `target="_blank"` or a `download` attribute.
- Top padding for headers comes from `--app-safe-top`, defined once per app in
  `admin/src/App.vue` and `app/src/App.vue`. Change the inset there, not in the
  ~32 consuming files, and never override `env(safe-area-inset-top)` from
  JavaScript.
- Keep `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`,
  `viewport-fit=cover` and the manifest link in both `index.html` files.
  `mobile-web-app-capable` does not replace the Apple tag on iOS.
- Both `public/manifest.json` files are un-ignored explicitly in `.gitignore`
  (which ignores `*.json`). Keep those `!` entries.

Changes to `index.html` or `manifest.json` only affect new installs; iOS bakes a
web app's configuration into the icon when the user adds it, so existing icons
keep their old behaviour until deleted and re-added.

## Local testing on a phone

Dev servers listen on the LAN and the dev API base URL follows the host in the
URL bar. Do not set `VITE_API_BASE_URL` in `admin/.env` or `app/.env` for LAN
testing — it pins the phone to its own `localhost`. Details in
[docs/PWA.md](docs/PWA.md).
