from pathlib import Path

INDEX = Path('index.html')
SW = Path('service-worker.js')
README = Path('README.md')


def replace_required(text: str, old: str, new: str, label: str, count: int | None = None) -> str:
    found = text.count(old)
    if found == 0:
        raise RuntimeError(f'Could not find expected block for {label}')
    if count is not None and found < count:
        raise RuntimeError(f'Expected at least {count} matches for {label}, found {found}')
    return text.replace(old, new)


html = INDEX.read_text(encoding='utf-8')

if 'const RICH_INDENT_STEP_PX = 24;' in html:
    print('Rich indent v22 already applied; nothing to do.')
else:
    # Make toolbar intent clearer. Indent/outdent are step controls; alignment
    # is a separate operation and should no longer look like indentation.
    toolbar_replacements = {
        'title="Outdent list item" aria-label="Outdent">⇤</button>': 'title="Decrease indent by one step" aria-label="Decrease indent">− Indent</button>',
        'title="Indent list item" aria-label="Indent">⇥</button>': 'title="Increase indent by one step" aria-label="Increase indent">+ Indent</button>',
        'data-rich-command="alignLeft" title="Align left" aria-label="Align left">≡←</button>': 'data-rich-command="alignLeft" title="Align left" aria-label="Align left">Left</button>',
        'data-rich-command="alignCenter" title="Align center" aria-label="Align center">≡</button>': 'data-rich-command="alignCenter" title="Align center" aria-label="Align center">Center</button>',
        'data-rich-command="alignRight" title="Align right" aria-label="Align right">→≡</button>': 'data-rich-command="alignRight" title="Align right" aria-label="Align right">Right</button>',
        'data-idea-rich-command="outdent" title="Outdent" aria-label="Outdent">⇤</button>': 'data-idea-rich-command="outdent" title="Decrease indent by one step" aria-label="Decrease indent">− Indent</button>',
        'data-idea-rich-command="indent" title="Indent" aria-label="Indent">⇥</button>': 'data-idea-rich-command="indent" title="Increase indent by one step" aria-label="Increase indent">+ Indent</button>',
        'data-idea-rich-command="alignLeft" title="Align left" aria-label="Align left">≡←</button>': 'data-idea-rich-command="alignLeft" title="Align left" aria-label="Align left">Left</button>',
        'data-idea-rich-command="alignCenter" title="Align center" aria-label="Align center">≡</button>': 'data-idea-rich-command="alignCenter" title="Align center" aria-label="Align center">Center</button>',
        'data-idea-rich-command="alignRight" title="Align right" aria-label="Align right">→≡</button>': 'data-idea-rich-command="alignRight" title="Align right" aria-label="Align right">Right</button>',
    }
    for old, new in toolbar_replacements.items():
        if old in html:
            html = html.replace(old, new)

    # Preserve safe step indentation when rich HTML is sanitized before save/render.
    old_sanitize = """        if (['P','DIV','H1','H2','H3','TH','TD'].includes(tag)) {
          const style = sourceElement.getAttribute('style') || '';
          const match = style.match(/text-align\\s*:\\s*(left|center|right|justify)/i);
          if (match) element.style.textAlign = match[1].toLowerCase();
          const align = (sourceElement.getAttribute('align') || '').toLowerCase();
          if (['left','center','right','justify'].includes(align)) element.style.textAlign = align;
        }"""
    new_sanitize = """        if (['P','DIV','H1','H2','H3','BLOCKQUOTE','TH','TD'].includes(tag)) {
          const style = sourceElement.getAttribute('style') || '';
          const match = style.match(/text-align\\s*:\\s*(left|center|right|justify)/i);
          if (match) element.style.textAlign = match[1].toLowerCase();
          const align = (sourceElement.getAttribute('align') || '').toLowerCase();
          if (['left','center','right','justify'].includes(align)) element.style.textAlign = align;

          const marginMatch = style.match(/margin-left\\s*:\\s*(\\d+(?:\\.\\d+)?)px/i);
          if (marginMatch) {
            const rawPixels = Number.parseFloat(marginMatch[1]) || 0;
            const steppedPixels = Math.min(192, Math.max(0, Math.round(rawPixels / 24) * 24));
            if (steppedPixels > 0) element.style.marginLeft = `${steppedPixels}px`;
          }
        }"""
    html = replace_required(html, old_sanitize, new_sanitize, 'rich HTML sanitizer alignment block')

    # Add a shared step-indentation helper. Normal paragraphs/headings move by
    # exactly 24px per click. List items still nest one list level at a time.
    helper = r'''

    const RICH_INDENT_STEP_PX = 24;
    const RICH_INDENT_MAX_LEVEL = 8;

    function stepRichIndent(editable, delta) {
      const selection = window.getSelection();
      if (!editable || !selection || !selection.rangeCount || !selection.isCollapsed || !editable.contains(selection.anchorNode)) return false;

      let node = selection.anchorNode;
      if (node?.nodeType === Node.TEXT_NODE) node = node.parentElement;
      const block = node?.closest?.('li,p,div,h1,h2,h3,blockquote');
      if (!block || !editable.contains(block)) return false;

      // Lists keep semantic nesting/numbering. Each click changes one list level.
      if (block.tagName === 'LI') {
        try {
          document.execCommand(delta > 0 ? 'indent' : 'outdent', false, null);
          return true;
        } catch {
          return false;
        }
      }

      const currentPixels = Number.parseFloat(block.style.marginLeft || '0') || 0;
      const currentLevel = Math.round(currentPixels / RICH_INDENT_STEP_PX);
      const nextLevel = Math.max(0, Math.min(RICH_INDENT_MAX_LEVEL, currentLevel + delta));
      block.style.marginLeft = nextLevel ? `${nextLevel * RICH_INDENT_STEP_PX}px` : '';
      return true;
    }
'''
    marker = '    function runMyNoteRichCommand(command) {'
    if marker not in html:
        raise RuntimeError('Could not find My Notes rich command function')
    html = html.replace(marker, helper + '\n\n' + marker, 1)

    # My Notes toolbar indent/outdent now uses the 24px step helper.
    html = replace_required(html, "        case 'indent': execRichCommand('indent'); break;", "        case 'indent': stepRichIndent(getMyNoteRichEditable(), 1); break;", 'My Notes indent command')
    html = replace_required(html, "        case 'outdent': execRichCommand('outdent'); break;", "        case 'outdent': stepRichIndent(getMyNoteRichEditable(), -1); break;", 'My Notes outdent command')

    old_my_note_tab = """    function handleRichTab(event) {
      if (event.key !== 'Tab' || !closestEditorElement('li')) return;
      event.preventDefault();
      document.execCommand(event.shiftKey ? 'outdent' : 'indent', false, null);
      syncMyNoteRichEditorToTextarea();
      refreshMyNoteDirtyState();
      updateMyNoteRichToolbar();
    }"""
    new_my_note_tab = """    function handleRichTab(event) {
      if (event.key !== 'Tab' || !selectionInsideMyNoteEditor()) return;
      event.preventDefault();
      stepRichIndent(getMyNoteRichEditable(), event.shiftKey ? -1 : 1);
      syncMyNoteRichEditorToTextarea();
      refreshMyNoteDirtyState();
      updateMyNoteRichToolbar();
    }"""
    html = replace_required(html, old_my_note_tab, new_my_note_tab, 'My Notes Tab indentation')

    # Idea Description + Private Notes use the same step helper.
    html = replace_required(html, "        case 'indent': execIdeaRichCommand(editor, 'indent'); break;", "        case 'indent': stepRichIndent(editor?.editable, 1); break;", 'Idea indent command')
    html = replace_required(html, "        case 'outdent': execIdeaRichCommand(editor, 'outdent'); break;", "        case 'outdent': stepRichIndent(editor?.editable, -1); break;", 'Idea outdent command')

    old_idea_tab = """        if (event.key === 'Tab' && ideaRichClosest(editor, 'li')) {
          event.preventDefault();
          document.execCommand(event.shiftKey ? 'outdent' : 'indent', false, null);
          syncIdeaRichEditor(editor);
          markEditorInteraction();
          updateIdeaRichToolbar(editor);
        }"""
    new_idea_tab = """        if (event.key === 'Tab' && ideaRichSelectionInside(editor)) {
          event.preventDefault();
          stepRichIndent(editor.editable, event.shiftKey ? -1 : 1);
          syncIdeaRichEditor(editor);
          markEditorInteraction();
          updateIdeaRichToolbar(editor);
        }"""
    html = replace_required(html, old_idea_tab, new_idea_tab, 'Idea Tab indentation')

    INDEX.write_text(html, encoding='utf-8')

    sw = SW.read_text(encoding='utf-8')
    if 'pks-ideas-v21' in sw:
        sw = sw.replace('pks-ideas-v21', 'pks-ideas-v22', 1)
    elif 'pks-ideas-v22' not in sw:
        raise RuntimeError('Could not identify service worker cache version')
    SW.write_text(sw, encoding='utf-8')

    if README.exists():
        readme = README.read_text(encoding='utf-8')
        if '## v22 stepped indentation' not in readme:
            readme += '''\n\n## v22 stepped indentation\n\n- Rich-text Indent/Outdent now moves normal text exactly 24px per step, up to 8 levels.\n- List items still nest one list level at a time, preserving numbering/bullets.\n- Tab / Shift+Tab uses the same one-step indentation behavior.\n- Toolbar controls now clearly label Indent separately from Left/Center/Right alignment.\n- Safe `margin-left` step values are preserved by HTML sanitization.\n- No Supabase SQL changes are required.\n'''
        README.write_text(readme, encoding='utf-8')

    print('Rich indent v22 patch applied successfully.')
