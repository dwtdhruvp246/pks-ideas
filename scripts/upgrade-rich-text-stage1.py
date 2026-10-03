from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# 1) Styling for the reusable rich-text editor used by My Notes in stage 1.
# -----------------------------------------------------------------------------
rich_css = r'''

    /* Rich text editor — Stage 1: My Notes */
    .rich-editor-shell { min-width:0; }
    .rich-editor-toolbar,
    .rich-editor-surface { display:none; }
    .rich-editor-shell.ready {
      border:1px solid var(--border); border-radius:12px; overflow:hidden; background:white;
      transition:border-color .18s ease, box-shadow .18s ease;
    }
    .rich-editor-shell.ready:focus-within {
      border-color:var(--primary); box-shadow:0 0 0 4px rgba(91,91,214,.10);
    }
    .rich-editor-shell.ready > #myNoteContent { display:none; }
    .rich-editor-shell.ready .rich-editor-toolbar {
      display:flex; align-items:center; gap:5px; padding:8px; overflow-x:auto; white-space:nowrap;
      background:#f8fafc; border-bottom:1px solid var(--border); scrollbar-width:thin;
    }
    .rich-editor-shell.ready .rich-editor-surface { display:block; }
    .rich-editor-toolbar-group { display:inline-flex; align-items:center; gap:4px; padding-right:5px; border-right:1px solid var(--border); }
    .rich-editor-toolbar-group:last-child { border-right:0; padding-right:0; }
    .rich-tool-button {
      flex:0 0 auto; min-width:34px; min-height:34px; padding:6px 8px; border:1px solid transparent;
      border-radius:8px; background:transparent; color:#374151; font-weight:700; font-size:12px;
    }
    .rich-tool-button:hover { background:white; border-color:var(--border); color:var(--primary); }
    .rich-tool-button.active { background:#eef2ff; border-color:#c7d2fe; color:#4338ca; }
    .rich-tool-button:disabled { opacity:.35; cursor:not-allowed; }
    .rich-tool-select {
      width:auto; min-width:118px; height:34px; padding:4px 30px 4px 9px; border-radius:8px; font-size:12px;
      background:white;
    }
    .rich-editor-surface .tiptap {
      min-height:250px; padding:14px; outline:none; color:var(--text); line-height:1.65; overflow-wrap:anywhere;
    }
    .rich-editor-surface .tiptap p { margin:0 0 .8em; }
    .rich-editor-surface .tiptap p:last-child { margin-bottom:0; }
    .rich-editor-surface .tiptap h1 { font-size:1.65rem; margin:1em 0 .55em; }
    .rich-editor-surface .tiptap h2 { font-size:1.35rem; margin:1em 0 .5em; }
    .rich-editor-surface .tiptap h3 { font-size:1.12rem; margin:.9em 0 .45em; }
    .rich-editor-surface .tiptap ul,
    .rich-editor-surface .tiptap ol { margin:.65em 0 .85em; padding-left:1.65rem; }
    .rich-editor-surface .tiptap li { margin:.2em 0; }
    .rich-editor-surface .tiptap blockquote {
      margin:.9em 0; padding:.25em 0 .25em 14px; border-left:3px solid #c7d2fe; color:#4b5563;
    }
    .rich-editor-surface .tiptap hr { border:0; border-top:1px solid var(--border); margin:1.2em 0; }
    .rich-editor-surface .tiptap a,
    .saved-note-content a { color:var(--primary); text-decoration:underline; }
    .rich-editor-surface .tiptap table,
    .saved-note-content table {
      width:100%; border-collapse:collapse; table-layout:fixed; margin:1em 0; overflow:hidden;
    }
    .rich-editor-surface .tiptap th,
    .rich-editor-surface .tiptap td,
    .saved-note-content th,
    .saved-note-content td {
      border:1px solid #cfd4dc; padding:8px 9px; vertical-align:top; min-width:70px;
    }
    .rich-editor-surface .tiptap th,
    .saved-note-content th { background:#f8fafc; font-weight:800; }
    .rich-editor-surface .tiptap .selectedCell { background:#eef2ff; }
    .rich-editor-hint { margin:7px 0 0; color:var(--muted); font-size:11px; }
    .rich-editor-load-note { display:none; }
    .rich-editor-shell.loading + .rich-editor-load-note { display:block; color:var(--muted); font-size:11px; margin-top:6px; }

    .my-note-editor.expanded .rich-editor-surface .tiptap { min-height:min(60vh, 680px); }

    .saved-note-content { white-space:normal; }
    .saved-note-content p { margin:0 0 .75em; }
    .saved-note-content p:last-child { margin-bottom:0; }
    .saved-note-content h1,
    .saved-note-content h2,
    .saved-note-content h3 { margin:.9em 0 .45em; color:var(--text); }
    .saved-note-content ul,
    .saved-note-content ol { margin:.6em 0 .8em; padding-left:1.55rem; }
    .saved-note-content blockquote { margin:.8em 0; padding-left:12px; border-left:3px solid #c7d2fe; }
    .saved-note-content hr { border:0; border-top:1px solid var(--border); margin:1em 0; }

    @media (max-width:560px) {
      .rich-editor-toolbar { -webkit-overflow-scrolling:touch; }
      .rich-tool-button { min-width:38px; min-height:38px; font-size:13px; }
      .rich-tool-select { min-width:110px; height:38px; }
      .rich-editor-surface .tiptap { min-height:220px; padding:13px; }
      .my-note-editor.expanded .rich-editor-surface .tiptap { min-height:64vh; }
    }
'''

