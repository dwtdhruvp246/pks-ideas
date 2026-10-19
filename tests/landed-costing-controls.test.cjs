const { test } = require('node:test');
const assert = require('node:assert/strict');
const { app, row, plain } = require('./landed-app.cjs');
const vm = require('node:vm');
const run = (a, code) => vm.runInContext(code, a.context);
const state = (a, code) => plain(run(a, code));
const item = (id, overrides = {}) => ({ id, name: 'Item '+id, supplier: 'Supplier A', item_number: '0012', colour: 'Black', base_price: 5, local_shipping: 0, units_per_carton: 10, carton_length_cm: 10, carton_width_cm: 10, carton_height_cm: 10, ...overrides });
function seed(a, items) { run(a, 'items='+JSON.stringify(items)+';itemNumberReady=true;'); a.context.renderItems(); a.context.renderCalc(); }
function select(a, id, checked = true) { a.element('itemRows').onchange({ target: { dataset: { deleteSelect:id }, checked, matches: s => s==='[data-delete-select]' } }); }
function type(a, id, text) { a.element(id).value=text; a.element(id).oninput(); }
function deleteAdapter(a, respond) {
  const requests=[];
  a.context.query=async(table, opts)=>opts({delete:()=>({in:(field,ids)=>({select:()=>{
    requests.push({table,field,ids:plain(ids)});return respond(ids,requests.length);
  }})})});
  return requests;
}

test('each of supplier, name, item number and colour can distinguish an item', () => {
  const a=app(), base={supplier:'A',name:'PETG',item_number:'0012',colour:'Black'};
  const identities=[base,{...base,supplier:'B'},{...base,name:'PLA'},{...base,item_number:'12'},{...base,colour:'White'}];
  const keys=identities.map(i=>a.context.bulkItemKey(i));
  assert.equal(new Set(keys).size,5);
  assert.equal(a.context.bulkItemKey({...base,supplier:' a ',name:' petg ',colour:' BLACK '}),keys[0]);
  const rows=identities.map(i=>{const r=row(i.name,i.colour);r[1]=i.supplier;r[12]=i.item_number;return r});
  const groups=a.parse([...rows,rows[0]]);assert.equal(groups.length,5);
  assert.equal(groups[0].item.item_number,'0012');assert.ok(groups.every(g=>g.priceTiers.length===1));
});

test('legacy templates remain valid; numbered imports require migration and preserve text', async () => {
  const a=app(), legacy=a.sheet([row()]);legacy[0]=legacy[0].slice(0,12);
  assert.equal(a.context.parseBulkSheet(legacy)[0].item.item_number,'');
  const numbered=[...row(),'0012'];await a.upload(a.sheet([numbered]));
  assert.equal(a.writes.length,0);assert.match(a.alerts[0],/one-time setup/);
  const ready=app({existing:[item('existing',{name:'PETG',colour:'Brown'})]});run(ready,'itemNumberReady=true');
  const differentSupplier=[...numbered];differentSupplier[1]='Supplier B';
  const sameSupplier=[...numbered];sameSupplier[1]='Supplier A';
  await ready.upload(ready.sheet([sameSupplier,differentSupplier]));
  assert.equal(ready.writes.filter(w=>w.table==='landed_items').length,1);
  assert.equal(ready.writes[0].payload.supplier,'Supplier B');assert.equal(ready.writes[0].payload.item_number,'0012');
  assert.match(ready.element('msg').textContent,/Skipped existing: 1/);
});

test('manual item creation rejects a duplicate identity and permits another supplier', async () => {
  const a=app({existing:[item('old',{name:'PETG'})]});run(a,'itemNumberReady=true');
  const fields={...item('new',{name:'PETG'})},form={elements:{namedItem:key=>({value:String(fields[key]??'')})}};
  a.element('tierRows').children=[];a.element('itemDialog').close=()=>{};
  await a.element('itemForm').onsubmit({preventDefault(){},target:form});
  assert.equal(a.writes.length,0);assert.match(a.element('msg').textContent,/already exists/);
  fields.supplier='Supplier B';await a.element('itemForm').onsubmit({preventDefault(){},target:form});
  assert.equal(a.writes.length,1);assert.equal(a.writes[0].payload.item_number,'0012');assert.equal(a.writes[0].payload.supplier,'Supplier B');
});

test('catalogue loading supports migrated and legacy schemas, including empty catalogues', async () => {
  for(const migrated of [true,false])for(const empty of [true,false]){
    const a=app(),record=item('a');if(!migrated)delete record.item_number;
    a.context.query=async(table,opts)=>opts({select:columns=>({
      order:()=>empty?[]:[record],
      limit:()=>{if(!migrated)throw Object.assign(Error('Missing item_number'),{code:'42703'});return []}
    })});
    // Price tiers return an array rather than the catalogue's ordering builder.
    const query=a.context.query;a.context.query=async(table,opts)=>table==='landed_price_tiers'?[]:query(table,opts);
    await a.loadCatalogue();assert.equal(run(a,'itemNumberReady'),migrated);assert.equal(run(a,'items.length'),empty?0:1);
  }
});

