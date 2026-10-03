from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

if 'rich-toolbar-more-button' in html:
    print('Rich toolbar polish v28 already applied; nothing to do.')
else:
    css = r'''

    /* Rich editor toolbar polish — v28 */
    .rich-toolbar-more-group {
      display:none;
      margin-left:auto;
      border-right:0 !important;
      padding-right:0 !important;
    }
    .rich-toolbar-more-button {
      min-width:auto;
      padding:6px 10px;
      white-space:nowrap;
    }

    @media (max-width:700px) {
      .rich-editor-toolbar.rich-toolbar-polished {
        flex-wrap:wrap;
        overflow-x:hidden;
        white-space:normal;
        gap:5px;
        align-items:center;
      }
      .rich-editor-toolbar.rich-toolbar-polished > .rich-editor-toolbar-group {
        border-right:0;
        padding-right:0;
      }
      .rich-editor-toolbar.rich-toolbar-polished .rich-toolbar-advanced {
        display:none;
      }
      .rich-editor-toolbar.rich-toolbar-polished.rich-toolbar-more-open .rich-toolbar-advanced {
        display:inline-flex;
      }
      .rich-editor-toolbar.rich-toolbar-polished .rich-toolbar-more-group {
        display:inline-flex;
      }
      .rich-editor-toolbar.rich-toolbar-polished .rich-tool-button {
        min-width:36px;
        min-height:36px;
        padding:6px 8px;
      }
      .rich-editor-toolbar.rich-toolbar-polished .rich-tool-select {
        min-width:118px;
        width:auto;
      }
      .rich-editor-toolbar.rich-toolbar-polished.rich-toolbar-more-open {
        align-items:flex-start;
      }
      .rich-editor-toolbar.rich-toolbar-polished.rich-toolbar-more-open .rich-toolbar-more-group {
        margin-left:0;
      }
    }

    @media (max-width:420px) {
      .rich-editor-toolbar.rich-toolbar-polished .rich-tool-button {
        min-width:34px;
        min-height:34px;
        font-size:12px;
      }
      .rich-editor-toolbar.rich-toolbar-polished .rich-toolbar-essential:nth-of-type(3) {
        flex:1 1 auto;
      }
    }
'''

    html = replace_once(
        html,
        '\n\n    /* Checklist workspace + per-idea checklist */',
        css + '\n\n    /* Checklist workspace + per-idea checklist */',
        'toolbar polish CSS',
    )

    js = r'''

    function enhanceRichToolbarForMobile(toolbar) {
      if (!toolbar || toolbar.dataset.mobilePolished === 'true') return;
      const groups = [...toolbar.querySelectorAll(':scope > .rich-editor-toolbar-group')];
      if (!groups.length) return;

      // Keep Undo/Redo, basic text formatting and list/indent controls visible.
      const essentialIndexes = new Set([0, 2, 3]);
      groups.forEach((group, index) => {
        group.classList.add(essentialIndexes.has(index) ? 'rich-toolbar-essential' : 'rich-toolbar-advanced');
      });

      const moreGroup = document.createElement('span');
      moreGroup.className = 'rich-editor-toolbar-group rich-toolbar-more-group';
      const moreButton = document.createElement('button');
      moreButton.type = 'button';
      moreButton.className = 'rich-tool-button rich-toolbar-more-button';
      moreButton.textContent = 'More ▾';
      moreButton.setAttribute('aria-expanded', 'false');
      moreButton.setAttribute('aria-label', 'Show more formatting tools');
      moreGroup.appendChild(moreButton);
      toolbar.appendChild(moreGroup);

      moreButton.addEventListener('mousedown', (event) => event.preventDefault());
      moreButton.addEventListener('click', () => {
        const opening = !toolbar.classList.contains('rich-toolbar-more-open');
        toolbar.classList.toggle('rich-toolbar-more-open', opening);
        moreButton.textContent = opening ? 'Less ▴' : 'More ▾';
        moreButton.setAttribute('aria-expanded', String(opening));
        moreButton.setAttribute('aria-label', opening ? 'Hide extra formatting tools' : 'Show more formatting tools');
      });

      toolbar.classList.add('rich-toolbar-polished');
      toolbar.dataset.mobilePolished = 'true';
    }

    function initializeRichToolbarPolish() {
      requestAnimationFrame(() => {
        document.querySelectorAll('.rich-editor-toolbar').forEach(enhanceRichToolbarForMobile);
      });
    }
'''

    html = replace_once(
        html,
        '\n    async function initializeRichTextEditors() {',
        js + '\n\n    async function initializeRichTextEditors() {',
        'toolbar polish JavaScript',
    )

    # All editor toolbars have been created by this point during startup.
    if '    initializeDashboardRichTextEditor();\n    initializeAuth();' in html:
        html = html.replace(
            '    initializeDashboardRichTextEditor();\n    initializeAuth();',
            '    initializeDashboardRichTextEditor();\n    initializeRichToolbarPolish();\n    initializeAuth();',
            1,
        )
    elif '    initializeAuth();' in html:
        html = html.replace('    initializeAuth();', '    initializeRichToolbarPolish();\n    initializeAuth();', 1)
    else:
        raise RuntimeError('Could not find startup initialization block')

    INDEX.write_text(html, encoding='utf-8')

    sw = SW.read_text(encoding='utf-8')
    if 'pks-ideas-v27' in sw:
        sw = sw.replace('pks-ideas-v27', 'pks-ideas-v28', 1)
    elif 'pks-ideas-v28' not in sw:
        raise RuntimeError('Could not identify service-worker cache version')
    SW.write_text(sw, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        marker = '## v28 mobile rich-text toolbar polish'
        if marker not in readme:
            readme += '''\n\n## v28 mobile rich-text toolbar polish\n\n- Rich-text toolbars are now compact and responsive on phones.\n- Undo/Redo, bold/italic/underline/strike and list/indent controls stay visible.\n- Headings, alignment, links, quotes, tables and other advanced controls move behind a `More` button on small screens.\n- Desktop toolbars keep the full control set visible.\n- Applies to My Notes, Idea Description, Private Notes, Checklist Details and Dashboard Notes.\n- No Supabase SQL changes are required.\n'''
            README.write_text(readme, encoding='utf-8')

    print('Rich toolbar mobile polish v28 applied successfully.')
