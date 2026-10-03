from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Could not find expected block for {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

if 'toggleDashboardNoteFormatting' in html:
    print('Dashboard compact rich editor v27 already applied; nothing to do.')
else:
    compact_css = r'''

    /* Dashboard Notes — compact rich editor layout (v27) */
    .dashboard-note-head-actions {
      display:flex;
      align-items:center;
      gap:8px;
      flex:0 0 auto;
    }
    .dashboard-format-toggle {
      padding:8px 11px;
      font-size:12px;
    }

    /* Keep the Dashboard clean by hiding the Word toolbar until requested. */
    .dashboard-rich-editor-shell.ready .rich-editor-toolbar {
      display:none;
    }
    .dashboard-rich-editor-shell.ready.formatting-open .rich-editor-toolbar,
    .dashboard-notes.expanded .dashboard-rich-editor-shell.ready .rich-editor-toolbar {
      display:flex;
    }

    /* The dashboard is a quick view. Long notes scroll inside the card. */
    .dashboard-notes:not(.expanded) .dashboard-rich-editor-shell .rich-editor-surface .tiptap {
      min-height:128px;
      height:128px;
      max-height:128px;
      overflow-y:auto;
      padding:13px 14px;
    }
    .dashboard-notes:not(.expanded) .dashboard-rich-editor-shell {
      flex:0 0 auto;
    }
    .dashboard-notes:not(.expanded) .dashboard-rich-editor-shell.formatting-open .rich-editor-surface .tiptap {
      min-height:112px;
      height:112px;
      max-height:112px;
    }

    .dashboard-notes.expanded .dashboard-format-toggle {
      display:none;
    }
    .dashboard-notes.expanded .dashboard-rich-editor-shell .rich-editor-surface .tiptap {
      min-height:56vh;
      height:auto;
      max-height:none;
      overflow-y:auto;
    }

    .dashboard-note-hint {
      margin-top:8px;
      line-height:1.4;
    }

    @media (max-width:800px) {
      .dashboard-notes:not(.expanded) .dashboard-rich-editor-shell .rich-editor-surface .tiptap {
        min-height:150px;
        height:150px;
        max-height:150px;
      }
      .dashboard-notes:not(.expanded) .dashboard-rich-editor-shell.formatting-open .rich-editor-surface .tiptap {
        min-height:130px;
        height:130px;
        max-height:130px;
      }
    }

    @media (max-width:560px) {
      .dashboard-notes-head {
        align-items:flex-start;
      }
      .dashboard-note-head-actions {
        gap:6px;
      }
      .dashboard-format-toggle,
      .dashboard-note-expand {
        padding:8px 9px;
        min-height:38px;
      }
      .dashboard-rich-editor-shell.ready.formatting-open .rich-editor-toolbar,
      .dashboard-notes.expanded .dashboard-rich-editor-shell.ready .rich-editor-toolbar {
        padding:6px;
      }
      .dashboard-notes.expanded .dashboard-rich-editor-shell .rich-editor-surface .tiptap {
        min-height:62vh;
      }
    }
'''

    html = replace_once(
        html,
        '\n\n    /* Checklist workspace + per-idea checklist */',
        compact_css + '\n\n    /* Checklist workspace + per-idea checklist */',
        'compact Dashboard Notes CSS',
    )

    old_head_button = '''                <button id="toggleDashboardNotesSize" class="btn btn-secondary dashboard-note-expand" type="button" aria-expanded="false">⛶ Expand</button>'''
    new_head_buttons = '''                <div class="dashboard-note-head-actions">
                  <button id="toggleDashboardNoteFormatting" class="btn btn-secondary dashboard-format-toggle" type="button" aria-expanded="false">Aa Format</button>
                  <button id="toggleDashboardNotesSize" class="btn btn-secondary dashboard-note-expand" type="button" aria-expanded="false">⛶ Expand</button>
                </div>'''
    html = replace_once(html, old_head_button, new_head_buttons, 'Dashboard Notes header actions')

    html = replace_once(
        html,
        '<div class="dashboard-note-hint">Enter creates a new paragraph/list item • Ctrl/Cmd + Enter saves</div>',
        '<div class="dashboard-note-hint">Enter = new paragraph / next list item • Ctrl/Cmd + Enter = save</div>',
        'Dashboard Notes hint copy',
    )

    # Add formatting toggle and compact-reset behavior without disturbing the
    # existing expand handler.
    listener_anchor = "    $('saveDashboardNoteButton').addEventListener('click', saveDashboardNote);"
    listener_block = r'''    $('toggleDashboardNoteFormatting').addEventListener('click', () => {
      const shell = $('dashboardNoteRichShell');
      const button = $('toggleDashboardNoteFormatting');
      const panel = document.querySelector('.dashboard-notes');
      if (!shell || !button || !panel || panel.classList.contains('expanded')) return;
      const opening = !shell.classList.contains('formatting-open');
      shell.classList.toggle('formatting-open', opening);
      button.setAttribute('aria-expanded', String(opening));
      button.textContent = opening ? 'Aa Hide format' : 'Aa Format';
      if (opening) window.setTimeout(() => dashboardRichEditor?.editable?.focus({ preventScroll:true }), 40);
    });

    $('toggleDashboardNotesSize').addEventListener('click', () => {
      const panel = document.querySelector('.dashboard-notes');
      const shell = $('dashboardNoteRichShell');
      const formatButton = $('toggleDashboardNoteFormatting');
      if (!panel || !shell || !formatButton) return;
      if (!panel.classList.contains('expanded')) {
        shell.classList.remove('formatting-open');
        formatButton.setAttribute('aria-expanded', 'false');
        formatButton.textContent = 'Aa Format';
      }
    });

''' + listener_anchor
    html = replace_once(html, listener_anchor, listener_block, 'Dashboard format toggle listeners')

    INDEX.write_text(html, encoding='utf-8')

    sw = SW.read_text(encoding='utf-8')
    if 'pks-ideas-v26' in sw:
        sw = sw.replace('pks-ideas-v26', 'pks-ideas-v27', 1)
    elif 'pks-ideas-v27' not in sw:
        raise RuntimeError('Could not identify service-worker cache version')
    SW.write_text(sw, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        marker = '## v27 compact Dashboard Notes editor'
        if marker not in readme:
            readme += '''\n\n## v27 compact Dashboard Notes editor\n\n- Dashboard Notes now keeps the full formatting toolbar hidden by default.\n- Added an `Aa Format` control to show/hide formatting without expanding the card.\n- Expanding Dashboard Notes automatically exposes the full formatting toolbar.\n- Long dashboard notes scroll inside a compact editor instead of stretching the dashboard.\n- Rich-text saving, realtime dirty-state protection and all existing formatting remain unchanged.\n'''
            README.write_text(readme, encoding='utf-8')

    print('Dashboard Notes compact rich-editor patch applied successfully.')
