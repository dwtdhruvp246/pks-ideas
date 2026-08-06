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
