function resultView(doc, result) {
  const make = (tag, text, className) => {
    const node = doc.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const section = make('section', undefined, 'result-view');
  section.append(make('p', result.doel, 'small'));
  section.append(make('h3', result.titel));
  section.append(make('p', `Beoordeling: ${result.beoordeling}`, 'assessment'));
  section.append(make('p', result.toelichting));
  section.append(make('p', `PHP-versie: ${result.php_versie || 'niet zichtbaar'}.`));
  section.append(make('p', result.vergelijking, 'small'));
  const signals = result.aanwijzingen?.signalen || [];
  section.append(make('p', 'Gevonden signalen: ' + (signals.join(' ') || 'geen.'), 'small'));
  const label = make('label', 'Bericht voor je websitebouwer of hoster');
  const message = make('textarea');
  message.value = result.bericht_hoster;
  message.readOnly = true;
  message.rows = 12;
  message.setAttribute('aria-label', 'Bericht voor je websitebouwer of hoster');
  label.append(message);
  section.append(label);
  const button = make('button', 'Kopieer bericht', 'primary');
  button.type = 'button';
  const status = make('p', '', 'small');
  status.setAttribute('role', 'status');
  button.addEventListener('click', async () => {
    const copied = await copyText(doc, message);
    status.textContent = copied ? 'Bericht gekopieerd. Je kunt het nu plakken in een mail.' :
      'Kopiëren is hier geblokkeerd. De tekst is geselecteerd. Kopieer zelf met Ctrl+C of Cmd+C, of houd de tekst ingedrukt.';
  });
  section.append(button, status);
  return section;
}

async function copyText(doc, field) {
  try {
    const clipboard = doc.defaultView?.navigator?.clipboard;
    if (clipboard && typeof clipboard.writeText === 'function') {
      await clipboard.writeText(field.value);
      return true;
    }
  } catch (_) { /* De handmatige route hieronder blijft beschikbaar. */ }
  field.focus();
  field.select();
  try { return Boolean(doc.execCommand && doc.execCommand('copy')); }
  catch (_) { return false; }
}
