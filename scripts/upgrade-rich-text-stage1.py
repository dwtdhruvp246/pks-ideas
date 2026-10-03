from pathlib import Path
import re

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')

html = INDEX.read_text(encoding='utf-8')

# Add a placeholder rule for the self-contained contenteditable surface.
css_anchor = "    .rich-editor-surface .tiptap {\n      min-height:250px; padding:14px; outline:none; color:var(--text); line-height:1.65; overflow-wrap:anywhere;\n    }"
css_replacement = css_anchor + "\n    .rich-editor-surface .tiptap:empty::before {\n      content: attr(data-placeholder); color:#9ca3af; pointer-events:none;\n    }\n    .rich-editor-surface .tiptap:focus { outline:none; }"
if css_anchor in html and 'data-placeholder' not in html:
    html = html.replace(css_anchor, css_replacement, 1)

start_marker = "    function looksLikeRichHtml(value = '') {"
end_marker = "\n    function getMyNoteSnapshot() {"
start = html.find(start_marker)
end = html.find(end_marker, start)
if start < 0 or end < 0:
    raise RuntimeError('Could not locate the current rich-editor helper block in index.html')

native_rich_js = r'''    function looksLikeRichHtml(value = '') {
      return /<(?:p|div|h[1-6]|ul|ol|li|strong|b|em|i|u|s|blockquote|table|thead|tbody|tr|th|td|hr|br|a|span)\b/i.test(String(value || ''));
    }

    function legacyTextToHtml(value = '') {
      const text = String(value || '');
      if (!text) return '<p><br></p>';
      const paragraphs = text.replace(/\r\n?/g, '\n').split(/\n{2,}/);
      return paragraphs.map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\n/g, '<br>')}</p>`).join('');
    }

    function sanitizeRichHtml(value = '') {
      const raw = String(value || '');
      const template = document.createElement('template');
      template.innerHTML = raw;

      const allowedTags = new Set([
        'P','DIV','BR','STRONG','B','EM','I','U','S','H1','H2','H3','UL','OL','LI',
        'BLOCKQUOTE','HR','A','TABLE','THEAD','TBODY','TR','TH','TD','SPAN'
      ]);
      const removeEntirely = new Set(['SCRIPT','STYLE','IFRAME','OBJECT','EMBED','SVG','MATH','LINK','META']);

      [...template.content.querySelectorAll('*')].forEach((element) => {
        const tag = element.tagName.toUpperCase();
        if (removeEntirely.has(tag)) {
          element.remove();
          return;
        }
        if (!allowedTags.has(tag)) {
          element.replaceWith(...element.childNodes);
          return;
        }

        [...element.attributes].forEach((attr) => element.removeAttribute(attr.name));

        if (tag === 'A') {
          const original = element.getAttribute('data-sanitized-href') || '';
          if (original) element.removeAttribute('data-sanitized-href');
        }
      });

      // A second pass is used because the first pass strips every attribute.
      // Recover safe values from the original HTML by parsing it separately.
      const source = document.createElement('template');
      source.innerHTML = raw;
      const cleanedElements = [...template.content.querySelectorAll('*')];
      const sourceElements = [...source.content.querySelectorAll('*')].filter((el) => allowedTags.has(el.tagName.toUpperCase()));
      cleanedElements.forEach((element, index) => {
        const sourceElement = sourceElements[index];
        if (!sourceElement) return;
        const tag = element.tagName.toUpperCase();
        if (tag === 'A') {
          const href = sourceElement.getAttribute('href') || '';
          try {
            const parsed = new URL(href, location.origin);
            if (['http:', 'https:', 'mailto:'].includes(parsed.protocol)) {
              element.setAttribute('href', parsed.protocol === 'mailto:' ? href : parsed.href);
              element.setAttribute('target', '_blank');
              element.setAttribute('rel', 'noopener noreferrer');
            }
          } catch {}
        }
        if (['TH','TD'].includes(tag)) {
          const colspan = Number.parseInt(sourceElement.getAttribute('colspan') || '1', 10);
          const rowspan = Number.parseInt(sourceElement.getAttribute('rowspan') || '1', 10);
          if (colspan > 1 && colspan <= 20) element.setAttribute('colspan', String(colspan));
          if (rowspan > 1 && rowspan <= 50) element.setAttribute('rowspan', String(rowspan));
        }
        if (['P','DIV','H1','H2','H3','TH','TD'].includes(tag)) {
          const style = sourceElement.getAttribute('style') || '';
          const match = style.match(/text-align\s*:\s*(left|center|right|justify)/i);
          if (match) element.style.textAlign = match[1].toLowerCase();
          const align = (sourceElement.getAttribute('align') || '').toLowerCase();
          if (['left','center','right','justify'].includes(align)) element.style.textAlign = align;
        }
      });

      return template.innerHTML;
    }

    function normalizeRichContent(value = '') {
      const raw = String(value || '');
      if (!raw.trim()) return '<p><br></p>';
      return sanitizeRichHtml(looksLikeRichHtml(raw) ? raw : legacyTextToHtml(raw));
    }

    function richTextToPlainText(value = '') {
      const raw = String(value || '');
      if (!looksLikeRichHtml(raw)) return raw;
      const holder = document.createElement('div');
      holder.innerHTML = sanitizeRichHtml(raw);
      return (holder.textContent || holder.innerText || '').replace(/\s+/g, ' ').trim();
    }

    function renderRichText(value = '') {
      return sanitizeRichHtml(normalizeRichContent(value));
    }

    function getMyNoteRichEditable() {
      return $('myNoteRichEditable');
    }

    function getMyNoteContentForStorage() {
      const editable = getMyNoteRichEditable();
      if (editable && $('myNoteRichEditorShell')?.classList.contains('ready')) {
        return sanitizeRichHtml(editable.innerHTML).trim();
      }
      return $('myNoteContent')?.value || '';
    }

    function setMyNoteRichContent(value = '') {
      const textarea = $('myNoteContent');
      const editable = getMyNoteRichEditable();
      const normalized = normalizeRichContent(value);
      if (editable) {
        editable.innerHTML = normalized;
        const clean = sanitizeRichHtml(editable.innerHTML);
        editable.innerHTML = clean || '<p><br></p>';
        if (textarea) textarea.value = clean;
        updateMyNoteRichToolbar();
      } else if (textarea) {
        textarea.value = value || '';
      }
    }

    function syncMyNoteRichEditorToTextarea() {
      const editable = getMyNoteRichEditable();
      const textarea = $('myNoteContent');
      if (!editable || !textarea) return;
      textarea.value = sanitizeRichHtml(editable.innerHTML);
    }

    function selectionInsideMyNoteEditor() {
      const editable = getMyNoteRichEditable();
      const selection = window.getSelection();
      if (!editable || !selection || !selection.rangeCount) return false;
      return editable.contains(selection.anchorNode);
    }

    function closestEditorElement(selector) {
      if (!selectionInsideMyNoteEditor()) return null;
      const selection = window.getSelection();
      let node = selection.anchorNode;
      if (node?.nodeType === Node.TEXT_NODE) node = node.parentElement;
      return node?.closest?.(selector) || null;
    }

    function updateMyNoteRichToolbar() {
      const toolbar = $('myNoteRichToolbar');
      if (!toolbar || !getMyNoteRichEditable()) return;
      const stateCommands = {
        bold: 'bold', italic: 'italic', underline: 'underline', strike: 'strikeThrough',
        bulletList: 'insertUnorderedList', orderedList: 'insertOrderedList',
        alignLeft: 'justifyLeft', alignCenter: 'justifyCenter', alignRight: 'justifyRight'
      };
      Object.entries(stateCommands).forEach(([buttonName, command]) => {
        let active = false;
        try { active = selectionInsideMyNoteEditor() && document.queryCommandState(command); } catch {}
        toolbar.querySelector(`[data-rich-command="${buttonName}"]`)?.classList.toggle('active', Boolean(active));
      });
      toolbar.querySelector('[data-rich-command="blockquote"]')?.classList.toggle('active', Boolean(closestEditorElement('blockquote')));
      toolbar.querySelector('[data-rich-command="link"]')?.classList.toggle('active', Boolean(closestEditorElement('a')));
      const inTable = Boolean(closestEditorElement('table'));
      toolbar.querySelectorAll('[data-rich-table-only]').forEach((button) => { button.disabled = !inTable; });

      const blockSelect = $('myNoteRichBlockType');
      if (blockSelect) {
        const block = closestEditorElement('h1,h2,h3,p,div');
        const tag = block?.tagName?.toLowerCase();
        blockSelect.value = tag === 'h1' ? 'heading1' : tag === 'h2' ? 'heading2' : tag === 'h3' ? 'heading3' : 'paragraph';
      }
    }

    function focusMyNoteRichEditor() {
      const editable = getMyNoteRichEditable();
      editable?.focus();
    }

    function execRichCommand(command, value = null) {
      focusMyNoteRichEditor();
      try { document.execCommand(command, false, value); } catch (error) { console.warn(`Rich text command failed: ${command}`, error); }
      syncMyNoteRichEditorToTextarea();
      refreshMyNoteDirtyState();
      updateMyNoteRichToolbar();
    }

    function insertHtmlAtRichSelection(html) {
      focusMyNoteRichEditor();
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

    function currentTableCell() {
      return closestEditorElement('th,td');
    }

    function placeCaretInCell(cell) {
      if (!cell) return;
      const range = document.createRange();
      range.selectNodeContents(cell);
      range.collapse(true);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      focusMyNoteRichEditor();
    }

    function addRichTableRow() {
      const cell = currentTableCell();
      const row = cell?.closest('tr');
      if (!row) return;
      const newRow = row.cloneNode(true);
      [...newRow.children].forEach((newCell) => { newCell.innerHTML = '<br>'; });
      row.after(newRow);
      placeCaretInCell(newRow.cells[Math.min(cell.cellIndex, newRow.cells.length - 1)]);
    }

    function addRichTableColumn() {
      const cell = currentTableCell();
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
      const targetRow = cell.closest('tr');
      placeCaretInCell(targetRow?.cells[index + 1]);
    }

    function deleteRichTableRow() {
      const cell = currentTableCell();
      const row = cell?.closest('tr');
      const table = cell?.closest('table');
      if (!row || !table) return;
      if (table.rows.length <= 1) table.remove();
      else row.remove();
      focusMyNoteRichEditor();
    }

    function deleteRichTableColumn() {
      const cell = currentTableCell();
      const table = cell?.closest('table');
      if (!cell || !table) return;
      const index = cell.cellIndex;
      if ((table.rows[0]?.cells.length || 0) <= 1) table.remove();
      else [...table.rows].forEach((row) => row.cells[index]?.remove());
      focusMyNoteRichEditor();
    }

    function deleteRichTable() {
      const table = closestEditorElement('table');
      table?.remove();
      focusMyNoteRichEditor();
    }

    function runMyNoteRichCommand(command) {
      switch (command) {
        case 'undo': execRichCommand('undo'); break;
        case 'redo': execRichCommand('redo'); break;
        case 'bold': execRichCommand('bold'); break;
        case 'italic': execRichCommand('italic'); break;
        case 'underline': execRichCommand('underline'); break;
        case 'strike': execRichCommand('strikeThrough'); break;
        case 'bulletList': execRichCommand('insertUnorderedList'); break;
        case 'orderedList': execRichCommand('insertOrderedList'); break;
        case 'indent': execRichCommand('indent'); break;
        case 'outdent': execRichCommand('outdent'); break;
        case 'alignLeft': execRichCommand('justifyLeft'); break;
        case 'alignCenter': execRichCommand('justifyCenter'); break;
        case 'alignRight': execRichCommand('justifyRight'); break;
        case 'blockquote': execRichCommand('formatBlock', 'blockquote'); break;
        case 'horizontalRule': execRichCommand('insertHorizontalRule'); break;
        case 'clearFormatting': execRichCommand('removeFormat'); break;
        case 'link': {
          const existing = closestEditorElement('a');
          const previous = existing?.getAttribute('href') || '';
          const href = window.prompt('Enter the link URL. Leave blank to remove the current link.', previous);
          if (href === null) break;
          const trimmed = href.trim();
          if (!trimmed) execRichCommand('unlink');
          else {
            const safe = /^(https?:\/\/|mailto:)/i.test(trimmed) ? trimmed : `https://${trimmed}`;
            execRichCommand('createLink', safe);
            const link = closestEditorElement('a');
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
          insertHtmlAtRichSelection(table);
          syncMyNoteRichEditorToTextarea();
          refreshMyNoteDirtyState();
          break;
        }
        case 'addRow': addRichTableRow(); break;
        case 'addColumn': addRichTableColumn(); break;
        case 'deleteRow': deleteRichTableRow(); break;
        case 'deleteColumn': deleteRichTableColumn(); break;
        case 'deleteTable': deleteRichTable(); break;
      }
      syncMyNoteRichEditorToTextarea();
      refreshMyNoteDirtyState();
      updateMyNoteRichToolbar();
    }

    function handleRichSmartList(event) {
      if (event.key !== ' ' || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
      const editable = getMyNoteRichEditable();
      const selection = window.getSelection();
      if (!editable || !selection?.rangeCount || !selection.isCollapsed || !editable.contains(selection.anchorNode)) return;
      const range = selection.getRangeAt(0);
      let block = range.startContainer.nodeType === Node.TEXT_NODE ? range.startContainer.parentElement : range.startContainer;
      block = block?.closest?.('p,div');
      if (!block || !editable.contains(block)) return;
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
      syncMyNoteRichEditorToTextarea();
      refreshMyNoteDirtyState();
    }

    function handleRichTab(event) {
      if (event.key !== 'Tab' || !closestEditorElement('li')) return;
      event.preventDefault();
      document.execCommand(event.shiftKey ? 'outdent' : 'indent', false, null);
      syncMyNoteRichEditorToTextarea();
      refreshMyNoteDirtyState();
      updateMyNoteRichToolbar();
    }

    async function initializeRichTextEditors() {
      if (richEditorLoadPromise) return richEditorLoadPromise;
      richEditorLoadPromise = Promise.resolve().then(() => {
        const shell = $('myNoteRichEditorShell');
        const host = $('myNoteRichEditor');
        const textarea = $('myNoteContent');
        if (!shell || !host || !textarea) return null;

        host.innerHTML = '<div id="myNoteRichEditable" class="tiptap" contenteditable="true" role="textbox" aria-multiline="true" spellcheck="true" data-placeholder="Write the useful information, lesson, code idea, process, or reminder you want to keep..."></div>';
        const editable = getMyNoteRichEditable();
        editable.innerHTML = normalizeRichContent(textarea.value || '');

        myNoteRichEditor = {
          getHTML: () => editable.innerHTML,
          commands: {
            setContent: (content) => { editable.innerHTML = normalizeRichContent(content); syncMyNoteRichEditorToTextarea(); updateMyNoteRichToolbar(); },
            focus: () => editable.focus()
          }
        };

        editable.addEventListener('input', () => {
          syncMyNoteRichEditorToTextarea();
          refreshMyNoteDirtyState();
          updateMyNoteRichToolbar();
        });
        editable.addEventListener('keyup', updateMyNoteRichToolbar);
        editable.addEventListener('mouseup', updateMyNoteRichToolbar);
        editable.addEventListener('keydown', (event) => {
          if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
            event.preventDefault();
            $('myNoteForm').requestSubmit();
            return;
          }
          handleRichSmartList(event);
          handleRichTab(event);
        });
        editable.addEventListener('paste', (event) => {
          const htmlData = event.clipboardData?.getData('text/html') || '';
          const plainData = event.clipboardData?.getData('text/plain') || '';
          if (!htmlData) return;
          event.preventDefault();
          insertHtmlAtRichSelection(sanitizeRichHtml(htmlData) || legacyTextToHtml(plainData));
          syncMyNoteRichEditorToTextarea();
          refreshMyNoteDirtyState();
        });

        $('myNoteRichToolbar')?.addEventListener('mousedown', (event) => {
          if (event.target.closest('button')) event.preventDefault();
        });
        $('myNoteRichToolbar')?.addEventListener('click', (event) => {
          const button = event.target.closest('[data-rich-command]');
          if (!button || button.disabled) return;
          runMyNoteRichCommand(button.dataset.richCommand);
        });
        $('myNoteRichBlockType')?.addEventListener('change', (event) => {
          const map = { paragraph: 'p', heading1: 'h1', heading2: 'h2', heading3: 'h3' };
          execRichCommand('formatBlock', map[event.target.value] || 'p');
        });
        document.addEventListener('selectionchange', () => {
          if (selectionInsideMyNoteEditor()) updateMyNoteRichToolbar();
        });

        shell.classList.remove('loading');
        shell.classList.add('ready');
        syncMyNoteRichEditorToTextarea();
        updateMyNoteRichToolbar();
        renderPersonalNotes();
        return myNoteRichEditor;
      }).catch((error) => {
        $('myNoteRichEditorShell')?.classList.remove('loading');
        console.warn('Self-contained rich text editor initialization failed. Falling back to the normal textarea.', error);
        return null;
      });
      return richEditorLoadPromise;
    }
'''

html = html[:start] + native_rich_js + html[end:]
INDEX.write_text(html, encoding='utf-8')

sw = SW.read_text(encoding='utf-8')
if "pks-ideas-v19" in sw:
    sw = sw.replace("pks-ideas-v19", "pks-ideas-v20", 1)
elif "pks-ideas-v20" not in sw:
    raise RuntimeError('Could not identify expected service-worker cache version')
SW.write_text(sw, encoding='utf-8')

if README.exists():
    readme = README.read_text(encoding='utf-8')
    note = '''\n\n## v20 rich text reliability fix\n\n- Replaced the external Tiptap/CDN dependency with a self-contained browser rich-text editor.\n- My Notes formatting now works without loading third-party editor modules.\n- Keeps headings, bold, italic, underline, strikethrough, lists, smart `1.` / `-` list creation, Tab/Shift+Tab indentation, alignment, links, quotes, horizontal rules, tables, undo/redo and HTML sanitization.\n- No Supabase SQL changes are required.\n'''
    if '## v20 rich text reliability fix' not in readme:
        README.write_text(readme + note, encoding='utf-8')

print('Applied self-contained rich text editor fix.')
