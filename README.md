# IdeaVault PWA

Upload every file and folder in this project to the root of the GitHub repository used by Cloudflare Pages.

Required files:
- `index.html`
- `manifest.webmanifest`
- `service-worker.js`
- `icons/icon-192.png`
- `icons/icon-512.png`
- `supabase.sql`

## Install the app

After Cloudflare deploys the site over HTTPS, open it in Chrome or Edge. Use the **Install app** button in the top bar when it appears. On Android, you can also use the browser menu and select **Install app** or **Add to Home screen**. On iPhone/iPad, open the site in Safari, tap Share, then **Add to Home Screen**.

The installed PWA opens in its own app window. The interface shell can open offline, but signing in, loading ideas, saving changes, and Supabase Realtime still require an internet connection.

When changing `service-worker.js`, increase the cache name (for example, `ideavault-v2`) so installed devices receive a fresh cache.


## Stability and security fixes

This build includes defensive Supabase Realtime handling, safe channel cleanup, delegated table actions without inline JavaScript, strengthened attribute escaping, robust date/number/text sorting, and improved horizontal table scrolling on small screens. The PWA cache version was also increased so deployed clients receive the corrected files.


## Full-page idea navigation update

This version replaces the Planning / Building / Launched sidebar shortcuts with a live list of idea titles. Clicking an idea title opens that idea as a full page instead of a dialog. The New Idea buttons also open a full-page editor. The dashboard remains available through **All ideas**.

No new Supabase schema changes are required for this navigation redesign.