html = replace_once(
    html,
    '\n\n\n    /* Checklist workspace + per-idea checklist */',
    rich_css + '\n\n    /* Checklist workspace + per-idea checklist */',
    'rich editor CSS insertion',
)

# -----------------------------------------------------------------------------
# 2) Replace My Notes content textarea with a progressive-enhancement shell.
#    The original textarea stays as a fallback and remains the compatibility
#    bridge for the existing form logic if CDN imports fail.
# -----------------------------------------------------------------------------
old_content_field = r'''              <div class="field">
                <label for="myNoteContent">Content *</label>
                <textarea id="myNoteContent" class="my-note-content" required placeholder="Write the useful information, lesson, code idea, process, or reminder you want to keep..."></textarea>
              </div>'''

new_content_field = r'''              <div class="field">
                <label for="myNoteContent">Content *</label>
                <div id="myNoteRichEditorShell" class="rich-editor-shell loading">
                  <div id="myNoteRichToolbar" class="rich-editor-toolbar" aria-label="Note formatting toolbar">
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="undo" title="Undo" aria-label="Undo">↶</button>
                      <button class="rich-tool-button" type="button" data-rich-command="redo" title="Redo" aria-label="Redo">↷</button>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <select id="myNoteRichBlockType" class="rich-tool-select" aria-label="Paragraph style">
                        <option value="paragraph">Paragraph</option>
                        <option value="heading1">Heading 1</option>
                        <option value="heading2">Heading 2</option>
                        <option value="heading3">Heading 3</option>
                      </select>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="bold" title="Bold (Ctrl+B)" aria-label="Bold"><strong>B</strong></button>
                      <button class="rich-tool-button" type="button" data-rich-command="italic" title="Italic (Ctrl+I)" aria-label="Italic"><em>I</em></button>
                      <button class="rich-tool-button" type="button" data-rich-command="underline" title="Underline (Ctrl+U)" aria-label="Underline"><u>U</u></button>
                      <button class="rich-tool-button" type="button" data-rich-command="strike" title="Strikethrough" aria-label="Strikethrough"><s>S</s></button>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="bulletList" title="Bulleted list" aria-label="Bulleted list">• List</button>
                      <button class="rich-tool-button" type="button" data-rich-command="orderedList" title="Numbered list" aria-label="Numbered list">1. List</button>
                      <button class="rich-tool-button" type="button" data-rich-command="outdent" title="Outdent list item" aria-label="Outdent">⇤</button>
                      <button class="rich-tool-button" type="button" data-rich-command="indent" title="Indent list item" aria-label="Indent">⇥</button>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="alignLeft" title="Align left" aria-label="Align left">≡←</button>
                      <button class="rich-tool-button" type="button" data-rich-command="alignCenter" title="Align center" aria-label="Align center">≡</button>
                      <button class="rich-tool-button" type="button" data-rich-command="alignRight" title="Align right" aria-label="Align right">→≡</button>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="link" title="Add or edit link" aria-label="Add or edit link">🔗</button>
                      <button class="rich-tool-button" type="button" data-rich-command="blockquote" title="Quote" aria-label="Quote">❝</button>
                      <button class="rich-tool-button" type="button" data-rich-command="horizontalRule" title="Horizontal line" aria-label="Horizontal line">─</button>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="insertTable" title="Insert table" aria-label="Insert table">▦ Table</button>
                      <button class="rich-tool-button" type="button" data-rich-command="addRow" data-rich-table-only title="Add table row" aria-label="Add table row">+Row</button>
                      <button class="rich-tool-button" type="button" data-rich-command="addColumn" data-rich-table-only title="Add table column" aria-label="Add table column">+Col</button>
                      <button class="rich-tool-button" type="button" data-rich-command="deleteRow" data-rich-table-only title="Delete table row" aria-label="Delete table row">−Row</button>
                      <button class="rich-tool-button" type="button" data-rich-command="deleteColumn" data-rich-table-only title="Delete table column" aria-label="Delete table column">−Col</button>
                      <button class="rich-tool-button" type="button" data-rich-command="deleteTable" data-rich-table-only title="Delete table" aria-label="Delete table">×Tbl</button>
                    </span>
                    <span class="rich-editor-toolbar-group">
                      <button class="rich-tool-button" type="button" data-rich-command="clearFormatting" title="Clear formatting" aria-label="Clear formatting">Tx</button>
                    </span>
                  </div>
                  <div id="myNoteRichEditor" class="rich-editor-surface" aria-label="Note content editor"></div>
                  <textarea id="myNoteContent" class="my-note-content" required placeholder="Write the useful information, lesson, code idea, process, or reminder you want to keep..."></textarea>
                </div>
                <div class="rich-editor-load-note">Loading the rich text editor… the normal text box remains available if it cannot load.</div>
                <div class="rich-editor-hint">Formatting supports headings, bold, italic, underline, lists, indentation, alignment, links, quotes and tables. Ctrl/Cmd + Enter saves.</div>
              </div>'''

