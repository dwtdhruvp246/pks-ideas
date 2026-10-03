from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

if 'checklistDetailsRichShell' in html:
    print('Checklist rich-text Stage 3 already applied; nothing to do.')
else:
    # -------------------------------------------------------------------------
    # CSS
    # -------------------------------------------------------------------------
    stage3_css = r'''

    /* Rich text editor — Stage 3: Checklist Details */
    .checklist-rich-editor-shell .rich-editor-surface .tiptap { min-height:220px; }
    .checklist-library-details,
    .checklist-rich-content { line-height:1.6; }
    .checklist-library-details > :first-child,
    .checklist-rich-content > :first-child { margin-top:0; }
    .checklist-library-details > :last-child,
    .checklist-rich-content > :last-child { margin-bottom:0; }
    .idea-checklist-details .checklist-linked-note { margin-top:10px; }

    @media (max-width:560px) {
      .checklist-rich-editor-shell .rich-editor-surface .tiptap { min-height:230px; }
    }
'''
    html = replace_once(
        html,
        '\n\n    /* Checklist workspace + per-idea checklist */',
        stage3_css + '\n\n    /* Checklist workspace + per-idea checklist */',
        'Checklist rich editor CSS',
    )

    # -------------------------------------------------------------------------
    # HTML
    # -------------------------------------------------------------------------
    old_details = '''            <div class="field">
              <label for="checklistDetails">Checklist details *</label>
              <textarea id="checklistDetails" required placeholder="Explain what needs to be checked or implemented..."></textarea>
            </div>'''
    new_details = '''            <div class="field">
              <label for="checklistDetails">Checklist details *</label>
              <div id="checklistDetailsRichShell" class="rich-editor-shell checklist-rich-editor-shell">
                <div id="checklistDetailsRichToolbar" class="rich-editor-toolbar" aria-label="Checklist details formatting toolbar"></div>
                <div id="checklistDetailsRichEditor" class="rich-editor-surface"></div>
                <textarea id="checklistDetails" class="rich-editor-fallback" required placeholder="Explain what needs to be checked or implemented..."></textarea>
              </div>
              <div class="idea-rich-hint">Use headings, bold, lists, indentation, links and tables. Ctrl/Cmd + Enter saves the checklist item.</div>
            </div>'''
    html = replace_once(html, old_details, new_details, 'Checklist Details field')

    # -------------------------------------------------------------------------
    # State
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        '    let editingChecklistItemId = null;\n',
        '    let editingChecklistItemId = null;\n    let checklistRichEditor = null;\n',
        'Checklist rich editor state',
    )

    # -------------------------------------------------------------------------
    # Rich rendering in Checklist library and inside Ideas.
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        "              <p>${escapeHtml(item.details || '')}</p>",
        "              <div class=\"saved-note-content checklist-library-details\">${renderRichText(item.details || '')}</div>",
        'Checklist library rich details rendering',
    )

    html = replace_once(
        html,
        "          <div class=\"idea-checklist-details hidden\" data-checklist-details=\"${escapeAttr(item.id)}\">${escapeHtml(item.details || '')}${note ? `<br><button class=\"checklist-linked-note\" type=\"button\" data-open-note=\"${escapeAttr(note.id)}\">▤ Open connected note: ${escapeHtml(note.title)}</button>` : ''}</div>",
        "          <div class=\"idea-checklist-details hidden\" data-checklist-details=\"${escapeAttr(item.id)}\"><div class=\"saved-note-content checklist-rich-content\">${renderRichText(item.details || '')}</div>${note ? `<button class=\"checklist-linked-note\" type=\"button\" data-open-note=\"${escapeAttr(note.id)}\">▤ Open connected note: ${escapeHtml(note.title)}</button>` : ''}</div>",
        'Idea checklist rich details rendering',
    )

    # -------------------------------------------------------------------------
    # Editor implementation. It reuses the tested self-contained rich-text
    # helpers already used by My Notes and Idea Description/Private Notes.
    # -------------------------------------------------------------------------
    checklist_js = r'''

    function syncChecklistRichEditor() {
      if (!checklistRichEditor?.editable || !checklistRichEditor?.textarea) return;
      repairOrderedListContinuations(checklistRichEditor.editable);
      checklistRichEditor.textarea.value = sanitizeRichHtml(checklistRichEditor.editable.innerHTML);
    }

    function getChecklistDetailsContentForStorage() {
      if (checklistRichEditor?.editable && checklistRichEditor.shell?.classList.contains('ready')) {
        repairOrderedListContinuations(checklistRichEditor.editable);
        return sanitizeRichHtml(checklistRichEditor.editable.innerHTML).trim();
      }
      return $('checklistDetails')?.value || '';
    }

    function setChecklistDetailsRichContent(value = '') {
      const textarea = $('checklistDetails');
      const normalized = normalizeRichContent(value);
      if (checklistRichEditor?.editable) {
        checklistRichEditor.editable.innerHTML = normalized;
        repairOrderedListContinuations(checklistRichEditor.editable);
        const clean = sanitizeRichHtml(checklistRichEditor.editable.innerHTML);
        checklistRichEditor.editable.innerHTML = clean || '<p><br></p>';
        if (textarea) textarea.value = clean;
        updateIdeaRichToolbar(checklistRichEditor);
      } else if (textarea) {
        textarea.value = value || '';
      }
    }

    function execChecklistRichCommand(command, value = null) {
      checklistRichEditor?.editable?.focus();
      try { document.execCommand(command, false, value); }
      catch (error) { console.warn(`Checklist rich text command failed: ${command}`, error); }
      syncChecklistRichEditor();
      updateIdeaRichToolbar(checklistRichEditor);
    }

    function runChecklistRichCommand(command) {
      const editor = checklistRichEditor;
      if (!editor) return;
      switch (command) {
        case 'undo': execChecklistRichCommand('undo'); break;
        case 'redo': execChecklistRichCommand('redo'); break;
        case 'bold': execChecklistRichCommand('bold'); break;
        case 'italic': execChecklistRichCommand('italic'); break;
        case 'underline': execChecklistRichCommand('underline'); break;
        case 'strike': execChecklistRichCommand('strikeThrough'); break;
        case 'bulletList': execChecklistRichCommand('insertUnorderedList'); break;
        case 'orderedList': execChecklistRichCommand('insertOrderedList'); break;
        case 'indent': stepRichIndent(editor.editable, 1); break;
        case 'outdent': stepRichIndent(editor.editable, -1); break;
        case 'alignLeft': execChecklistRichCommand('justifyLeft'); break;
        case 'alignCenter': execChecklistRichCommand('justifyCenter'); break;
        case 'alignRight': execChecklistRichCommand('justifyRight'); break;
        case 'blockquote': execChecklistRichCommand('formatBlock', 'blockquote'); break;
        case 'horizontalRule': execChecklistRichCommand('insertHorizontalRule'); break;
        case 'clearFormatting': execChecklistRichCommand('removeFormat'); break;
        case 'link': {
          const existing = ideaRichClosest(editor, 'a');
          const previous = existing?.getAttribute('href') || '';
          const href = window.prompt('Enter the link URL. Leave blank to remove the current link.', previous);
          if (href === null) break;
          const trimmed = href.trim();
          if (!trimmed) execChecklistRichCommand('unlink');
          else {
            const safe = /^(https?:\/\/|mailto:)/i.test(trimmed) ? trimmed : `https://${trimmed}`;
            execChecklistRichCommand('createLink', safe);
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
      syncChecklistRichEditor();
      updateIdeaRichToolbar(editor);
    }

    function handleChecklistRichSmartList(event) {
      const editor = checklistRichEditor;
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
      syncChecklistRichEditor();
      updateIdeaRichToolbar(editor);
    }

    function initializeChecklistRichTextEditor() {
      const shell = $('checklistDetailsRichShell');
      const host = $('checklistDetailsRichEditor');
      const textarea = $('checklistDetails');
      const toolbar = $('checklistDetailsRichToolbar');
      if (!shell || !host || !textarea || !toolbar) return null;

      toolbar.innerHTML = buildIdeaRichToolbar('checklistDetailsRichBlockType');
      host.innerHTML = '<div class="tiptap" contenteditable="true" role="textbox" aria-multiline="true" spellcheck="true" data-placeholder="Explain what needs to be checked or implemented..."></div>';
      const editable = host.firstElementChild;
      checklistRichEditor = { shell, host, textarea, toolbar, editable, blockSelectId:'checklistDetailsRichBlockType' };
      editable.innerHTML = normalizeRichContent(textarea.value || '');

      editable.addEventListener('input', () => {
        syncChecklistRichEditor();
        updateIdeaRichToolbar(checklistRichEditor);
      });
      editable.addEventListener('keyup', () => updateIdeaRichToolbar(checklistRichEditor));
      editable.addEventListener('mouseup', () => updateIdeaRichToolbar(checklistRichEditor));
      editable.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
          event.preventDefault();
          $('checklistForm').requestSubmit();
          return;
        }
        if (event.key === 'Tab' && ideaRichSelectionInside(checklistRichEditor)) {
          event.preventDefault();
          stepRichIndent(editable, event.shiftKey ? -1 : 1);
          syncChecklistRichEditor();
          updateIdeaRichToolbar(checklistRichEditor);
          return;
        }
        handleChecklistRichSmartList(event);
      });
      editable.addEventListener('paste', (event) => {
        const htmlData = event.clipboardData?.getData('text/html') || '';
        const plainData = event.clipboardData?.getData('text/plain') || '';
        if (!htmlData) return;
        event.preventDefault();
        insertIdeaRichHtml(checklistRichEditor, sanitizeRichHtml(htmlData) || legacyTextToHtml(plainData));
        syncChecklistRichEditor();
      });

      toolbar.addEventListener('mousedown', (event) => {
        if (event.target.closest('button')) event.preventDefault();
      });
      toolbar.addEventListener('click', (event) => {
        const button = event.target.closest('[data-idea-rich-command]');
        if (!button || button.disabled) return;
        runChecklistRichCommand(button.dataset.ideaRichCommand);
      });
      $('checklistDetailsRichBlockType')?.addEventListener('change', (event) => {
        const map = { paragraph:'p', heading1:'h1', heading2:'h2', heading3:'h3' };
        execChecklistRichCommand('formatBlock', map[event.target.value] || 'p');
      });
      document.addEventListener('selectionchange', () => {
        if (ideaRichSelectionInside(checklistRichEditor)) updateIdeaRichToolbar(checklistRichEditor);
      });

      shell.classList.add('ready');
      syncChecklistRichEditor();
      updateIdeaRichToolbar(checklistRichEditor);
      return checklistRichEditor;
    }
'''

    html = replace_once(
        html,
        '\n    function resetChecklistEditor() {',
        checklist_js + '\n\n    function resetChecklistEditor() {',
        'Checklist rich editor JavaScript',
    )

    # -------------------------------------------------------------------------
    # Reset/open/save wiring.
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        "      $('checklistForm').reset();\n      $('checklistItemId').value = '';",
        "      $('checklistForm').reset();\n      setChecklistDetailsRichContent('');\n      $('checklistItemId').value = '';",
        'Checklist editor reset rich details',
    )

    html = replace_once(
        html,
        "        $('checklistDetails').value = item.details || '';",
        "        setChecklistDetailsRichContent(item.details || '');",
        'Checklist editor load rich details',
    )

    html = replace_once(
        html,
        "      const details = $('checklistDetails').value.trim();\n      if (!title) { $('checklistTitle').focus(); return; }\n      if (!details) { $('checklistDetails').focus(); return; }",
        "      const details = getChecklistDetailsContentForStorage().trim();\n      if (!title) { $('checklistTitle').focus(); return; }\n      if (!richTextToPlainText(details).trim()) { if (checklistRichEditor?.editable) checklistRichEditor.editable.focus(); else $('checklistDetails').focus(); return; }",
        'Checklist save rich details',
    )

    # -------------------------------------------------------------------------
    # Startup
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        '    initializeRichTextEditors();\n    initializeIdeaRichTextEditors();\n    initializeAuth();',
        '    initializeRichTextEditors();\n    initializeIdeaRichTextEditors();\n    initializeChecklistRichTextEditor();\n    initializeAuth();',
        'Checklist rich editor initialization',
    )

    INDEX.write_text(html, encoding='utf-8')

    # Bump PWA cache so installed apps get Stage 3.
    sw = SW.read_text(encoding='utf-8')
    if "pks-ideas-v24" in sw:
        sw = sw.replace("pks-ideas-v24", "pks-ideas-v25", 1)
    elif "pks-ideas-v25" not in sw:
        raise RuntimeError('Could not identify the service-worker cache version')
    SW.write_text(sw, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        marker = '## v25 rich text — Checklist Details'
        if marker not in readme:
            readme += '''\n\n## v25 rich text — Checklist Details\n\n- Checklist Details now uses the same self-contained Word-like rich-text editor as My Notes and Idea notes.\n- Supports headings, bold, italic, underline, strikethrough, bullet/numbered lists, stepped indentation, alignment, links, quotes, horizontal rules and tables.\n- Numbered-list continuation/start fixes are reused in Checklist Details.\n- Formatted details render in the Checklist library and when an item is expanded inside an Idea.\n- Existing plain-text checklist details remain compatible.\n- No Supabase schema change is required because checklist_items.details is already an unrestricted text column.\n'''
            README.write_text(readme, encoding='utf-8')

    print('Checklist rich-text Stage 3 patch applied successfully.')
