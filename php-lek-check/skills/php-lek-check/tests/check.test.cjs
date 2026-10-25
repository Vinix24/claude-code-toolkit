const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {root, data, fixtures, createChecker, runCase} = require('./helpers.cjs');
const checker = createChecker(data);

for (const item of fixtures.cases) test('Gedeeld geval: ' + item.name, () => {
  const result = runCase(checker, item);
  for (const [key, value] of Object.entries(item.expected)) assert.equal(result[key], value, key);
  assert.doesNotMatch(JSON.stringify(result), /gepatcht|veilig|private-value/i);
  assert.match(result.bericht_hoster, /Voor je websitebouwer: zo weet je het zeker/);
});

function checkOrder(api) {
  const rank = {'onbekend':0, 'lijkt bijgewerkt volgens het versienummer':1, 'kan kwetsbaar zijn':2,
    'kan kwetsbaar zijn, tenzij je hoster een backport heeft toegepast':3,
    'kan kwetsbaar zijn; PHP zelf noemt voor deze versie geen reparatie, upgrade nodig':4};
  const groups = fixtures.severity_groups.map(group => group.map(name => {
    const result = runCase(api, fixtures.cases.find(item => item.name === name));
    assert.ok(Object.hasOwn(rank, result.beoordeling));
    return rank[result.beoordeling];
  }));
  for (let i = 0; i < groups.length - 1; i++) assert.ok(Math.min(...groups[i]) > Math.max(...groups[i+1]));
}
test('De beoordeling van een oudere reeks is nooit milder', () => checkOrder(checker));
test('Mutatie 8.4.27 naar 8.4.26 wordt rood', () => {
  const mutated = structuredClone(data);
  mutated.patches['8.4'] = 26;
  const item = fixtures.cases.find(item => item.name === 'php-8.4.26');
  assert.throws(() => assert.equal(runCase(createChecker(mutated), item).uitkomst, item.expected.uitkomst), assert.AssertionError);
});
test('Mutatie oude PHP naar onbekend wordt rood', () => {
  const mutated = structuredClone(data);
  mutated.results.unsupported.assessment = 'onbekend';
  assert.throws(() => checkOrder(createChecker(mutated)), assert.AssertionError);
});
test('De pagina bevat dezelfde regels en dezelfde beoordelingscode', () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const embedded = JSON.parse(html.match(/<script type="application\/json" id="rules-data">([\s\S]*?)<\/script>/)[1]);
  assert.deepEqual(embedded, data);
  assert.ok(html.includes(fs.readFileSync(path.join(root, 'src/core.js'), 'utf8').trim()));
  const bookmark = html.match(/<script type="text\/plain" id="bookmarklet-source">([\s\S]*?)<\/script>/)[1];
  assert.equal((bookmark.match(/\bfetch\s*\(/g) || []).length, 1);
  assert.match(bookmark, /fetch\(location\.href, \{credentials: "same-origin", cache: "no-store", redirect: "manual"\}\)/);
  new vm.Script(bookmark);
});
test('Paginacode doet geen netwerk- of opslagaanroep', () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const pageScript = html.match(/<script id="page-script">([\s\S]*?)<\/script>/)[1];
  assert.doesNotMatch(pageScript, /\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|localStorage|sessionStorage|indexedDB|document\.cookie\s*=/);
  new vm.Script(pageScript);
});