html = replace_once(html, old_content_field, new_content_field, 'My Notes content field')

# -----------------------------------------------------------------------------
# 3) State for the rich editor.
# -----------------------------------------------------------------------------
html = replace_once(
    html,
    '    let editingChecklistItemId = null;\n',
    "    let editingChecklistItemId = null;\n    let myNoteRichEditor = null;\n    let richHtmlSanitizer = null;\n    let richEditorLoadPromise = null;\n",
    'rich editor state variables',
)

# -----------------------------------------------------------------------------
# 4) Reusable rich text helpers + Tiptap initialization.
# -----------------------------------------------------------------------------
rich_js = r'''

    function looksLikeRichHtml(value = '') {
      return /<(?:p|h[1-6]|ul|ol|li|strong|em|u|s|blockquote|table|thead|tbody|tr|th|td|hr|br|a)\b/i.test(String(value || ''));
    }

    function legacyTextToHtml(value = '') {
      const text = String(value || '');
      if (!text) return '<p></p>';
      const paragraphs = text.replace(/\r\n?/g, '\n').split(/\n{2,}/);
      return paragraphs.map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\n/g, '<br>')}</p>`).join('');
    }

    function normalizeRichContent(value = '') {
      const raw = String(value || '');
      if (!raw.trim()) return '<p></p>';
      if (!looksLikeRichHtml(raw)) return legacyTextToHtml(raw);
      if (!richHtmlSanitizer) return raw;
      return sanitizeRichHtml(raw);
    }

    function sanitizeRichHtml(value = '') {
      const raw = String(value || '');
      if (!richHtmlSanitizer) return raw;
      return richHtmlSanitizer.sanitize(raw, {
        ALLOWED_TAGS: ['p','br','strong','em','u','s','h1','h2','h3','ul','ol','li','blockquote','hr','a','table','thead','tbody','tr','th','td'],
        ALLOWED_ATTR: ['href','target','rel','colspan','rowspan','style']
      });
    }

    function richTextToPlainText(value = '') {
      const raw = String(value || '');
      if (!looksLikeRichHtml(raw)) return raw;
      const holder = document.createElement('div');
      if (richHtmlSanitizer) holder.innerHTML = sanitizeRichHtml(raw);
      else holder.textContent = raw.replace(/<[^>]+>/g, ' ');
      return (holder.textContent || holder.innerText || '').replace(/\s+/g, ' ').trim();
    }

    function renderRichText(value = '') {
      if (!richHtmlSanitizer) return legacyTextToHtml(String(value || ''));
      return sanitizeRichHtml(normalizeRichContent(value));
    }

    function getMyNoteContentForStorage() {
      if (myNoteRichEditor && $('myNoteRichEditorShell')?.classList.contains('ready')) {
        return sanitizeRichHtml(myNoteRichEditor.getHTML()).trim();
      }
      return $('myNoteContent')?.value || '';
    }

    function setMyNoteRichContent(value = '') {
      const textarea = $('myNoteContent');
      const normalized = normalizeRichContent(value);
      if (myNoteRichEditor) {
        myNoteRichEditor.commands.setContent(normalized, { emitUpdate: false });
        const clean = sanitizeRichHtml(myNoteRichEditor.getHTML());
        if (textarea) textarea.value = clean;
        updateMyNoteRichToolbar();
      } else if (textarea) {
        textarea.value = value || '';
      }
    }

    function syncMyNoteRichEditorToTextarea() {
      if (!myNoteRichEditor) return;
      const textarea = $('myNoteContent');
      if (textarea) textarea.value = sanitizeRichHtml(myNoteRichEditor.getHTML());
    }

    function updateMyNoteRichToolbar() {
      if (!myNoteRichEditor) return;
      const toolbar = $('myNoteRichToolbar');
      if (!toolbar) return;
      const editor = myNoteRichEditor;
      const active = {
        bold: editor.isActive('bold'),
        italic: editor.isActive('italic'),
        underline: editor.isActive('underline'),
        strike: editor.isActive('strike'),
        bulletList: editor.isActive('bulletList'),
        orderedList: editor.isActive('orderedList'),
        blockquote: editor.isActive('blockquote'),
        link: editor.isActive('link'),
        alignLeft: editor.isActive({ textAlign: 'left' }),
        alignCenter: editor.isActive({ textAlign: 'center' }),
        alignRight: editor.isActive({ textAlign: 'right' })
      };
      Object.entries(active).forEach(([command, isActive]) => {
        toolbar.querySelector(`[data-rich-command="${command}"]`)?.classList.toggle('active', Boolean(isActive));
      });
      const inTable = editor.isActive('table');
      toolbar.querySelectorAll('[data-rich-table-only]').forEach((button) => { button.disabled = !inTable; });
      const blockSelect = $('myNoteRichBlockType');
      if (blockSelect) {
        if (editor.isActive('heading', { level: 1 })) blockSelect.value = 'heading1';
        else if (editor.isActive('heading', { level: 2 })) blockSelect.value = 'heading2';
        else if (editor.isActive('heading', { level: 3 })) blockSelect.value = 'heading3';
        else blockSelect.value = 'paragraph';
      }
    }

    function runMyNoteRichCommand(command) {
      if (!myNoteRichEditor) return;
      const editor = myNoteRichEditor;
      const chain = () => editor.chain().focus();
      switch (command) {
        case 'undo': chain().undo().run(); break;
        case 'redo': chain().redo().run(); break;
        case 'bold': chain().toggleBold().run(); break;
        case 'italic': chain().toggleItalic().run(); break;
        case 'underline': chain().toggleUnderline().run(); break;
        case 'strike': chain().toggleStrike().run(); break;
        case 'bulletList': chain().toggleBulletList().run(); break;
        case 'orderedList': chain().toggleOrderedList().run(); break;
        case 'indent': chain().sinkListItem('listItem').run(); break;
        case 'outdent': chain().liftListItem('listItem').run(); break;
        case 'alignLeft': chain().setTextAlign('left').run(); break;
        case 'alignCenter': chain().setTextAlign('center').run(); break;
        case 'alignRight': chain().setTextAlign('right').run(); break;
        case 'blockquote': chain().toggleBlockquote().run(); break;
        case 'horizontalRule': chain().setHorizontalRule().run(); break;
        case 'clearFormatting': chain().unsetAllMarks().clearNodes().run(); break;
        case 'link': {
          const previous = editor.getAttributes('link')?.href || '';
          const href = window.prompt('Enter the link URL. Leave blank to remove the current link.', previous);
          if (href === null) break;
          const trimmed = href.trim();
          if (!trimmed) chain().extendMarkRange('link').unsetLink().run();
          else {
            const safe = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
            chain().extendMarkRange('link').setLink({ href: safe, target: '_blank', rel: 'noopener noreferrer' }).run();
          }
          break;
        }
        case 'insertTable': {
          const rowsValue = window.prompt('How many rows?', '3');
          if (rowsValue === null) break;
          const colsValue = window.prompt('How many columns?', '3');
          if (colsValue === null) break;
          const rows = Math.min(20, Math.max(2, Number.parseInt(rowsValue, 10) || 3));
          const cols = Math.min(10, Math.max(2, Number.parseInt(colsValue, 10) || 3));
          chain().insertTable({ rows, cols, withHeaderRow: true }).run();
          break;
        }
        case 'addRow': chain().addRowAfter().run(); break;
        case 'addColumn': chain().addColumnAfter().run(); break;
        case 'deleteRow': chain().deleteRow().run(); break;
        case 'deleteColumn': chain().deleteColumn().run(); break;
        case 'deleteTable': chain().deleteTable().run(); break;
      }
      updateMyNoteRichToolbar();
    }

    async function initializeRichTextEditors() {
      if (richEditorLoadPromise) return richEditorLoadPromise;
      const shell = $('myNoteRichEditorShell');
      const host = $('myNoteRichEditor');
      if (!shell || !host) return null;
      richEditorLoadPromise = (async () => {
        try {
          const [coreModule, starterModule, tableModule, alignModule, purifyModule] = await Promise.all([
            import('https://cdn.jsdelivr.net/npm/@tiptap/core@3.31.4/+esm'),
            import('https://cdn.jsdelivr.net/npm/@tiptap/starter-kit@3.31.4/+esm'),
            import('https://cdn.jsdelivr.net/npm/@tiptap/extension-table@3.31.4/+esm'),
            import('https://cdn.jsdelivr.net/npm/@tiptap/extension-text-align@3.31.4/+esm'),
            import('https://cdn.jsdelivr.net/npm/dompurify@3.4.16/+esm')
          ]);
          const Editor = coreModule.Editor;
          const StarterKit = starterModule.default || starterModule.StarterKit;
          const TableKit = tableModule.TableKit;
          const TextAlign = alignModule.default || alignModule.TextAlign;
          richHtmlSanitizer = purifyModule.default || purifyModule;
          if (!Editor || !StarterKit || !TableKit || !TextAlign || !richHtmlSanitizer?.sanitize) throw new Error('A rich editor dependency did not load correctly.');

          myNoteRichEditor = new Editor({
            element: host,
            extensions: [
              StarterKit.configure({
                link: { openOnClick: false, autolink: true, defaultProtocol: 'https' }
              }),
              TableKit,
              TextAlign.configure({ types: ['heading', 'paragraph'] })
            ],
            content: normalizeRichContent($('myNoteContent')?.value || ''),
            editorProps: {
              attributes: { spellcheck: 'true', autocomplete: 'off' },
              handleKeyDown: (_view, event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                  event.preventDefault();
                  $('myNoteForm').requestSubmit();
                  return true;
                }
                return false;
              }
            },
            onCreate: () => {
              syncMyNoteRichEditorToTextarea();
              updateMyNoteRichToolbar();
            },
            onUpdate: () => {
              syncMyNoteRichEditorToTextarea();
              refreshMyNoteDirtyState();
              updateMyNoteRichToolbar();
            },
            onSelectionUpdate: updateMyNoteRichToolbar
          });

          $('myNoteRichToolbar')?.addEventListener('click', (event) => {
            const button = event.target.closest('[data-rich-command]');
            if (!button || button.disabled) return;
            runMyNoteRichCommand(button.dataset.richCommand);
          });
          $('myNoteRichBlockType')?.addEventListener('change', (event) => {
            if (!myNoteRichEditor) return;
            const value = event.target.value;
            const chain = myNoteRichEditor.chain().focus();
            if (value === 'heading1') chain.toggleHeading({ level: 1 }).run();
            else if (value === 'heading2') chain.toggleHeading({ level: 2 }).run();
            else if (value === 'heading3') chain.toggleHeading({ level: 3 }).run();
            else chain.setParagraph().run();
            updateMyNoteRichToolbar();
          });

          shell.classList.remove('loading');
          shell.classList.add('ready');
          syncMyNoteRichEditorToTextarea();
          renderPersonalNotes();
          return myNoteRichEditor;
        } catch (error) {
          shell.classList.remove('loading');
          console.warn('Rich text editor could not be loaded. Falling back to the normal text area.', error);
          return null;
        }
      })();
      return richEditorLoadPromise;
    }
'''

