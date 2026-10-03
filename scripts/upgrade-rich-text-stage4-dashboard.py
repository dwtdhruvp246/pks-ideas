from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')
SQL = Path('supabase.sql')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

if 'dashboardNoteRichShell' in html:
    print('Dashboard rich-text Stage 4 already applied; nothing to do.')
else:
    # -------------------------------------------------------------------------
    # CSS
    # -------------------------------------------------------------------------
    stage4_css = r'''

    /* Rich text editor — Stage 4: Dashboard Notes */
    .dashboard-rich-editor-shell .rich-editor-surface .tiptap {
      min-height:180px;
    }
    .dashboard-notes.expanded .dashboard-rich-editor-shell .rich-editor-surface .tiptap {
      min-height:58vh;
    }
    .dashboard-rich-editor-shell.ready > .dashboard-note-textarea {
      display:none;
    }

    @media (max-width:560px) {
      .dashboard-rich-editor-shell .rich-editor-surface .tiptap { min-height:190px; }
      .dashboard-notes.expanded .dashboard-rich-editor-shell .rich-editor-surface .tiptap { min-height:64vh; }
    }
'''
    html = replace_once(
        html,
        '\n\n    /* Checklist workspace + per-idea checklist */',
        stage4_css + '\n\n    /* Checklist workspace + per-idea checklist */',
        'Dashboard rich editor CSS',
    )

    # -------------------------------------------------------------------------
    # HTML
    # -------------------------------------------------------------------------
    old_dashboard = '''              <textarea id="dashboardNoteInput" class="input dashboard-note-textarea" placeholder="Type what you need to do..."></textarea>
              <div class="dashboard-note-hint">Press Enter to save • Shift + Enter for a new line</div>'''
    new_dashboard = '''              <div id="dashboardNoteRichShell" class="rich-editor-shell dashboard-rich-editor-shell">
                <div id="dashboardNoteRichToolbar" class="rich-editor-toolbar" aria-label="Dashboard Notes formatting toolbar"></div>
                <div id="dashboardNoteRichEditor" class="rich-editor-surface"></div>
                <textarea id="dashboardNoteInput" class="input dashboard-note-textarea rich-editor-fallback" placeholder="Type what you need to do..."></textarea>
              </div>
              <div class="dashboard-note-hint">Enter creates a new paragraph/list item • Ctrl/Cmd + Enter saves</div>'''
    html = replace_once(html, old_dashboard, new_dashboard, 'Dashboard Notes editor HTML')

    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        '    let checklistRichEditor = null;\n',
        '    let checklistRichEditor = null;\n    let dashboardRichEditor = null;\n',
        'Dashboard rich editor state',
    )

    # -------------------------------------------------------------------------
    # Rich editor implementation
    # -------------------------------------------------------------------------
    dashboard_js = r'''

    function syncDashboardRichEditor() {
      if (!dashboardRichEditor?.editable || !dashboardRichEditor?.textarea) return;
      repairOrderedListContinuations(dashboardRichEditor.editable);
      dashboardRichEditor.textarea.value = sanitizeRichHtml(dashboardRichEditor.editable.innerHTML);
    }

    function getDashboardNoteContentForStorage() {
      if (dashboardRichEditor?.editable && dashboardRichEditor.shell?.classList.contains('ready')) {
        repairOrderedListContinuations(dashboardRichEditor.editable);
        return sanitizeRichHtml(dashboardRichEditor.editable.innerHTML).trim();
      }
      return $('dashboardNoteInput')?.value || '';
    }

    function setDashboardNoteRichContent(value = '') {
      const textarea = $('dashboardNoteInput');
      const normalized = normalizeRichContent(value);
      if (dashboardRichEditor?.editable) {
        dashboardRichEditor.editable.innerHTML = normalized;
        repairOrderedListContinuations(dashboardRichEditor.editable);
        const clean = sanitizeRichHtml(dashboardRichEditor.editable.innerHTML);
        dashboardRichEditor.editable.innerHTML = clean || '<p><br></p>';
        if (textarea) textarea.value = clean;
        updateIdeaRichToolbar(dashboardRichEditor);
      } else if (textarea) {
        textarea.value = value || '';
      }
    }

    function execDashboardRichCommand(command, value = null) {
      dashboardRichEditor?.editable?.focus();
      try { document.execCommand(command, false, value); }
      catch (error) { console.warn(`Dashboard rich text command failed: ${command}`, error); }
      syncDashboardRichEditor();
      if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
      else updateDashboardNoteStatus('', '');
      updateIdeaRichToolbar(dashboardRichEditor);
    }

    function runDashboardRichCommand(command) {
      const editor = dashboardRichEditor;
      if (!editor) return;
      switch (command) {
        case 'undo': execDashboardRichCommand('undo'); break;
        case 'redo': execDashboardRichCommand('redo'); break;
        case 'bold': execDashboardRichCommand('bold'); break;
        case 'italic': execDashboardRichCommand('italic'); break;
        case 'underline': execDashboardRichCommand('underline'); break;
        case 'strike': execDashboardRichCommand('strikeThrough'); break;
        case 'bulletList': execDashboardRichCommand('insertUnorderedList'); break;
        case 'orderedList': execDashboardRichCommand('insertOrderedList'); break;
        case 'indent': stepRichIndent(editor.editable, 1); break;
        case 'outdent': stepRichIndent(editor.editable, -1); break;
        case 'alignLeft': execDashboardRichCommand('justifyLeft'); break;
        case 'alignCenter': execDashboardRichCommand('justifyCenter'); break;
        case 'alignRight': execDashboardRichCommand('justifyRight'); break;
        case 'blockquote': execDashboardRichCommand('formatBlock', 'blockquote'); break;
        case 'horizontalRule': execDashboardRichCommand('insertHorizontalRule'); break;
        case 'clearFormatting': execDashboardRichCommand('removeFormat'); break;
        case 'link': {
          const existing = ideaRichClosest(editor, 'a');
          const previous = existing?.getAttribute('href') || '';
          const href = window.prompt('Enter the link URL. Leave blank to remove the current link.', previous);
          if (href === null) break;
          const trimmed = href.trim();
          if (!trimmed) execDashboardRichCommand('unlink');
          else {
            const safe = /^(https?:\/\/|mailto:)/i.test(trimmed) ? trimmed : `https://${trimmed}`;
            execDashboardRichCommand('createLink', safe);
            const link = ideaRichClosest(editor, 'a');
            if (link) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
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
          let table = '<table><tbody>';
          for (let r = 0; r < rows; r += 1) {
            table += '<tr>';
            for (let c = 0; c < cols; c += 1) table += r === 0 ? '<th><br></th>' : '<td><br></td>';
            table += '</tr>';
          }
          table += '</tbody></table><p><br></p>';
          insertIdeaRichHtml(editor, table);
          break;
        }
        case 'addRow': addIdeaRichTableRow(editor); break;
        case 'addColumn': addIdeaRichTableColumn(editor); break;
        case 'deleteRow': deleteIdeaRichTableRow(editor); break;
        case 'deleteColumn': deleteIdeaRichTableColumn(editor); break;
        case 'deleteTable': ideaRichClosest(editor, 'table')?.remove(); editor.editable.focus(); break;
      }
      syncDashboardRichEditor();
      if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
      else updateDashboardNoteStatus('', '');
      updateIdeaRichToolbar(editor);
    }

    function handleDashboardRichSmartList(event) {
      const editor = dashboardRichEditor;
      if (!editor || event.key !== ' ' || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
      const selection = window.getSelection();
      if (!selection?.rangeCount || !selection.isCollapsed || !editor.editable.contains(selection.anchorNode)) return;
      const range = selection.getRangeAt(0);
      let block = range.startContainer.nodeType === Node.TEXT_NODE ? range.startContainer.parentElement : range.startContainer;
      block = block?.closest?.('p,div');
      if (!block || !editor.editable.contains(block)) return;
      const prefixRange = document.createRange();
      prefixRange.selectNodeContents(block);
      try { prefixRange.setEnd(range.endContainer, range.endOffset); } catch { return; }
      const prefix = prefixRange.toString();
      const ordered = /^\s*\d+\.$/.test(prefix);
      const bullet = /^\s*[-*]$/.test(prefix);
      if (!ordered && !bullet) return;
      event.preventDefault();
      prefixRange.deleteContents();
      selection.removeAllRanges();
      const caret = document.createRange();
      caret.selectNodeContents(block);
      caret.collapse(true);
      selection.addRange(caret);
      document.execCommand(ordered ? 'insertOrderedList' : 'insertUnorderedList', false, null);
      syncDashboardRichEditor();
      updateIdeaRichToolbar(editor);
      if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
    }

    function initializeDashboardRichTextEditor() {
      const shell = $('dashboardNoteRichShell');
      const host = $('dashboardNoteRichEditor');
      const textarea = $('dashboardNoteInput');
      const toolbar = $('dashboardNoteRichToolbar');
      if (!shell || !host || !textarea || !toolbar) return null;

      toolbar.innerHTML = buildIdeaRichToolbar('dashboardNoteRichBlockType');
      host.innerHTML = '<div class="tiptap" contenteditable="true" role="textbox" aria-multiline="true" spellcheck="true" data-placeholder="Type what you need to do..."></div>';
      const editable = host.firstElementChild;
      dashboardRichEditor = { shell, host, textarea, toolbar, editable, blockSelectId:'dashboardNoteRichBlockType' };
      editable.innerHTML = normalizeRichContent(textarea.value || '');

      editable.addEventListener('input', () => {
        syncDashboardRichEditor();
        if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
        else updateDashboardNoteStatus('', '');
        updateIdeaRichToolbar(dashboardRichEditor);
      });
      editable.addEventListener('keyup', () => updateIdeaRichToolbar(dashboardRichEditor));
      editable.addEventListener('mouseup', () => updateIdeaRichToolbar(dashboardRichEditor));
      editable.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
          event.preventDefault();
          saveDashboardNote();
          return;
        }
        if (event.key === 'Tab' && ideaRichSelectionInside(dashboardRichEditor)) {
          event.preventDefault();
          stepRichIndent(editable, event.shiftKey ? -1 : 1);
          syncDashboardRichEditor();
          if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
          updateIdeaRichToolbar(dashboardRichEditor);
          return;
        }
        handleDashboardRichSmartList(event);
      });
      editable.addEventListener('paste', (event) => {
        const htmlData = event.clipboardData?.getData('text/html') || '';
        const plainData = event.clipboardData?.getData('text/plain') || '';
        if (!htmlData) return;
        event.preventDefault();
        insertIdeaRichHtml(dashboardRichEditor, sanitizeRichHtml(htmlData) || legacyTextToHtml(plainData));
        syncDashboardRichEditor();
        if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
      });

      toolbar.addEventListener('mousedown', (event) => {
        if (event.target.closest('button')) event.preventDefault();
      });
      toolbar.addEventListener('click', (event) => {
        const button = event.target.closest('[data-idea-rich-command]');
        if (!button || button.disabled) return;
        runDashboardRichCommand(button.dataset.ideaRichCommand);
      });
      $('dashboardNoteRichBlockType')?.addEventListener('change', (event) => {
        const map = { paragraph:'p', heading1:'h1', heading2:'h2', heading3:'h3' };
        execDashboardRichCommand('formatBlock', map[event.target.value] || 'p');
      });
      document.addEventListener('selectionchange', () => {
        if (ideaRichSelectionInside(dashboardRichEditor)) updateIdeaRichToolbar(dashboardRichEditor);
      });

      shell.classList.add('ready');
      syncDashboardRichEditor();
      updateIdeaRichToolbar(dashboardRichEditor);
      return dashboardRichEditor;
    }
'''
    html = replace_once(
        html,
        '\n    function updateDashboardNoteStatus(state = \'\', message = \'\') {',
        dashboard_js + '\n\n    function updateDashboardNoteStatus(state = \'\', message = \'\') {',
        'Dashboard rich editor JavaScript',
    )

    # -------------------------------------------------------------------------
    # Dirty-state + load/save/realtime wiring
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        "      const input = $('dashboardNoteInput');\n      return Boolean(input && input.value !== dashboardNoteSavedValue);",
        "      const input = $('dashboardNoteInput');\n      if (!input) return false;\n      return getDashboardNoteContentForStorage() !== dashboardNoteSavedValue;",
        'Dashboard dirty state rich content',
    )

    html = replace_once(
        html,
        "      if (input) input.value = value;\n      dashboardNoteSavedValue = value;",
        "      if (input) setDashboardNoteRichContent(value);\n      dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(value));",
        'Dashboard load rich content',
    )

    html = replace_once(
        html,
        "      const input = $('dashboardNoteInput');\n      const content = input.value;",
        "      const input = $('dashboardNoteInput');\n      const content = getDashboardNoteContentForStorage();",
        'Dashboard save rich content',
    )

    html = replace_once(
        html,
        "      dashboardNoteSavedValue = data?.content ?? content;\n      if (input.value === dashboardNoteSavedValue) {",
        "      dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(data?.content ?? content));\n      if (getDashboardNoteContentForStorage() === dashboardNoteSavedValue) {",
        'Dashboard post-save rich comparison',
    )

    html = replace_once(
        html,
        "            if (!dashboardNoteIsDirty()) input.value = '';\n            dashboardNoteSavedValue = '';",
        "            if (!dashboardNoteIsDirty()) setDashboardNoteRichContent('');\n            dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(''));",
        'Dashboard realtime delete rich content',
    )

    html = replace_once(
        html,
        "          if (!dashboardNoteIsDirty() || input.value === dashboardNoteSavedValue) {\n            input.value = incoming;\n            dashboardNoteSavedValue = incoming;",
        "          if (!dashboardNoteIsDirty() || getDashboardNoteContentForStorage() === dashboardNoteSavedValue) {\n            setDashboardNoteRichContent(incoming);\n            dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(incoming));",
        'Dashboard realtime update rich content',
    )

    html = replace_once(
        html,
        "            dashboardNoteSavedValue = incoming;\n            updateDashboardNoteStatus('unsaved', 'Changed on another device — your local text is not saved');",
        "            dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(incoming));\n            updateDashboardNoteStatus('unsaved', 'Changed on another device — your local text is not saved');",
        'Dashboard realtime incoming saved version',
    )

    # Logout/reset
    html = replace_once(
        html,
        "      if ($('dashboardNoteInput')) $('dashboardNoteInput').value = '';\n      dashboardNoteSavedValue = '';",
        "      if ($('dashboardNoteInput')) setDashboardNoteRichContent('');\n      dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(''));",
        'Dashboard logout reset rich content',
    )

    # Expand focus
    html = replace_once(
        html,
        "          $('dashboardNoteInput').focus({ preventScroll: true });\n          panel.scrollIntoView({ behavior: 'smooth', block: 'start' });",
        "          if (dashboardRichEditor?.editable) dashboardRichEditor.editable.focus({ preventScroll: true });\n          else $('dashboardNoteInput').focus({ preventScroll: true });\n          panel.scrollIntoView({ behavior: 'smooth', block: 'start' });",
        'Dashboard expand rich focus',
    )

    # Remove old textarea input/Enter-to-save listeners and replace with fallback-only input handling.
    old_listeners = '''    $('saveDashboardNoteButton').addEventListener('click', saveDashboardNote);
    $('dashboardNoteInput').addEventListener('input', () => {
      if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
      else updateDashboardNoteStatus('', '');
    });
    $('dashboardNoteInput').addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        saveDashboardNote();
      }
    });'''
    new_listeners = '''    $('saveDashboardNoteButton').addEventListener('click', saveDashboardNote);
    $('dashboardNoteInput').addEventListener('input', () => {
      if (dashboardRichEditor?.shell?.classList.contains('ready')) return;
      if (dashboardNoteIsDirty()) updateDashboardNoteStatus('unsaved', 'Unsaved changes');
      else updateDashboardNoteStatus('', '');
    });'''
    html = replace_once(html, old_listeners, new_listeners, 'Dashboard keyboard/listener behavior')

    # Startup
    html = replace_once(
        html,
        '    initializeChecklistRichTextEditor();\n    initializeAuth();',
        '    initializeChecklistRichTextEditor();\n    initializeDashboardRichTextEditor();\n    initializeAuth();',
        'Dashboard rich editor initialization',
    )

    INDEX.write_text(html, encoding='utf-8')

    # -------------------------------------------------------------------------
    # PWA cache bump
    # -------------------------------------------------------------------------
    sw = SW.read_text(encoding='utf-8')
    if 'pks-ideas-v25' in sw:
        sw = sw.replace('pks-ideas-v25', 'pks-ideas-v26', 1)
    elif 'pks-ideas-v26' not in sw:
        raise RuntimeError('Could not identify expected service worker version v25')
    SW.write_text(sw, encoding='utf-8')

    # -------------------------------------------------------------------------
    # Reference SQL: future fresh installs should not reintroduce the old limit.
    # -------------------------------------------------------------------------
    if SQL.exists():
        sql = SQL.read_text(encoding='utf-8')
        sql = sql.replace("content text not null default '' check (char_length(content) <= 10000),", "content text not null default '',", 1)
        marker = 'create index if not exists dashboard_notes_user_id_idx on public.dashboard_notes(user_id);'
        if marker in sql and 'drop constraint if exists dashboard_notes_content_check' not in sql:
            sql = sql.replace(marker, "alter table public.dashboard_notes\n  drop constraint if exists dashboard_notes_content_check;\n\n" + marker, 1)
        SQL.write_text(sql, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        marker = '## v26 rich text — Dashboard Notes'
        if marker not in readme:
            readme += '''\n\n## v26 rich text — Dashboard Notes\n\n- Dashboard Notes now uses the same self-contained rich-text editor as My Notes, Ideas and Checklist Details.\n- Enter creates normal paragraphs/list items; Ctrl/Cmd + Enter saves.\n- Existing plain-text dashboard notes remain compatible.\n- Dirty-state and cross-device protection continue to work with formatted HTML.\n- The old 10,000-character dashboard-note database constraint is removed from the reference schema.\n'''
            README.write_text(readme, encoding='utf-8')

    print('Dashboard rich-text Stage 4 patch applied successfully.')
