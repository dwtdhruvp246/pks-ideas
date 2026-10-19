const { test } = require('node:test');
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
    if (!elements.has(id)) elements.set(id, { value: '', classList: { add() {}, remove() {} } });
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
  vm.runInContext('items=mockItems; loadItems=async()=>{items=mockItems};', context);
  const headers = plain(vm.runInContext('BULK_HEADERS', context));
  const sheet = rows => context.XLSX.utils.aoa_to_sheet([headers, ...rows]);
  const parse = rows => plain(context.parseBulkSheet(sheet(rows)));
  const upload = async input => {
    const file = { arrayBuffer: async () => input };
    await element('bulkFile').onchange({ target: { files: [file], value: 'file.xlsx' } });
  };
  return { context, parse, sheet, upload, writes, prompts, alerts, element, mockItems };
}

test('different names keep matching colours and quantity ranges separate', () => {
  const names = ['PETG', 'PLA', 'PLA+', 'PLA+ (New Style)', 'TPU 95A', 'TPU 98A'];
  const groups = app().parse(names.map(name => row(name, 'Black')));
  assert.deepEqual(groups.map(g => g.item.name), names);
  assert.ok(groups.every(g => g.priceTiers.length === 1));
});

test('supplier and colour variants stay separate, including delimiter characters', () => {
  const a = row(), b = row(), c = row('PETG', 'Black');
  b[1] = 'Other supplier';
  assert.equal(app().parse([a, b, c]).length, 3);
  const d = row('A\u001fB'), e = row('A');
  d[1] = 'C'; e[1] = 'B\u001fC';
  assert.equal(app().parse([d, e]).length, 2);
});

test('identical nonconsecutive open-ended rows produce one tier per item', () => {
  const groups = app().parse([row(), row('PLA'), row(), row('PLA')]);
  assert.equal(groups.length, 2);
  assert.ok(groups.every(g => g.priceTiers.length === 1));
  assert.deepEqual(groups[0].priceTiers[0], { min_qty: 1, max_qty: null, unit_price: 4.7 });
});

test('repeated finite tiers collapse while distinct tiers sort and remain', () => {
  const groups = app().parse([row('PETG', 'Brown', 20, '', 4), row('PETG', 'Brown', 1, 19), row('PETG', 'Brown', 1, 19)]);
  assert.deepEqual(groups[0].priceTiers, [
    { min_qty: 1, max_qty: 19, unit_price: 4.7 },
    { min_qty: 20, max_qty: null, unit_price: 4 }
  ]);
});

test('repeated rows without tiers are safe', () => {
  const a = row(); a.splice(9, 3, '', '', '');
  assert.deepEqual(app().parse([a, a])[0].priceTiers, []);
});

test('same range with a different price still fails with both source rows', () => {
  assert.throws(() => app().parse([row(), row('PETG', 'Brown', 1, '', 4)]),
    /Row 3: quantity tiers overlap with row 2 for PETG \(Brown\)/);
});

test('true overlaps and a misplaced open-ended tier still fail', () => {
  assert.throws(() => app().parse([row('PETG', 'Brown', 1, 20), row('PETG', 'Brown', 20, 30)]), /overlap/);
  assert.throws(() => app().parse([row(), row('PETG', 'Brown', 20, 30)]), /open-ended tier must be last/);
});

test('conflicting item details cannot be hidden by an identical tier', () => {
  for (const column of [3, 4, 5, 6, 7, 8]) {
    const changed = row(); changed[column] += 1;
    assert.throws(() => app().parse([row(), changed]), /Row 3: Repeated item details differ from row 2/);
  }
});

test('USD parsing and validation remain intact', () => {
  const a = row(); a[3] = 'US$ 1,234.50'; a[11] = 'USD 4.70';
  assert.equal(app().parse([a])[0].item.base_price, 1234.5);
  const invalid = row(); invalid[5] = 1.5;
  assert.throws(() => app().parse([invalid]), /whole number/);
  assert.throws(() => app().parse([row('PETG', 'Brown', '', '', 5)]), /Tier From Qty is required/);
  assert.throws(() => app().parse([row('PETG', 'Brown', 10, 9)]), /cannot be less/);
});

test('upload skips an existing identity but imports another name with the same colour', async () => {
  const a = app({ existing: [{ name: ' petg ', supplier: null, colour: ' BROWN ' }] });
  await a.upload(a.sheet([row(), row('PLA'), row('PLA')]));
  assert.deepEqual(a.writes.map(w => w.table), ['landed_items', 'landed_price_tiers']);
  assert.equal(a.writes[0].payload.name, 'PLA');
  assert.equal(a.writes[1].payload.length, 1);
  assert.match(a.prompts[0], /Import 1 new items with 1 quantity tiers/);
  assert.match(a.element('msg').textContent, /Imported 1 item\(s\). Skipped existing: 1. Failed: 0/);
  await a.upload(a.sheet([row(), row('PLA')]));
  assert.equal(a.writes.length, 2);
  assert.equal(a.prompts.length, 1);
  assert.match(a.element('msg').textContent, /Nothing imported/);
});

test('invalid data and cancellation cause no writes', async () => {
  const invalid = app();
  await invalid.upload(invalid.sheet([row('PLA'), row(), row('PETG', 'Brown', 1, '', 9)]));
  assert.equal(invalid.writes.length, 0);
  assert.equal(invalid.prompts.length, 0);
  assert.equal(invalid.alerts.length, 1);
  assert.equal(invalid.element('uploadTemplate').disabled, false);
  const cancelled = app({ approve: false });
  await cancelled.upload(cancelled.sheet([row()]));
  assert.equal(cancelled.writes.length, 0);
});

test('uploaded 376-row workbook imports 374 distinct items and is safe to reimport', {
  skip: !(process.env.BULK_TEST_WORKBOOK && process.env.BULK_TEST_XLSX)
}, async () => {
  const a = app({ realExcel: true });
  const bytes = fs.readFileSync(process.env.BULK_TEST_WORKBOOK);
  const wb = a.context.XLSX.read(bytes, { type: 'array', cellDates: false });
  const rows = a.context.XLSX.utils.sheet_to_json(wb.Sheets.Items, { header: 1, defval: '', raw: true });
  assert.equal(rows.length - 1, 376);
  const groups = plain(a.context.parseBulkSheet(wb.Sheets.Items));
  assert.equal(groups.length, 374);
  assert.ok(groups.every(g => g.priceTiers.length === 1));
  const brown = groups.filter(g => ['PETG', 'PLA'].includes(g.item.name) && g.item.colour === 'Brown');
  assert.equal(brown.length, 2);
  assert.deepEqual(brown.map(g => g.priceTiers[0].unit_price), [4.7, 5.79]);
  await a.upload(bytes);
  assert.equal(a.alerts.length, 0);
  const itemWrites = a.writes.filter(w => w.table === 'landed_items');
  const tierWrites = a.writes.filter(w => w.table === 'landed_price_tiers');
  assert.equal(itemWrites.length, 374);
  assert.equal(tierWrites.length, 374);
  assert.ok(tierWrites.every(w => w.payload.length === 1));
  assert.match(a.element('msg').textContent, /Imported 374 item\(s\). Skipped existing: 0. Failed: 0/);
  await a.upload(bytes);
  assert.equal(a.writes.length, 748);
  assert.equal(a.prompts.length, 1);
  assert.match(a.element('msg').textContent, /all 374 items already exist/);
});
