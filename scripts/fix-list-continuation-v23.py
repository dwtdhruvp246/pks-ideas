from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

if 'function repairOrderedListContinuations' in html:
    print('v23 list continuation already applied; nothing to do.')
else:
    # ---------------------------------------------------------------------
    # Preserve <ol start="..."> through sanitization so continued numbering
    # survives database storage, reloads and cross-device use.
    # ---------------------------------------------------------------------
    old_sanitize = """        if (['TH','TD'].includes(tag)) {
          const colspan = Number.parseInt(sourceElement.getAttribute('colspan') || '1', 10);
          const rowspan = Number.parseInt(sourceElement.getAttribute('rowspan') || '1', 10);
          if (colspan > 1 && colspan <= 20) element.setAttribute('colspan', String(colspan));
          if (rowspan > 1 && rowspan <= 50) element.setAttribute('rowspan', String(rowspan));
        }
        if (['P','DIV','H1','H2','H3','BLOCKQUOTE','TH','TD'].includes(tag)) {"""
    new_sanitize = """        if (['TH','TD'].includes(tag)) {
          const colspan = Number.parseInt(sourceElement.getAttribute('colspan') || '1', 10);
          const rowspan = Number.parseInt(sourceElement.getAttribute('rowspan') || '1', 10);
          if (colspan > 1 && colspan <= 20) element.setAttribute('colspan', String(colspan));
          if (rowspan > 1 && rowspan <= 50) element.setAttribute('rowspan', String(rowspan));
        }
        if (tag === 'OL') {
          const start = Number.parseInt(sourceElement.getAttribute('start') || '1', 10);
          if (Number.isFinite(start) && start > 1 && start <= 10000) element.setAttribute('start', String(start));
        }
        if (['P','DIV','H1','H2','H3','BLOCKQUOTE','TH','TD'].includes(tag)) {"""
    html = replace_once(html, old_sanitize, new_sanitize, 'OL start sanitizer')

    # ---------------------------------------------------------------------
    # When a user changes one numbered item into bullets, contenteditable
    # typically produces OL -> UL -> OL. The trailing OL normally restarts
    # at 1. Repair it to continue from the preceding OL count.
    #
    # We intentionally bridge only across UL siblings. A separate numbered
    # list after a paragraph/heading still starts at 1, so independent lists
    # are not accidentally joined.
    # ---------------------------------------------------------------------
    helper = r'''

    function directListItemCount(list) {
      if (!list) return 0;
      return [...list.children].filter((child) => child.tagName === 'LI').length;
    }

    function repairOrderedListContinuations(editable) {
      if (!editable) return;
      editable.querySelectorAll('ol').forEach((orderedList) => {
        let previous = orderedList.previousElementSibling;
        let crossedBulletDetails = false;

        while (previous?.tagName === 'UL') {
          crossedBulletDetails = true;
          previous = previous.previousElementSibling;
        }

        if (!crossedBulletDetails || previous?.tagName !== 'OL') return;

        const previousStart = Math.max(1, Number.parseInt(previous.getAttribute('start') || '1', 10) || 1);
        const previousCount = directListItemCount(previous);
        if (!previousCount) return;

        const expectedStart = Math.min(10000, previousStart + previousCount);
        orderedList.setAttribute('start', String(expectedStart));
      });
    }
'''
    marker = '    function syncIdeaRichEditor(editor) {'
    if marker not in html:
        raise RuntimeError('Could not find Idea rich sync function')
    html = html.replace(marker, helper + '\n\n' + marker, 1)

    old_idea_sync = """    function syncIdeaRichEditor(editor) {
      if (!editor?.editable || !editor?.textarea) return;
      editor.textarea.value = sanitizeRichHtml(editor.editable.innerHTML);
    }"""
    new_idea_sync = """    function syncIdeaRichEditor(editor) {
      if (!editor?.editable || !editor?.textarea) return;
      repairOrderedListContinuations(editor.editable);
      editor.textarea.value = sanitizeRichHtml(editor.editable.innerHTML);
    }"""
    html = replace_once(html, old_idea_sync, new_idea_sync, 'Idea rich sync repair')

    old_note_sync = """    function syncMyNoteRichEditorToTextarea() {
      const editable = getMyNoteRichEditable();
      const textarea = $('myNoteContent');
      if (!editable || !textarea) return;
      textarea.value = sanitizeRichHtml(editable.innerHTML);
    }"""
    new_note_sync = """    function syncMyNoteRichEditorToTextarea() {
      const editable = getMyNoteRichEditable();
      const textarea = $('myNoteContent');
      if (!editable || !textarea) return;
      repairOrderedListContinuations(editable);
      textarea.value = sanitizeRichHtml(editable.innerHTML);
    }"""
    html = replace_once(html, old_note_sync, new_note_sync, 'My Notes rich sync repair')

    # Repair immediately when server/saved content is placed into an editor,
    # so old notes with OL/UL/OL structure display correctly before typing.
    old_idea_set = """      if (editor?.editable) {
        editor.editable.innerHTML = normalized;
        const clean = sanitizeRichHtml(editor.editable.innerHTML);"""
    new_idea_set = """      if (editor?.editable) {
        editor.editable.innerHTML = normalized;
        repairOrderedListContinuations(editor.editable);
        const clean = sanitizeRichHtml(editor.editable.innerHTML);"""
    html = replace_once(html, old_idea_set, new_idea_set, 'Idea set rich content repair')

    old_note_set = """      if (editable) {
        editable.innerHTML = normalized;
        const clean = sanitizeRichHtml(editable.innerHTML);"""
    new_note_set = """      if (editable) {
        editable.innerHTML = normalized;
        repairOrderedListContinuations(editable);
        const clean = sanitizeRichHtml(editable.innerHTML);"""
    html = replace_once(html, old_note_set, new_note_set, 'My Notes set rich content repair')

    INDEX.write_text(html, encoding='utf-8')

    # PWA cache bump.
    sw = SW.read_text(encoding='utf-8')
    if 'pks-ideas-v22' in sw:
        sw = sw.replace('pks-ideas-v22', 'pks-ideas-v23', 1)
    elif 'pks-ideas-v23' not in sw:
        raise RuntimeError('Could not identify service worker cache version')
    SW.write_text(sw, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        if '## v23 numbered-list continuation' not in readme:
            readme += '''\n\n## v23 numbered-list continuation\n\n- Numbered lists now continue after an intervening bulleted detail list instead of restarting at 1.\n- Example: `1. Dashboard` → bullet details → `2. Workspace`.\n- Continued numbering is stored using the safe HTML `ol start` attribute and survives save/reload.\n- Applied to My Notes, Idea Description, and Idea Private Notes.\n- Independent numbered lists separated by normal paragraphs/headings still start at 1.\n- No Supabase SQL changes are required.\n'''
        README.write_text(readme, encoding='utf-8')

    print('v23 numbered-list continuation patch applied successfully.')
