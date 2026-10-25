/* Alleen deze functie mag een netwerkverzoek doen. */
(async function phpLekCheck() {
  const data = /*__RULES__*/;
  /*__CORE__*/
  /*__RENDER__*/
  const checker = createChecker(data);
  const previousFocus = document.activeElement;
  const records = checker.collectDOM(document);
  let cookies = '';
  try { cookies = document.cookie; } catch (_) { /* Niet alle cookies zijn leesbaar. */ }
  const address = location.href;
  const host = document.createElement('div');
  host.setAttribute('data-php-lek-check-overlay', '');
  const root = host.attachShadow({mode: 'open'});
  const style = document.createElement('style');
  style.textContent = `
    :host { all: initial; }
    * { box-sizing: border-box; }
    dialog { width: min(720px, calc(100vw - 24px)); max-height: calc(100dvh - 32px);
      overflow: auto; padding: 24px; border: 2px solid #244b40; border-radius: 16px;
      background: #fffdf7; color: #183b32; font: 17px/1.55 system-ui, sans-serif; }
    dialog::backdrop { background: rgb(12 28 24 / .7); }
    header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    h2, h3 { line-height: 1.25; margin: 12px 0; }
    p { margin: 12px 0; }
    .small { font-size: 14px; color: #43594f; }
    .assessment { font-weight: 700; }
    button { min-height: 44px; padding: 10px 16px; border: 1px solid #244b40; border-radius: 8px;
      background: #fffdf7; color: #183b32; font: inherit; cursor: pointer; }
    .primary { background: #183b32; color: white; }
    textarea { display: block; width: 100%; margin: 8px 0 16px; padding: 12px; resize: vertical;
      border: 1px solid #667c71; border-radius: 8px; background: white; color: #183b32; font: 15px/1.5 system-ui, sans-serif; }
    :focus-visible { outline: 3px solid #98631d; outline-offset: 3px; }
  `;
  const dialog = document.createElement('dialog');
  dialog.setAttribute('aria-labelledby', 'php-check-title');
  const header = document.createElement('header');
  const title = document.createElement('h2');
  title.id = 'php-check-title';
  title.textContent = 'Jouw PHP-check';
  const close = document.createElement('button');
  close.type = 'button';
  close.textContent = 'Sluiten';
  close.addEventListener('click', () => dialog.close());
  header.append(title, close);
  const content = document.createElement('div');
  content.textContent = 'De knop leest één antwoord van deze pagina. Even wachten…';
  dialog.append(header, content);
  root.append(style, dialog);
  (document.body || document.documentElement).append(host);
  dialog.addEventListener('close', () => {
    host.remove();
    if (previousFocus?.isConnected) previousFocus.focus({preventScroll: true});
  });
  dialog.showModal();
  close.focus();
  let result;
  try {
    if (!/^https?:$/.test(location.protocol)) throw new Error('Open eerst je eigen website. Gebruik anders route B op de checkpagina.');
    const response = await fetch(location.href, {credentials: "same-origin", cache: "no-store", redirect: "manual"});
    if (response.type === 'opaqueredirect' || response.status >= 300 && response.status < 400) {
      throw new Error('Deze pagina verwijst door. De knop volgt die verwijzing niet. Open zelf het uiteindelijke adres of gebruik route B.');
    }
    const headers = {};
    for (const name of ['X-Powered-By', 'Server', 'Link']) headers[name] = response.headers.get(name) || '';
    result = checker.evaluate({headers, htmlRecords: records, cookie: cookies, url: address});
    if (response.status >= 400 && result.uitkomst === 'geen_php') {
      throw new Error('De website gaf een foutantwoord. Gebruik route B of stuur het bericht naar je hoster.');
    }
  } catch (error) {
    result = checker.evaluate({htmlRecords: records, cookie: cookies, url: address});
    result.uitkomst = null;
    result.titel = 'Controle niet afgerond';
    result.beoordeling = 'onbekend';
    result.toelichting = error instanceof TypeError ?
      'De browser kon het antwoord niet lezen. Een instelling van de site of een netwerkfout kan de knop blokkeren. Gebruik route B of stuur het bericht naar je hoster.' : error.message;
  }
  if (host.isConnected) content.replaceChildren(resultView(document, result));
})();
