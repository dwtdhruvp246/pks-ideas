# IdeaVault — Dashboard Notes Layout

This version removes the purple dashboard hero and replaces the four-wide counter row with a 2×2 counter block beside a persistent Notes panel.

## Dashboard notes

- Type directly into the Notes panel.
- Press **Enter** to save.
- Press **Shift + Enter** to insert a new line.
- You can also click **Save note**.
- Notes are stored in Supabase and sync across open devices with Realtime.
- If another device saves while you have unsaved local text, IdeaVault keeps your local text and warns you rather than overwriting it.

## Deployment

1. Run `supabase.sql` in Supabase SQL Editor. This creates the `dashboard_notes` table, RLS policies and Realtime publication entry.
2. Upload all files/folders to the GitHub repository used by Cloudflare Pages.
3. The service worker cache is bumped to `ideavault-v6`.

Existing ideas, costing, full idea pages, collapsible navigation, PWA installation and unsaved idea-editor protection remain in place.