html = replace_once(
    html,
    '\n    function getMyNoteSnapshot() {',
    rich_js + '\n\n    function getMyNoteSnapshot() {',
    'rich editor JavaScript helpers',
)

# Snapshot uses editor HTML when available.
html = replace_once(
    html,
    "        content: $('myNoteContent')?.value || '',",
    "        content: getMyNoteContentForStorage(),",
    'My Notes snapshot content',
)

# Search uses plain text extracted from rich content.
html = replace_once(
    html,
    "        const matchesSearch = !query || `${note.title || ''} ${note.content || ''}`.toLowerCase().includes(query);",
    "        const matchesSearch = !query || `${note.title || ''} ${richTextToPlainText(note.content || '')}`.toLowerCase().includes(query);",
    'My Notes rich search',
)

# Saved note rendering now safely renders formatting instead of escaping tags.
html = replace_once(
    html,
    '          <div class="saved-note-content">${escapeHtml(note.content)}</div>',
    '          <div class="saved-note-content">${renderRichText(note.content)}</div>',
    'saved note rich rendering',
)

# Reset and open editor must keep Tiptap and the compatibility textarea in sync.
html = replace_once(
    html,
    "      $('myNoteForm').reset();\n      updatePersonalNoteCategoryOptions();",
    "      $('myNoteForm').reset();\n      setMyNoteRichContent('');\n      updatePersonalNoteCategoryOptions();",
    'reset My Notes rich content',
)

