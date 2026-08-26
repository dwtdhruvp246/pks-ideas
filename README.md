# Pks Ideas v15

This release adds guarded multi-device stale-data detection for open Idea pages.

## Deploy
1. Replace your website files with this package.
2. Run `supabase.sql` once in Supabase SQL Editor. It is written to be safe for an existing database.
3. Deploy through GitHub / Cloudflare Pages.
4. Fully close and reopen the installed PWA once so the `pks-ideas-v15` service worker takes over.

## Multi-device behavior
- Open Idea pages are never silently replaced by background sync.
- Focus, wake, online, fallback sync, and Realtime only check whether `ideas.updated_at` is newer.
- If newer, an inline warning appears.
- Reloading server data happens only after an explicit user action.
- Saving stale data opens a conflict dialog with Cancel, Reload latest data, and Save anyway.
- Changes to Costing and Test Accounts update the parent Idea timestamp so they also trigger stale detection.

## Also retained
- Pks Ideas branding
- expandable Dashboard Notes
- expandable My Notes editor
- expandable Idea Private Notes
- no automatic Idea-title focus on open
- no browser-side character limits on Dashboard Notes, My Notes content, or Idea Private Notes
- My Notes categories and filtering
- unsaved-change guards
