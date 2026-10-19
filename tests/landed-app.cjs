const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../landed-costing.html'), 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
const plain = value => JSON.parse(JSON.stringify(value));
const row = (name = 'PETG', colour = 'Brown', from = 1, to = '', price = 4.7) =>
  [name, '', colour, 4.7, 0, 10, 62, 62, 40, from, to, price];

// Execute the shipped page, including its upload handler, with isolated DOM/DB adapters.
// Optional real-workbook check uses the exact SheetJS bundle loaded by the page.
function app({ existing = [], approve = true, realExcel = false } = {}) {
  const elements = new Map(), writes = [], prompts = [], alerts = [], mockItems = [...existing];
  const element = id => {
    if (!elements.has(id)) elements.set(id, { value: '', classList: { add() {}, remove() {}, toggle() {} } });
    return elements.get(id);
  };
  const db = {
    auth: { getSession: async () => ({ data: { session: null } }) },
    from: table => ({ insert(payload) {
      writes.push({ table, payload: plain(payload) });
      if (table === 'landed_items') {
        const item = { ...payload, id: 'item-' + mockItems.length };
        mockItems.push(item);
        return { select: () => ({ single: async () => ({ data: { id: item.id } }) }) };
      }
      return Promise.resolve({ data: null });
    } })
  };
  const context = vm.createContext({
    document: { getElementById: element, querySelectorAll: () => [] },
    window: { supabase: { createClient: () => db }, addEventListener() {} },
    confirm: message => { prompts.push(message); return approve; },
    alert: message => alerts.push(message),
    mockItems
  });
  if (realExcel) {
    vm.runInContext(fs.readFileSync(process.env.BULK_TEST_XLSX, 'utf8'), context);
    context.window.XLSX = context.XLSX;
  } else {
    context.XLSX = context.window.XLSX = {
      utils: { sheet_to_json: sheet => plain(sheet), aoa_to_sheet: rows => rows },
      read: sheet => ({ Sheets: { Items: sheet } })
    };
  }
  vm.runInContext(script, context, { filename: 'landed-costing.html' });
  const loadCatalogue = context.loadItems;
  vm.runInContext('items=mockItems; loadItems=async()=>{items=mockItems};', context);
  const headers = plain(vm.runInContext('BULK_HEADERS', context));
  const sheet = rows => context.XLSX.utils.aoa_to_sheet([headers, ...rows]);
  const parse = rows => plain(context.parseBulkSheet(sheet(rows)));
  const upload = async input => {
    const file = { arrayBuffer: async () => input };
    await element('bulkFile').onchange({ target: { files: [file], value: 'file.xlsx' } });
  };
  return { context, parse, sheet, upload, writes, prompts, alerts, element, mockItems, loadCatalogue };
}

module.exports={app,row,plain};