html = replace_once(
    html,
    "        $('myNoteContent').value = note.content || '';",
    "        setMyNoteRichContent(note.content || '');",
    'open My Notes rich content',
)

# Save validates visible text, but stores sanitized HTML.
html = replace_once(
    html,
    "      const content = $('myNoteContent').value.trim();\n      if (!title) { updateMyNoteStatus('unsaved', 'Please enter a title.'); $('myNoteTitle').focus(); return; }\n      if (!content) { updateMyNoteStatus('unsaved', 'Please enter the note content.'); $('myNoteContent').focus(); return; }",
    "      const content = getMyNoteContentForStorage().trim();\n      if (!title) { updateMyNoteStatus('unsaved', 'Please enter a title.'); $('myNoteTitle').focus(); return; }\n      if (!richTextToPlainText(content).trim()) { updateMyNoteStatus('unsaved', 'Please enter the note content.'); if (myNoteRichEditor) myNoteRichEditor.commands.focus(); else $('myNoteContent').focus(); return; }",
    'save My Notes rich content',
)

# Realtime updates should set the rich editor when there is no local draft.
html = replace_once(
    html,
    "              $('myNoteContent').value = changed.content || '';",
    "              setMyNoteRichContent(changed.content || '');",
    'Realtime My Notes rich content',
)

