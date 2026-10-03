from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')

html = INDEX.read_text(encoding='utf-8')

old = r'''    function repairOrderedListContinuations(editable) {
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
    }'''

new = r'''    function isEmptyRichBlock(element) {
      if (!element) return false;
      if (!['P','DIV'].includes(element.tagName)) return false;
      return !(element.textContent || '').trim() && !element.querySelector('img,table,ul,ol,hr');
    }

    function repairOrderedListContinuations(editable) {
      if (!editable) return;

      // Only top-level numbered lists participate in automatic continuation.
      // Nested numbered lists keep the browser's own numbering semantics.
      [...editable.children].filter((element) => element.tagName === 'OL').forEach((orderedList) => {
        let previous = orderedList.previousElementSibling;
        let crossedBulletDetails = false;

        // Empty spacer paragraphs are allowed around bullet-detail blocks, but
        // real paragraphs/headings are section breaks and reset numbering.
        while (previous) {
          if (previous.tagName === 'UL') {
            crossedBulletDetails = true;
            previous = previous.previousElementSibling;
            continue;
          }
          if (isEmptyRichBlock(previous)) {
            previous = previous.previousElementSibling;
            continue;
          }
          break;
        }

        if (crossedBulletDetails && previous?.tagName === 'OL') {
          const previousStart = Math.max(1, Number.parseInt(previous.getAttribute('start') || '1', 10) || 1);
          const previousCount = directListItemCount(previous);
          if (previousCount) {
            const expectedStart = Math.min(10000, previousStart + previousCount);
            orderedList.setAttribute('start', String(expectedStart));
            return;
          }
        }

        // This is a new independent list. Never inherit a stale start="2"
        // (or another continuation value) from a previous browser edit.
        orderedList.removeAttribute('start');
      });
    }'''

if 'function isEmptyRichBlock(element)' not in html:
    if old not in html:
        raise RuntimeError('Could not find the existing ordered-list continuation function')
    html = html.replace(old, new, 1)
else:
    print('v24 ordered-list start repair already present')

INDEX.write_text(html, encoding='utf-8')

sw = SW.read_text(encoding='utf-8')
if 'pks-ideas-v23' in sw:
    sw = sw.replace('pks-ideas-v23', 'pks-ideas-v24', 1)
elif 'pks-ideas-v24' not in sw:
    raise RuntimeError('Could not identify service-worker cache version')
SW.write_text(sw, encoding='utf-8')

if README.exists():
    readme = README.read_text(encoding='utf-8')
    if '## v24 numbered-list start repair' not in readme:
        readme += '''\n\n## v24 numbered-list start repair\n\n- Independent top-level numbered lists always start at 1.\n- Numbering only continues across intervening bullet-detail lists.\n- Real paragraph/heading section breaks reset numbering back to 1.\n- Empty spacer paragraphs around bullet details do not break continuation.\n- Fixes stale `start=2` values after Backspace, Enter, or typing `1.` + Space.\n- Applies to My Notes, Idea Description and Private Notes.\n- No Supabase SQL changes are required.\n'''
        README.write_text(readme, encoding='utf-8')

print('v24 numbered-list start repair applied successfully')