test('item numbers appear in calculator snapshots, exports, search and sorting', () => {
  const a=app();seed(a,[item('a'),item('b',{item_number:'0013'})]);run(a,"selected=new Map([['a',2]]);");a.context.renderCalc();
  const snapshot=state(a,'calcResult');assert.equal(snapshot[0].item_number,'0012');assert.match(a.context.csv(snapshot),/"0012"/);
  type(a,'itemSearch','0013');assert.match(a.element('itemRows').innerHTML,/data-edit="b"/);assert.doesNotMatch(a.element('itemRows').innerHTML,/data-edit="a"/);
  type(a,'calcSearch','0012');assert.match(a.element('calcRows').innerHTML,/data-select="a"/);assert.doesNotMatch(a.element('calcRows').innerHTML,/data-select="b"/);
  run(a,"itemSort={key:'item_number',direction:-1};");type(a,'itemSearch','');
  assert.ok(a.element('itemRows').innerHTML.indexOf('data-edit="b"')<a.element('itemRows').innerHTML.indexOf('data-edit="a"'));
});

test('every Clear search button restores rows, focuses input and preserves calculator selection', () => {
  const a=app();seed(a,[item('a'),item('b')]);run(a,"selected=new Map([['a',7]]);currentSaved={lines:calculate()};");
  for(const id of ['itemSearch','calcSearch','savedSearch','savedLinesSearch']){
    let focused=false;a.element(id).focus=()=>{focused=true};type(a,id,'no match');
    a.element(id+'Clear').onclick();assert.equal(a.element(id).value,'');assert.ok(focused);
    assert.deepEqual(state(a,'[...selected]'),[['a',7]]);assert.equal(run(a,'calcDirty'),false);
  }
  assert.match(a.element('itemRows').innerHTML,/data-edit="a"/);assert.match(a.element('calcRows').innerHTML,/data-select="b"/);
});

test('bulk checkboxes select visible rows, preserve hidden picks and stay independent of calculator', () => {
  const a=app();seed(a,[item('a',{name:'Alpha'}),item('b',{name:'Beta'}),item('c',{name:'Beta 2'})]);run(a,"selected=new Map([['c',9]]);");
  type(a,'itemSearch','Alpha');a.element('selectAllItems').onchange({target:{checked:true}});assert.deepEqual(state(a,'[...deleteSelection]'),['a']);
  type(a,'itemSearch','Beta');select(a,'b');assert.ok(a.element('selectAllItems').indeterminate);assert.match(a.element('deleteSelectionCount').textContent,/2 selected \(1 hidden/);
  a.element('selectAllItems').onchange({target:{checked:false}});assert.deepEqual(state(a,'[...deleteSelection]'),['a']);
  a.element('clearDeleteSelection').onclick();assert.equal(run(a,'deleteSelection.size'),0);assert.deepEqual(state(a,'[...selected]'),[['c',9]]);
});

test('cancelled deletion makes no requests or local changes', async () => {
  const a=app({approve:false});seed(a,[item('a')]);select(a,'a');const requests=deleteAdapter(a,ids=>ids.map(id=>({id})));
  await a.element('deleteSelectedItems').onclick();assert.equal(requests.length,0);assert.equal(run(a,'items.length'),1);assert.equal(run(a,'deleteSelection.size'),1);
});

test('deletion removes only returned IDs, preserves saved history and flags changed calculations', async () => {
  const a=app();seed(a,[item('a'),item('b'),item('c')]);run(a,"selected=new Map([['a',3],['c',4]]);tiers=[{item_id:'a'},{item_id:'b'}];currentSaved={id:'saved',lines:[{source_item_id:'a',item_number:'0012'}]};");
  select(a,'a');select(a,'b');type(a,'itemSearch','no-matching-item');const snapshot=state(a,'currentSaved');
  const requests=deleteAdapter(a,()=>[{id:'a'}]);await a.element('deleteSelectedItems').onclick();
  assert.deepEqual(requests,[{table:'landed_items',field:'id',ids:['a','b']}]);assert.deepEqual(state(a,'items.map(i=>i.id)'),['b','c']);
  assert.deepEqual(state(a,'[...deleteSelection]'),['b']);assert.deepEqual(state(a,'[...selected]'),[['c',4]]);assert.equal(run(a,'calcDirty'),true);
  assert.deepEqual(state(a,'tiers'),[{item_id:'b'}]);assert.deepEqual(state(a,'currentSaved'),snapshot);assert.match(a.prompts[0],/2 selected item\(s\) are hidden/);assert.match(a.element('msg').textContent,/Deleted 1 of 2/);
});

test('large deletion batches remain bounded and failures leave remaining items selected', async () => {
  const a=app();const records=Array.from({length:123},(_,i)=>item(String(i)));seed(a,records);
  a.element('selectAllItems').onchange({target:{checked:true}});
  const requests=deleteAdapter(a,(ids,index)=>{if(index===2)throw Error('Network failed');return ids.map(id=>({id}))});
  await a.element('deleteSelectedItems').onclick();assert.equal(requests.length,2);assert.ok(requests.every(r=>r.ids.length<=50));
  assert.equal(run(a,'items.length'),73);assert.equal(run(a,'deleteSelection.size'),73);assert.equal(run(a,'deleteBusy'),false);assert.match(a.element('msg').textContent,/Network failed/);
});

test('duplicate delete clicks cannot submit concurrently', async () => {
  const a=app();seed(a,[item('a')]);select(a,'a');let release;
  const requests=deleteAdapter(a,ids=>new Promise(resolve=>{release=()=>resolve(ids.map(id=>({id})))}));
  const first=a.element('deleteSelectedItems').onclick();await a.element('deleteSelectedItems').onclick();assert.equal(requests.length,1);assert.equal(a.prompts.length,1);
  release();await first;assert.equal(run(a,'items.length'),0);assert.equal(run(a,'deleteBusy'),false);
});