# Start progressive rich-editor loading without blocking the rest of the app.
html = replace_once(
    html,
    '    initializeAuth();\n',
    '    initializeRichTextEditors();\n    initializeAuth();\n',
    'rich editor initialization',
)

INDEX.write_text(html, encoding='utf-8')

# -----------------------------------------------------------------------------
# 5) Bump PWA cache so installed apps receive the new editor UI.
# -----------------------------------------------------------------------------
sw = SW.read_text(encoding='utf-8')
if "pks-ideas-v18" in sw:
    sw = sw.replace("pks-ideas-v18", "pks-ideas-v19", 1)
elif "pks-ideas-v19" not in sw:
    raise RuntimeError('Could not identify the service-worker cache version')
SW.write_text(sw, encoding='utf-8')

# Keep a compact release note in the repository.
if README.exists():
    readme = README.read_text(encoding='utf-8')
    marker = '## v19 rich text — My Notes'
    if marker not in readme:
        readme += '''\n\n## v19 rich text — My Notes\n\n- My Notes Content now uses a Word-like rich-text editor when the editor CDN loads successfully.\n- Supports headings, bold, italic, underline, strikethrough, bullet/numbered lists, list indentation, alignment, links, quotes, horizontal rules and tables.\n- Existing plain-text notes are preserved and converted to rich HTML only when edited/saved.\n- Stored HTML is sanitized before save/render.\n- The original textarea remains as a graceful fallback if the rich editor cannot load.\n- No Supabase schema changes are required for this stage because `personal_notes.content` is already a text column.\n'''
        README.write_text(readme, encoding='utf-8')

print('Rich text Stage 1 patch applied successfully.')
