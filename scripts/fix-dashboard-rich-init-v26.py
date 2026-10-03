from pathlib import Path

INDEX = Path('index.html')


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'Missing expected block: {label}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

old_load = """      const value = data?.content || '';
      const input = $('dashboardNoteInput');
      if (input && dashboardNoteIsDirty()) {
        if (value !== dashboardNoteSavedValue) {
          dashboardNoteSavedValue = value;
          updateDashboardNoteStatus('unsaved', 'Changed on another device — your local text is not saved');
        }
        return;
      }
      if (input) setDashboardNoteRichContent(value);
      dashboardNoteSavedValue = sanitizeRichHtml(normalizeRichContent(value));"""

new_load = """      const value = data?.content || '';
      const incomingCanonical = sanitizeRichHtml(normalizeRichContent(value));
      const input = $('dashboardNoteInput');
      if (input && dashboardNoteIsDirty()) {
        if (incomingCanonical !== dashboardNoteSavedValue) {
          dashboardNoteSavedValue = incomingCanonical;
          updateDashboardNoteStatus('unsaved', 'Changed on another device — your local text is not saved');
        }
        return;
      }
      if (input) setDashboardNoteRichContent(value);
      dashboardNoteSavedValue = incomingCanonical;"""

html = replace_once(html, old_load, new_load, 'canonical dashboard load')

old_init = """      shell.classList.add('ready');
      syncDashboardRichEditor();
      updateIdeaRichToolbar(dashboardRichEditor);
      return dashboardRichEditor;"""

new_init = """      shell.classList.add('ready');
      syncDashboardRichEditor();
      // Establish a canonical empty baseline before auth loads the saved note.
      // Without this, an empty rich editor (<p><br></p>) could look dirty against ''.
      if (!dashboardNoteSavedValue) dashboardNoteSavedValue = getDashboardNoteContentForStorage();
      updateIdeaRichToolbar(dashboardRichEditor);
      return dashboardRichEditor;"""

html = replace_once(html, old_init, new_init, 'dashboard rich init baseline')
INDEX.write_text(html, encoding='utf-8')
print('Dashboard rich initialization fix applied.')
