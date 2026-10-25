/* De gegevens en de volgorde van de regels komen uitsluitend uit rules.json. */
function createChecker(data) {
  const pattern = (name, flags = 'i') => new RegExp(data.patterns[name], flags);
  const compare = (a, b) => {
    for (let i = 0; i < Math.max(a.length, b.length); i++) {
      if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) - (b[i] || 0);
    }
    return 0;
  };

  function collectDOM(doc) {
    const generators = [], attributes = [];
    for (const node of doc.querySelectorAll('meta[name]')) {
      if ((node.getAttribute('name') || '').toLowerCase() === 'generator') {
        generators.push(node.getAttribute('content') || '');
      }
    }
    for (const node of doc.querySelectorAll('[src], [action], [href]')) {
      for (const name of ['src', 'action', 'href']) {
        if (node.hasAttribute(name)) attributes.push({name, value: node.getAttribute(name) || ''});
      }
    }
    return {generators, attributes};
  }

  function chooseVersion(number, suffix) {
    const branch = number.slice(0, 2), key = branch.join('.');
    const facts = {
      suffix: Boolean(suffix), known_branch: Object.hasOwn(data.patches, key),
      prerelease: pattern('prerelease').test(suffix),
      fixed: Object.hasOwn(data.patches, key) && number[2] >= data.patches[key]
    };
    for (const rule of data.rules) {
      if (Object.entries(rule.when).every(([name, value]) =>
        name === 'max_branch' ? compare(branch, value) <= 0 : facts[name] === value)) {
        return {key: rule.result, number, version: number.join('.') + suffix};
      }
    }
    throw new Error('Geen beoordelingsregel gevonden.');
  }

  function makeMessage(url, version) {
    const fields = {url: url || '(vul je websiteadres in)', version: version || 'niet zichtbaar'};
    const message = data.message.replace(/\{(url|version)\}/g, (_, key) => fields[key]);
    return message + '\n\nVoor je websitebouwer: zo weet je het zeker\n' +
      data.builder_steps.map((step, index) => `${index + 1}. ${step}`).join('\n');
  }

  function evaluate(input = {}) {
    const headers = {};
    for (const [name, value] of Object.entries(input.headers || {})) {
      const key = name.toLowerCase();
      headers[key] = (headers[key] || []).concat(Array.isArray(value) ? value : [String(value)]);
    }
    const powered = (headers['x-powered-by'] || []).join(' | ');
    const server = (headers.server || []).join(' | ');
    const html = input.htmlRecords || {generators: [], attributes: []};
    const signals = new Set();
    for (const [name, value] of [['X-Powered-By', powered], ['Server', server]]) {
      if (pattern('php').test(value)) signals.add(`Header ${name} noemt PHP.`);
    }
    if (powered.trim() && !pattern('php').test(powered)) signals.add(data.signals.custom);
    for (const value of html.generators) {
      const cms = value.match(pattern('cms'));
      if (cms) signals.add(`HTML-metatag generator noemt ${cms[0]}.`);
    }
    for (const {name, value} of html.attributes) {
      const match = value.match(pattern('path'));
      if (match) signals.add(`HTML-attribuut ${name} bevat ${match[0]}.`);
    }
    const cookies = (headers['set-cookie'] || []).map(value => value.split(';')[0]);
    if (cookies.concat(input.cookie || '').some(value => pattern('cookie').test(value))) signals.add(data.signals.cookie);
    if (pattern('link').test((headers.link || []).join(' '))) signals.add(data.signals.link);
    if (input.cms) signals.add(data.signals.cms_flag);
    const candidates = Array.from((powered + ' ' + server).matchAll(pattern('version', 'gi')),
      match => chooseVersion(match.slice(1, 4).map(Number), match[4]));
    candidates.sort((a, b) => data.results[a.key].priority - data.results[b.key].priority || compare(a.number, b.number));
    const chosen = candidates[0];
    const definition = data.results[chosen ? chosen.key : signals.size ? 'hidden' : 'none'];
    const version = chosen ? chosen.version : null;
    return {
      doel: data.purpose, url: input.url || '', uitkomst: definition.code,
      beoordeling: definition.assessment, php_versie: version, vergelijking: data.comparison,
      titel: definition.title, toelichting: definition.explanation,
      aanwijzingen: {'X-Powered-By': powered, Server: server, generator: html.generators, signalen: [...signals].sort()},
      bericht_hoster: makeMessage(input.url, version)
    };
  }
  return {evaluate, collectDOM, makeMessage, data};
}
