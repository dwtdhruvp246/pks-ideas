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


## v19 rich text — My Notes

- My Notes Content now uses a Word-like rich-text editor when the editor CDN loads successfully.
- Supports headings, bold, italic, underline, strikethrough, bullet/numbered lists, list indentation, alignment, links, quotes, horizontal rules and tables.
- Existing plain-text notes are preserved and converted to rich HTML only when edited/saved.
- Stored HTML is sanitized before save/render.
- The original textarea remains as a graceful fallback if the rich editor cannot load.
- No Supabase schema changes are required for this stage because `personal_notes.content` is already a text column.


## v20 rich text reliability fix

- Replaced the external Tiptap/CDN dependency with a self-contained browser rich-text editor.
- My Notes formatting now works without loading third-party editor modules.
- Keeps headings, bold, italic, underline, strikethrough, lists, smart `1.` / `-` list creation, Tab/Shift+Tab indentation, alignment, links, quotes, horizontal rules, tables, undo/redo and HTML sanitization.
- No Supabase SQL changes are required.


## v21 rich text — Idea fields

- Idea **Description** now uses the same self-contained Word-like rich-text editor as My Notes.
- Idea **Private Notes** now uses the same editor and keeps its Expand/Collapse behavior.
- Rich content participates in unsaved-change detection, stale-data/manual reload protection, idea search, and dashboard previews.
- Existing plain-text Description/Private Notes remain compatible and are converted only when saved after editing.
- Run the supplied SQL manually to remove old Description/Notes length checks before storing larger formatted content.


## v22 stepped indentation

- Rich-text Indent/Outdent now moves normal text exactly 24px per step, up to 8 levels.
- List items still nest one list level at a time, preserving numbering/bullets.
- Tab / Shift+Tab uses the same one-step indentation behavior.
- Toolbar controls now clearly label Indent separately from Left/Center/Right alignment.
- Safe `margin-left` step values are preserved by HTML sanitization.
- No Supabase SQL changes are required.


## v23 numbered-list continuation

- Numbered lists now continue after an intervening bulleted detail list instead of restarting at 1.
- Example: `1. Dashboard` → bullet details → `2. Workspace`.
- Continued numbering is stored using the safe HTML `ol start` attribute and survives save/reload.
- Applied to My Notes, Idea Description, and Idea Private Notes.
- Independent numbered lists separated by normal paragraphs/headings still start at 1.
- No Supabase SQL changes are required.


## v24 numbered-list start repair

- Independent top-level numbered lists always start at 1.
- Numbering only continues across intervening bullet-detail lists.
- Real paragraph/heading section breaks reset numbering back to 1.
- Empty spacer paragraphs around bullet details do not break continuation.
- Fixes stale `start=2` values after Backspace, Enter, or typing `1.` + Space.
- Applies to My Notes, Idea Description and Private Notes.
- No Supabase SQL changes are required.


## v25 rich text — Checklist Details

- Checklist Details now uses the same self-contained Word-like rich-text editor as My Notes and Idea notes.
- Supports headings, bold, italic, underline, strikethrough, bullet/numbered lists, stepped indentation, alignment, links, quotes, horizontal rules and tables.
- Numbered-list continuation/start fixes are reused in Checklist Details.
- Formatted details render in the Checklist library and when an item is expanded inside an Idea.
- Existing plain-text checklist details remain compatible.
- No Supabase schema change is required because checklist_items.details is already an unrestricted text column.


## v26 rich text — Dashboard Notes

- Dashboard Notes now uses the same self-contained rich-text editor as My Notes, Ideas and Checklist Details.
- Enter creates normal paragraphs/list items; Ctrl/Cmd + Enter saves.
- Existing plain-text dashboard notes remain compatible.
- Dirty-state and cross-device protection continue to work with formatted HTML.
- The old 10,000-character dashboard-note database constraint is removed from the reference schema.
