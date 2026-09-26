# PWA behaviour on iOS home screen

Both frontends are installed by users via Safari's **Add to Home Screen**:

| App | Origin | Dev port | Entry |
| --- | --- | --- | --- |
| Customer app | `app.grainstoryfarm.ca` | 3000 | `app/src/main.js` |
| Admin | `admin.grainstoryfarm.ca` | 3001 | `admin/src/main.js` |

They share `shared/pwaStandalone.js`, aliased as `@shared` in both `vite.config.js` files.

This document exists because two iOS behaviours are non-obvious and easy to
re-break. Read the two "rules" sections before touching links, headers, or the
PWA meta tags.

## 1. In-app link guard

### The iOS behaviour

On recent iOS versions, tapping a real `<a href>` inside a home-screen web app
hands the navigation to an in-app Safari window with a URL bar, back button and
refresh button, even when the link is same-origin. `router-link` renders real
anchors, so the entire side menu (admin) and bottom tab bar (customer app) used
to drop out of the installed app on every tap.

Cancelling the `click` event is **not** enough: iOS commits to the in-app browser
at touch time, before the click listener runs.

### What we do

`installInAppLinkGuard(router)` in `shared/pwaStandalone.js`, called from both
`main.js` files:

1. On `pointerdown` with `pointerType === 'touch'`, it rewrites the anchor's
   `href` to the current path. iOS then sees a same-document link and does not
   open the in-app browser.
2. On `click`, it restores the real `href`, calls `preventDefault()`, and
   navigates with `router.push()`.
3. Scroll, pointer cancel, context menu and page hide all restore the `href`.

Mouse input never gets the swap, so cmd-click, middle-click and "copy link
address" keep the real target. `vue-router`'s own handler sees `defaultPrevented`
and bails, so each tap produces exactly one navigation.

### Rules for future code

- **Do not re-add a standalone-mode gate to the guard.** It used to start with
  `if (!isStandaloneWebApp()) return`. That is exactly backwards: an icon that
  iOS already launched with browser chrome reports itself as *not* standalone, so
  the guard disabled itself on the devices that needed it and users stayed stuck.
  It now runs unconditionally; in a normal browser tab it is equivalent to the
  SPA routing those links already perform.
- **A same-origin `<a href="/...">` will be routed client-side.** If you add a
  link that must reach the server (a download route, a server-rendered page), opt
  out with `target="_blank"` or a `download` attribute, or the SPA will try to
  resolve it as a route and render nothing.
- Cross-origin links, `tel:`/`mailto:`/`sms:`, `download`, and `target` other
  than `_self` are already ignored by the guard.

## 2. Safe-area padding

Page and modal headers pad their top with a single variable, defined once per app
in `admin/src/App.vue` and `app/src/App.vue`:

```css
:root {
  --app-safe-top: env(safe-area-inset-top, 0px);
}
```

Roughly 32 views and modals consume it as
`padding-top: calc(<spacing> + var(--app-safe-top, env(safe-area-inset-top, 0px)))`.
Tune the inset globally by changing the `:root` definition rather than editing
individual files.

**Do not try to "correct" the inset from JavaScript.** An earlier attempt measured
`window.screen.height - window.innerHeight` to detect whether iOS had already
reserved the status-bar strip, and zeroed the inset when it thought so. It
guessed wrong on real devices and pushed every header under the clock. Trust
`env(safe-area-inset-top)`.

Known iOS quirk, outside our control: on some versions the system draws its own
band above the web layer while `env(safe-area-inset-top)` still reports a value,
so the gap under the status bar looks taller than intended. See
[WebKit bug 301994](https://bugs.webkit.org/show_bug.cgi?id=301994). No page-level
CSS can reclaim that band.

## 3. Install-time snapshot (why fixes don't reach existing icons)

iOS records the web app's configuration — scope, display mode, the
`apple-mobile-web-app-*` meta tags — **when the icon is created**, and never
re-reads it from the server for that icon.

Consequences a coding agent should not try to solve in code:

- Changing `index.html` or `manifest.json` only affects **new** installs and
  re-adds. Existing icons keep their old behaviour until the user deletes and
  re-adds them.
- How an icon *launches* (standalone vs. with browser chrome) is baked in. Only
  the in-session navigation behaviour can be fixed at runtime, which is what the
  link guard does.

Required in both `index.html` files, easy to drop by accident:

```html
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="viewport" content="... viewport-fit=cover">
<link rel="manifest" href="/manifest.json">
```

`mobile-web-app-capable` is the standards-track tag and does **not** replace
`apple-mobile-web-app-capable` on iOS; keep both.

Each app serves `public/manifest.json` with `"scope": "/"`, `"start_url": "/"`
and `"display": "standalone"`. The root `.gitignore` ignores `*.json`, so both
manifests carry explicit `!` un-ignore entries. Deploys copy the working
directory rather than a git checkout, so a gitignored file still ships — keep the
un-ignore anyway so the repo matches production.

## 4. Service worker updates

`admin/public/sw.js` and `app/public/sw.js` use network-first for HTML and hashed
assets, and carry a `VERSION` constant bumped by `admin/update-version.sh` and
`app/update-version.sh`. `CACHE_NAME` derives from it, so bumping the version is
what evicts old caches on activate.

Installed web apps can resume a suspended session for a long time, so after a
deploy a user may need to fully swipe the app closed and relaunch before new JS
loads. `UpdatePrompt.vue` surfaces the in-app update notification.

## 5. Testing on a real iPhone over wifi

Both dev servers listen on the LAN (`server.host: true`) and infer the HMR host
from the URL bar, so `http://<mac-lan-ip>:3000` and `:3001` work from a phone on
the same network. Find the IP with `ipconfig getifaddr en0`.

The dev API base URL follows the host in the URL bar — see `getApiBaseURL()` in
`app/src/config/api.js` and `admin/src/api/client.js` — because `localhost:5015`
on a phone means the phone itself. The Flask backend already binds `0.0.0.0` and
allows any origin.

Gotchas:

- Setting `VITE_API_BASE_URL` in `admin/.env` or `app/.env` overrides that
  inference and will point the phone at its own `localhost`. Leave it unset for
  LAN testing.
- Over plain `http` on a LAN IP the origin is insecure, so **service workers do
  not register**. Add to Home Screen and standalone mode still work, so the link
  guard and safe-area behaviour are testable; anything service-worker dependent
  is not.
- Production builds are unaffected by all of the above: the `server` block is
  dev-only, and the hostname-following branch sits behind `import.meta.env.DEV`,
  which is constant-folded out of the bundle.

Verify a production bundle never carries a dev URL:

```bash
cd admin && VITE_API_BASE_URL=https://backend.grainstoryfarm.ca/api \
  npx vite build --outDir /tmp/admin-check --emptyOutDir
grep -rl ':5015' /tmp/admin-check/assets   # expect no matches
```
