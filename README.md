# IdeaVault v14 — My Notes Categories

This version adds categories and category filtering to the **My Notes** workspace.

## New features

- Optional **Category** dropdown when adding or editing a My Notes entry.
- The last dropdown option is **＋ Add category…**.
- Selecting it opens a small inline category creator; no modal is used.
- Categories are saved to Supabase and sync between devices.
- Saved notes display their category as a badge.
- The Saved Notes search now has a **Filter** button.
- The filter panel lets you filter notes by category while still searching title/content.
- **Clear filter** returns to all categories.

## Required Supabase step

Run the included `supabase.sql` once in Supabase SQL Editor. It:

1. Adds the optional `category` column to `personal_notes`.
2. Creates `personal_note_categories`.
3. Adds RLS policies restricted to the signed-in owner.
4. Enables Realtime for the categories table.

The migration uses `IF NOT EXISTS`/safe policy recreation where appropriate and can be run over the existing IdeaVault schema.

## PWA

The service-worker cache is `ideavault-v14`.
