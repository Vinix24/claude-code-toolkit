const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'rules.json'), 'utf8'));
const fixtures = JSON.parse(fs.readFileSync(path.join(root, 'cases.json'), 'utf8'));
const core = fs.readFileSync(path.join(root, 'src/core.js'), 'utf8');
const createChecker = vm.runInNewContext(core + '\ncreateChecker;');

// Kleine DOM-adapter voor de HTML-fragmenten in cases.json, zonder npm-pakketten.
// Een aparte headless proef gebruikt de echte DOMParser en dezelfde gevallen.
function fixtureDocument(html) {
  const nodes = [];
  const markup = html.replace(/<!--[\s\S]*?-->/g, '').replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, '');
  for (const tag of markup.matchAll(/<([a-z][\w-]*)\b((?:[^>"']|"[^"]*"|'[^']*')*)>/gi)) {
    const attrs = {};
    for (const attr of tag[2].matchAll(/([\w:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) {
      attrs[attr[1].toLowerCase()] = (attr[2] ?? attr[3] ?? attr[4] ?? '').replace(/&amp;/g, '&').replace(/&quot;/g, '"');
    }
    nodes.push({tag: tag[1].toLowerCase(), getAttribute: name => attrs[name] ?? null, hasAttribute: name => Object.hasOwn(attrs, name)});
  }
  return {querySelectorAll(selector) {
    if (selector === 'meta[name]') return nodes.filter(node => node.tag === 'meta' && node.hasAttribute('name'));
    if (selector === '[src], [action], [href]') return nodes.filter(node => ['src', 'action', 'href'].some(name => node.hasAttribute(name)));
    throw new Error('Onbekende selector in de fixture-adapter: ' + selector);
  }};
}
function runCase(checker, item) {
  return checker.evaluate({...item, url: fixtures.url, htmlRecords: checker.collectDOM(fixtureDocument(item.html))});
}
module.exports = {root, data, fixtures, createChecker, fixtureDocument, runCase};
