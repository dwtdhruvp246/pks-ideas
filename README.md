# IdeaVault — Collapsible Navigation PWA

This version changes the left navigation into a collapsible drawer on desktop and mobile.

## Navigation behavior

- The sidebar is collapsed by default.
- Use the ☰ button in the top-left to open it.
- Selecting **All ideas** or an idea title navigates to that page and closes the sidebar.
- Clicking outside the sidebar closes it.
- Pressing **Escape** closes it.
- Clicking the currently open idea closes the sidebar without reloading the idea.
- Existing unsaved-change protection remains active. If navigation is cancelled because of unsaved changes, the page is not changed.

## Deployment

Upload all project files to the GitHub repository used by Cloudflare Pages. The service-worker cache is bumped to `ideavault-v5`.

No new Supabase SQL is required for this UI change.
