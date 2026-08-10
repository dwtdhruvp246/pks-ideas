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


## My Notes workspace

A separate **My Notes** page is now available under **Workspace**. It is independent from the quick dashboard Notes box.

Each saved note has:
- Title
- Optional project/source title
- Main content
- Optional links (one per line)

The page supports creating, editing, deleting, search across title/content, unsaved-change warnings, and Supabase Realtime cross-device syncing.

Run the latest `supabase.sql` before deploying because this version creates the `personal_notes` table and its RLS/Realtime configuration. The PWA cache is `ideavault-v7`.

## v8 — Responsive My Notes editor

- My Notes now adapts to tablet and phone widths without overflowing the screen.
- The note form is collapsed by default.
- Use **+ Add note** to reveal the editor.
- Editing a saved note opens the same editor.
- Saving a new or edited note refreshes the list and automatically collapses the editor.
- **Cancel** or the × button closes the editor, with an unsaved-change warning when needed.


## Live cross-device sync (v9)

This build hardens synchronization across devices:
- Realtime subscriptions for ideas, dashboard notes, My Notes, and idea costing.
- Automatic reconnect after the app returns from the background, regains focus, or comes back online.
- A 12-second background fallback refresh while the app is visible, so data still updates if a mobile browser suspends the Realtime socket.
- Active project pages refresh automatically when there are no unsaved local edits.
- Unsaved local edits are never silently overwritten by remote changes.

Run the latest `supabase.sql` once so `idea_costs` is also included in the `supabase_realtime` publication.


## Test accounts (v10)

Each idea now has a **Test accounts** section for development/demo logins. You can add multiple entries with a username/email, password and note. Passwords are masked by default and can be shown per row. Test-account changes are included in Realtime and fallback cross-device sync.

Run the latest `supabase.sql` once to create `public.idea_test_accounts` and its RLS/Realtime configuration.

**Security:** this feature stores the supplied test passwords as database values. Use it only for low-value test/demo credentials. Do not store production passwords, personal email passwords, financial credentials, API secret keys, or other sensitive secrets.

PWA cache: `ideavault-v10`.


## v11 — editor sync stability fix

Fixed a race condition where a background sync that started just before a local edit could finish afterwards and redraw the project editor from Supabase. This was most visible when clicking **Add account** under Test Accounts: the new row could appear and then disappear.

The active idea refresh now re-checks the unsaved/saving state after all network requests finish and before changing any editor fields. Local unsaved edits therefore always win until you explicitly save or discard them.

The PWA cache is `ideavault-v11`. No database schema change is required for this fix.
