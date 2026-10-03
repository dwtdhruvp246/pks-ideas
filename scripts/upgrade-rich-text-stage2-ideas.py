from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

if 'ideaDescriptionRichShell' in html and 'ideaNotesRichShell' in html:
    print('Stage 2 already applied; nothing to do.')
else:
    # -------------------------------------------------------------------------
    # CSS: reuse the self-contained My Notes editor styling for Idea fields.
    # -------------------------------------------------------------------------
    stage2_css = r'''

    /* Rich text editor — Stage 2: Idea Description + Private Notes */
    .rich-editor-shell.ready > .rich-editor-fallback { display:none; }
    .idea-rich-editor-shell .rich-editor-surface .tiptap { min-height:180px; }
    .idea-private-rich .rich-editor-surface .tiptap { min-height:220px; }
    .private-notes-field.expanded .idea-private-rich .rich-editor-surface .tiptap {
      min-height:min(62vh, 680px);
    }
    .idea-rich-hint { margin-top:7px; color:var(--muted); font-size:11px; line-height:1.45; }

    @media (max-width:560px) {
      .idea-rich-editor-shell .rich-editor-surface .tiptap { min-height:190px; }
      .idea-private-rich .rich-editor-surface .tiptap { min-height:230px; }
      .private-notes-field.expanded .idea-private-rich .rich-editor-surface .tiptap { min-height:64vh; }
    }
'''
    html = replace_once(
        html,
        '\n\n    /* Checklist workspace + per-idea checklist */',
        stage2_css + '\n\n    /* Checklist workspace + per-idea checklist */',
        'Stage 2 rich editor CSS',
    )

    # -------------------------------------------------------------------------
    # HTML: progressively enhance the existing textareas. The textareas remain
    # as fallbacks and as compatibility mirrors for existing form code.
    # -------------------------------------------------------------------------
    old_description = '<div class="field span-2"><label for="ideaDescription">Description</label><textarea id="ideaDescription" maxlength="2000" placeholder="Describe the problem, solution and main features..."></textarea></div>'
    new_description = '''<div class="field span-2">
                  <label for="ideaDescription">Description</label>
                  <div id="ideaDescriptionRichShell" class="rich-editor-shell idea-rich-editor-shell">
                    <div id="ideaDescriptionRichToolbar" class="rich-editor-toolbar" aria-label="Description formatting toolbar"></div>
                    <div id="ideaDescriptionRichEditor" class="rich-editor-surface"></div>
                    <textarea id="ideaDescription" class="rich-editor-fallback" placeholder="Describe the problem, solution and main features..."></textarea>
                  </div>
                  <div class="idea-rich-hint">Use headings, formatting, lists, indentation, links and tables just like My Notes.</div>
                </div>'''
    html = replace_once(html, old_description, new_description, 'Idea Description field')

    old_private = '<textarea id="ideaNotes" placeholder="Research, pricing, competitors, next actions..."></textarea>'
    new_private = '''<div id="ideaNotesRichShell" class="rich-editor-shell idea-rich-editor-shell idea-private-rich">
                    <div id="ideaNotesRichToolbar" class="rich-editor-toolbar" aria-label="Private notes formatting toolbar"></div>
                    <div id="ideaNotesRichEditor" class="rich-editor-surface"></div>
                    <textarea id="ideaNotes" class="rich-editor-fallback" placeholder="Research, pricing, competitors, next actions..."></textarea>
                  </div>
                  <div class="idea-rich-hint">Formatting is saved with this idea. Ctrl/Cmd + Enter saves the idea.</div>'''
    html = replace_once(html, old_private, new_private, 'Idea Private Notes field')

    # -------------------------------------------------------------------------
    # State variables.
    # -------------------------------------------------------------------------
    html = replace_once(
        html,
        '    let richEditorLoadPromise = null;\n',
        "    let richEditorLoadPromise = null;\n    let ideaDescriptionRichEditor = null;\n    let ideaNotesRichEditor = null;\n",
        'Idea rich editor state',
    )

    # -------------------------------------------------------------------------
    # Generic self-contained editor implementation for Idea fields. This uses
    # the same browser-native editing approach as the working My Notes editor.
    # -------------------------------------------------------------------------
    idea_editor_js = r'''

    function buildIdeaRichToolbar(blockSelectId) {
      return `<span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="undo" title="Undo" aria-label="Undo">↶</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="redo" title="Redo" aria-label="Redo">↷</button>
        </span>
        <span class="rich-editor-toolbar-group">
          <select id="${blockSelectId}" class="rich-tool-select" aria-label="Paragraph style">
            <option value="paragraph">Paragraph</option>
            <option value="heading1">Heading 1</option>
            <option value="heading2">Heading 2</option>
            <option value="heading3">Heading 3</option>
          </select>
        </span>
        <span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="bold" title="Bold" aria-label="Bold"><strong>B</strong></button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="italic" title="Italic" aria-label="Italic"><em>I</em></button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="underline" title="Underline" aria-label="Underline"><u>U</u></button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="strike" title="Strikethrough" aria-label="Strikethrough"><s>S</s></button>
        </span>
        <span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="bulletList" title="Bulleted list" aria-label="Bulleted list">• List</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="orderedList" title="Numbered list" aria-label="Numbered list">1. List</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="outdent" title="Outdent" aria-label="Outdent">⇤</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="indent" title="Indent" aria-label="Indent">⇥</button>
        </span>
        <span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="alignLeft" title="Align left" aria-label="Align left">≡←</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="alignCenter" title="Align center" aria-label="Align center">≡</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="alignRight" title="Align right" aria-label="Align right">→≡</button>
        </span>
        <span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="link" title="Add or edit link" aria-label="Add or edit link">🔗</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="blockquote" title="Quote" aria-label="Quote">❝</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="horizontalRule" title="Horizontal line" aria-label="Horizontal line">─</button>
        </span>
        <span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="insertTable" title="Insert table" aria-label="Insert table">▦ Table</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="addRow" data-idea-rich-table-only title="Add table row">+Row</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="addColumn" data-idea-rich-table-only title="Add table column">+Col</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="deleteRow" data-idea-rich-table-only title="Delete table row">−Row</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="deleteColumn" data-idea-rich-table-only title="Delete table column">−Col</button>
          <button class="rich-tool-button" type="button" data-idea-rich-command="deleteTable" data-idea-rich-table-only title="Delete table">×Tbl</button>
        </span>
        <span class="rich-editor-toolbar-group">
          <button class="rich-tool-button" type="button" data-idea-rich-command="clearFormatting" title="Clear formatting" aria-label="Clear formatting">Tx</button>
        </span>`;
    }

    function ideaRichSelectionInside(editor) {
      const selection = window.getSelection();
      if (!editor?.editable || !selection || !selection.rangeCount) return false;
      return editor.editable.contains(selection.anchorNode);
    }

    function ideaRichClosest(editor, selector) {
      if (!ideaRichSelectionInside(editor)) return null;
      const selection = window.getSelection();
      let node = selection.anchorNode;
      if (node?.nodeType === Node.TEXT_NODE) node = node.parentElement;
      const found = node?.closest?.(selector) || null;
      return found && editor.editable.contains(found) ? found : null;
    }

    function syncIdeaRichEditor(editor) {
      if (!editor?.editable || !editor?.textarea) return;
      editor.textarea.value = sanitizeRichHtml(editor.editable.innerHTML);
    }

    function getIdeaRichContent(editor, textareaId) {
      if (editor?.editable && editor.shell?.classList.contains('ready')) {
        return sanitizeRichHtml(editor.editable.innerHTML).trim();
      }
      return $(textareaId)?.value || '';
    }

    function setIdeaRichContent(editor, textareaId, value = '') {
      const textarea = $(textareaId);
      const normalized = normalizeRichContent(value);
      if (editor?.editable) {
        editor.editable.innerHTML = normalized;
        const clean = sanitizeRichHtml(editor.editable.innerHTML);
        editor.editable.innerHTML = clean || '<p><br></p>';
        if (textarea) textarea.value = clean;
        updateIdeaRichToolbar(editor);
      } else if (textarea) {
        textarea.value = value || '';
      }
    }

    function getIdeaDescriptionContentForStorage() {
      return getIdeaRichContent(ideaDescriptionRichEditor, 'ideaDescription');
    }

    function getIdeaNotesContentForStorage() {
      return getIdeaRichContent(ideaNotesRichEditor, 'ideaNotes');
    }

    function setIdeaDescriptionRichContent(value = '') {
      setIdeaRichContent(ideaDescriptionRichEditor, 'ideaDescription', value);
    }

    function setIdeaNotesRichContent(value = '') {
      setIdeaRichContent(ideaNotesRichEditor, 'ideaNotes', value);
    }

    function optionalRichValue(value = '') {
      const clean = sanitizeRichHtml(value).trim();
      return richTextToPlainText(clean).trim() ? clean : null;
    }

    function updateIdeaRichToolbar(editor) {
      if (!editor?.toolbar || !editor?.editable) return;
      const stateCommands = {
        bold: 'bold', italic: 'italic', underline: 'underline', strike: 'strikeThrough',
        bulletList: 'insertUnorderedList', orderedList: 'insertOrderedList',
        alignLeft: 'justifyLeft', alignCenter: 'justifyCenter', alignRight: 'justifyRight'
      };
      Object.entries(stateCommands).forEach(([buttonName, command]) => {
        let active = false;
        try { active = ideaRichSelectionInside(editor) && document.queryCommandState(command); } catch {}
        editor.toolbar.querySelector(`[data-idea-rich-command="${buttonName}"]`)?.classList.toggle('active', Boolean(active));
      });
      editor.toolbar.querySelector('[data-idea-rich-command="blockquote"]')?.classList.toggle('active', Boolean(ideaRichClosest(editor, 'blockquote')));
      editor.toolbar.querySelector('[data-idea-rich-command="link"]')?.classList.toggle('active', Boolean(ideaRichClosest(editor, 'a')));
      const inTable = Boolean(ideaRichClosest(editor, 'table'));
      editor.toolbar.querySelectorAll('[data-idea-rich-table-only]').forEach((button) => { button.disabled = !inTable; });
      const blockSelect = $(editor.blockSelectId);
      if (blockSelect) {
        const block = ideaRichClosest(editor, 'h1,h2,h3,p,div');
        const tag = block?.tagName?.toLowerCase();
        blockSelect.value = tag === 'h1' ? 'heading1' : tag === 'h2' ? 'heading2' : tag === 'h3' ? 'heading3' : 'paragraph';
      }
    }

    function execIdeaRichCommand(editor, command, value = null) {
      editor?.editable?.focus();
      try { document.execCommand(command, false, value); }
      catch (error) { console.warn(`Idea rich text command failed: ${command}`, error); }
      syncIdeaRichEditor(editor);
      markEditorInteraction();
      updateIdeaRichToolbar(editor);
    }

    function insertIdeaRichHtml(editor, html) {
      editor?.editable?.focus();
      try {
        if (document.queryCommandSupported?.('insertHTML')) {
          document.execCommand('insertHTML', false, html);
          return;
        }
      } catch {}
      const selection = window.getSelection();
      if (!selection?.rangeCount) return;
      const range = selection.getRangeAt(0);
      range.deleteContents();
      const fragment = range.createContextualFragment(html);
      const last = fragment.lastChild;
      range.insertNode(fragment);
      if (last) {
        range.setStartAfter(last);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    }

    function currentIdeaRichTableCell(editor) {
      return ideaRichClosest(editor, 'th,td');
    }

    function placeIdeaRichCaret(editor, cell) {
      if (!cell) return;
      const range = document.createRange();
      range.selectNodeContents(cell);
      range.collapse(true);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      editor.editable.focus();
    }

    function addIdeaRichTableRow(editor) {
      const cell = currentIdeaRichTableCell(editor);
      const row = cell?.closest('tr');
      if (!row) return;
      const newRow = row.cloneNode(true);
      [...newRow.children].forEach((newCell) => { newCell.innerHTML = '<br>'; });
      row.after(newRow);
      placeIdeaRichCaret(editor, newRow.cells[Math.min(cell.cellIndex, newRow.cells.length - 1)]);
    }

    function addIdeaRichTableColumn(editor) {
      const cell = currentIdeaRichTableCell(editor);
      const table = cell?.closest('table');
      if (!cell || !table) return;
      const index = cell.cellIndex;
      [...table.rows].forEach((row) => {
        const reference = row.cells[index];
        const tag = reference?.tagName?.toLowerCase() === 'th' ? 'th' : 'td';
        const newCell = document.createElement(tag);
        newCell.innerHTML = '<br>';
        if (reference) reference.after(newCell); else row.appendChild(newCell);
      });
      placeIdeaRichCaret(editor, cell.closest('tr')?.cells[index + 1]);
    }

    function deleteIdeaRichTableRow(editor) {
      const cell = currentIdeaRichTableCell(editor);
      const row = cell?.closest('tr');
      const table = cell?.closest('table');
      if (!row || !table) return;
      if (table.rows.length <= 1) table.remove(); else row.remove();
      editor.editable.focus();
    }

    function deleteIdeaRichTableColumn(editor) {
      const cell = currentIdeaRichTableCell(editor);
      const table = cell?.closest('table');
      if (!cell || !table) return;
      const index = cell.cellIndex;
      if ((table.rows[0]?.cells.length || 0) <= 1) table.remove();
      else [...table.rows].forEach((row) => row.cells[index]?.remove());
      editor.editable.focus();
    }

    function runIdeaRichCommand(editor, command) {
      switch (command) {
        case 'undo': execIdeaRichCommand(editor, 'undo'); break;
        case 'redo': execIdeaRichCommand(editor, 'redo'); break;
        case 'bold': execIdeaRichCommand(editor, 'bold'); break;
        case 'italic': execIdeaRichCommand(editor, 'italic'); break;
        case 'underline': execIdeaRichCommand(editor, 'underline'); break;
        case 'strike': execIdeaRichCommand(editor, 'strikeThrough'); break;
        case 'bulletList': execIdeaRichCommand(editor, 'insertUnorderedList'); break;
        case 'orderedList': execIdeaRichCommand(editor, 'insertOrderedList'); break;
        case 'indent': execIdeaRichCommand(editor, 'indent'); break;
        case 'outdent': execIdeaRichCommand(editor, 'outdent'); break;
        case 'alignLeft': execIdeaRichCommand(editor, 'justifyLeft'); break;
        case 'alignCenter': execIdeaRichCommand(editor, 'justifyCenter'); break;
        case 'alignRight': execIdeaRichCommand(editor, 'justifyRight'); break;
        case 'blockquote': execIdeaRichCommand(editor, 'formatBlock', 'blockquote'); break;
        case 'horizontalRule': execIdeaRichCommand(editor, 'insertHorizontalRule'); break;
        case 'clearFormatting': execIdeaRichCommand(editor, 'removeFormat'); break;
        case 'link': {
          const existing = ideaRichClosest(editor, 'a');
          const previous = existing?.getAttribute('href') || '';
          const href = window.prompt('Enter the link URL. Leave blank to remove the current link.', previous);
          if (href === null) break;
          const trimmed = href.trim();
          if (!trimmed) execIdeaRichCommand(editor, 'unlink');
          else {
            const safe = /^(https?:\/\/|mailto:)/i.test(trimmed) ? trimmed : `https://${trimmed}`;
            execIdeaRichCommand(editor, 'createLink', safe);
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
      syncIdeaRichEditor(editor);
      markEditorInteraction();
      updateIdeaRichToolbar(editor);
    }

    function handleIdeaRichSmartList(editor, event) {
      if (event.key !== ' ' || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
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
      syncIdeaRichEditor(editor);
      markEditorInteraction();
    }

    function createIdeaRichEditor({ shellId, hostId, textareaId, toolbarId, blockSelectId, placeholder }) {
      const shell = $(shellId);
      const host = $(hostId);
      const textarea = $(textareaId);
      const toolbar = $(toolbarId);
      if (!shell || !host || !textarea || !toolbar) return null;

      toolbar.innerHTML = buildIdeaRichToolbar(blockSelectId);
      host.innerHTML = `<div class="tiptap" contenteditable="true" role="textbox" aria-multiline="true" spellcheck="true" data-placeholder="${escapeAttr(placeholder)}"></div>`;
      const editable = host.firstElementChild;
      const editor = { shell, host, textarea, toolbar, editable, blockSelectId };
      editable.innerHTML = normalizeRichContent(textarea.value || '');

      editable.addEventListener('input', () => {
        syncIdeaRichEditor(editor);
        markEditorInteraction();
        updateIdeaRichToolbar(editor);
      });
      editable.addEventListener('keyup', () => updateIdeaRichToolbar(editor));
      editable.addEventListener('mouseup', () => updateIdeaRichToolbar(editor));
      editable.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
          event.preventDefault();
          $('ideaForm').requestSubmit();
          return;
        }
        if (event.key === 'Tab' && ideaRichClosest(editor, 'li')) {
          event.preventDefault();
          document.execCommand(event.shiftKey ? 'outdent' : 'indent', false, null);
          syncIdeaRichEditor(editor);
          markEditorInteraction();
          updateIdeaRichToolbar(editor);
          return;
        }
        handleIdeaRichSmartList(editor, event);
      });
      editable.addEventListener('paste', (event) => {
        const htmlData = event.clipboardData?.getData('text/html') || '';
        const plainData = event.clipboardData?.getData('text/plain') || '';
        if (!htmlData) return;
        event.preventDefault();
        insertIdeaRichHtml(editor, sanitizeRichHtml(htmlData) || legacyTextToHtml(plainData));
        syncIdeaRichEditor(editor);
        markEditorInteraction();
      });

      toolbar.addEventListener('mousedown', (event) => {
        if (event.target.closest('button')) event.preventDefault();
      });
      toolbar.addEventListener('click', (event) => {
        const button = event.target.closest('[data-idea-rich-command]');
        if (!button || button.disabled) return;
        runIdeaRichCommand(editor, button.dataset.ideaRichCommand);
      });
      $(blockSelectId)?.addEventListener('change', (event) => {
        const map = { paragraph:'p', heading1:'h1', heading2:'h2', heading3:'h3' };
        execIdeaRichCommand(editor, 'formatBlock', map[event.target.value] || 'p');
      });

      shell.classList.add('ready');
      syncIdeaRichEditor(editor);
      updateIdeaRichToolbar(editor);
      return editor;
    }

    function initializeIdeaRichTextEditors() {
      ideaDescriptionRichEditor = createIdeaRichEditor({
        shellId:'ideaDescriptionRichShell', hostId:'ideaDescriptionRichEditor', textareaId:'ideaDescription',
        toolbarId:'ideaDescriptionRichToolbar', blockSelectId:'ideaDescriptionRichBlockType',
        placeholder:'Describe the problem, solution and main features...'
      });
      ideaNotesRichEditor = createIdeaRichEditor({
        shellId:'ideaNotesRichShell', hostId:'ideaNotesRichEditor', textareaId:'ideaNotes',
        toolbarId:'ideaNotesRichToolbar', blockSelectId:'ideaNotesRichBlockType',
        placeholder:'Research, pricing, competitors, next actions...'
      });
      document.addEventListener('selectionchange', () => {
        if (ideaRichSelectionInside(ideaDescriptionRichEditor)) updateIdeaRichToolbar(ideaDescriptionRichEditor);
        if (ideaRichSelectionInside(ideaNotesRichEditor)) updateIdeaRichToolbar(ideaNotesRichEditor);
      });
    }
'''

    html = replace_once(
        html,
        '\n    function getIdeaFormSnapshot() {',
        idea_editor_js + '\n\n    function getIdeaFormSnapshot() {',
        'Idea rich editor JavaScript',
    )

    # -------------------------------------------------------------------------
    # Dirty-state snapshots now use rich HTML rather than hidden textarea text.
    # -------------------------------------------------------------------------
    html = html.replace("        description: $('ideaDescription').value,", "        description: getIdeaDescriptionContentForStorage(),")
    html = html.replace("        notes: $('ideaNotes').value,", "        notes: getIdeaNotesContentForStorage(),")

    # -------------------------------------------------------------------------
    # Server/manual reload and normal idea opening must load rich content into
    # the contenteditable editors, not just their hidden textarea mirrors.
    # Replace all matching refresh/open assignments safely.
    # -------------------------------------------------------------------------
    html = html.replace("$('ideaDescription').value = freshIdea.description || '';", "setIdeaDescriptionRichContent(freshIdea.description || '');")
    html = html.replace("$('ideaNotes').value = freshIdea.notes || '';", "setIdeaNotesRichContent(freshIdea.notes || '');")
    html = html.replace("$('ideaDescription').value = idea.description || '';", "setIdeaDescriptionRichContent(idea.description || '');")
    html = html.replace("$('ideaNotes').value = idea.notes || '';", "setIdeaNotesRichContent(idea.notes || '');")

    # Clear both visual editors when preparing a new/open form before values load.
    html = replace_once(
        html,
        "      $('ideaForm').reset();\n      if ($('privateNotesField'))",
        "      $('ideaForm').reset();\n      setIdeaDescriptionRichContent('');\n      setIdeaNotesRichContent('');\n      if ($('privateNotesField'))",
        'Idea form rich editor reset',
    )

    # -------------------------------------------------------------------------
    # Search + dashboard preview should search/display readable text, not tags.
    # -------------------------------------------------------------------------
    old_haystack = "const haystack = [idea.title, idea.description, idea.category, idea.status, idea.tech_stack, idea.supabase_account, idea.cloudflare_account, idea.notes, idea.target_user, idea.next_step, idea.website_url, idea.github_url].join(' ').toLowerCase();"
    new_haystack = "const haystack = [idea.title, richTextToPlainText(idea.description || ''), idea.category, idea.status, idea.tech_stack, idea.supabase_account, idea.cloudflare_account, richTextToPlainText(idea.notes || ''), idea.target_user, idea.next_step, idea.website_url, idea.github_url].join(' ').toLowerCase();"
    html = replace_once(html, old_haystack, new_haystack, 'Idea rich text search')

    html = replace_once(
        html,
        "        const notes = idea.notes || idea.description || '—';",
        "        const notes = richTextToPlainText(idea.notes || idea.description || '') || '—';",
        'Idea dashboard notes preview',
    )

    # -------------------------------------------------------------------------
    # Save sanitized rich HTML. Empty rich editors remain NULL rather than
    # storing an empty paragraph.
    # -------------------------------------------------------------------------
    html = html.replace(
        "        description: $('ideaDescription').value.trim() || null,",
        "        description: optionalRichValue(getIdeaDescriptionContentForStorage()),",
    )
    html = html.replace(
        "        notes: $('ideaNotes').value.trim() || null,",
        "        notes: optionalRichValue(getIdeaNotesContentForStorage()),",
    )

    # Initialize the Idea editors before auth/bootstrap begins.
    html = replace_once(
        html,
        '    initializeRichTextEditors();\n    initializeAuth();',
        '    initializeRichTextEditors();\n    initializeIdeaRichTextEditors();\n    initializeAuth();',
        'Idea rich editor initialization',
    )

    INDEX.write_text(html, encoding='utf-8')

    # PWA cache bump.
    sw = SW.read_text(encoding='utf-8')
    if "pks-ideas-v20" in sw:
        sw = sw.replace("pks-ideas-v20", "pks-ideas-v21", 1)
    elif "pks-ideas-v21" not in sw:
        raise RuntimeError('Could not identify the expected service-worker cache version')
    SW.write_text(sw, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        marker = '## v21 rich text — Idea fields'
        if marker not in readme:
            readme += '''\n\n## v21 rich text — Idea fields\n\n- Idea **Description** now uses the same self-contained Word-like rich-text editor as My Notes.\n- Idea **Private Notes** now uses the same editor and keeps its Expand/Collapse behavior.\n- Rich content participates in unsaved-change detection, stale-data/manual reload protection, idea search, and dashboard previews.\n- Existing plain-text Description/Private Notes remain compatible and are converted only when saved after editing.\n- Run the supplied SQL manually to remove old Description/Notes length checks before storing larger formatted content.\n'''
            README.write_text(readme, encoding='utf-8')

    print('Rich text Stage 2 patch applied successfully.')
