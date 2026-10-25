/* Optionele echte browserproef. Node 22+ en een aparte Chromium-testbinary.
 * Geen npm-pakketten, geen bestaand browserprofiel en geen systeemklembord.
 * PHP_CHECK_CHROMIUM=/pad/naar/chrome-headless-shell node tests/headless.cjs
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const {pathToFileURL} = require('node:url');
const {root, data, fixtures, createChecker} = require('./helpers.cjs');
const binary = process.env.PHP_CHECK_CHROMIUM;
if (!binary) throw new Error('Stel PHP_CHECK_CHROMIUM in op een aparte Chromium-testbinary.');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'php-check-browser-'));
const output = path.join(root, 'output', 'headless');
fs.mkdirSync(output, {recursive: true});
const requests = [];
let mode = 'normal';
const server = http.createServer((req, res) => {
  requests.push({url:req.url, method:req.method});
  if (mode === 'redirect') { res.writeHead(302, {Location:`http://localhost:${server.address().port}/other`}); res.end(); return; }
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('X-Powered-By', 'PHP/8.3.20');
  res.setHeader('Set-Cookie', 'PHPSESSID=test-session; Path=/');
  if (mode === 'csp') res.setHeader('Content-Security-Policy', "default-src 'none'; script-src 'none'; connect-src 'none'; style-src 'unsafe-inline'");
  res.end('<!doctype html><meta name="generator" content="WordPress 8.4.27"><link rel="icon" href="data:,"><title>Lokale proef</title><h1>Mijn lokale website</h1><button id="previous">Vorige focus</button>');
});
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
let browser, socket;
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const site = `http://127.0.0.1:${server.address().port}/`;
  browser = spawn(binary, ['--headless', '--disable-gpu', '--disable-background-networking', '--no-first-run',
    '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${temporary}`, 'about:blank'], {stdio:['ignore','ignore','pipe']});
  const websocketURL = await new Promise((resolve, reject) => {
    let log = '';
    const timer = setTimeout(() => reject(new Error('Testbrowser startte niet: ' + log)), 15000);
    browser.once('error', reject);
    browser.stderr.on('data', chunk => {
      log += chunk;
      const match = log.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) { clearTimeout(timer); resolve(match[1]); }
    });
  });
  socket = new WebSocket(websocketURL);
  await once(socket, 'open');
  let id = 0, session;
  const pending = new Map(), network = [];
  socket.addEventListener('message', event => {
    const value = JSON.parse(event.data);
    if (value.id && pending.has(value.id)) {
      const item = pending.get(value.id); pending.delete(value.id); clearTimeout(item.timer);
      value.error ? item.reject(new Error(JSON.stringify(value.error))) : item.resolve(value.result);
    }
    if (value.method === 'Network.requestWillBeSent') network.push(value.params.request.url);
  });
  const send = (method, params = {}, scoped = true) => new Promise((resolve, reject) => {
    const key = ++id;
    const timer = setTimeout(() => { pending.delete(key); reject(new Error('CDP time-out: ' + method)); }, 10000);
    pending.set(key, {resolve, reject, timer});
    socket.send(JSON.stringify({id:key, method, params, ...(scoped && session ? {sessionId:session} : {})}));
  });
  const {targetId} = await send('Target.createTarget', {url:'about:blank'}, false);
  ({sessionId:session} = await send('Target.attachToTarget', {targetId, flatten:true}, false));
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', {expression, awaitPromise:true, returnByValue:true, userGesture:true});
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const until = async expression => {
    for (let count = 0; count < 100; count++) { if (await evaluate(expression)) return; await wait(30); }
    throw new Error('Verwachte toestand ontbreekt: ' + expression);
  };
  const navigate = async url => { await send('Page.navigate', {url}); await until('document.readyState === "complete"'); };
  const viewport = async (width, height, mobile) => send('Emulation.setDeviceMetricsOverride', {width,height,mobile,deviceScaleFactor:1});
  const capture = async filename => {
    const shot = await send('Page.captureScreenshot', {format:'png', captureBeyondViewport:false});
    fs.writeFileSync(path.join(output, filename), Buffer.from(shot.data, 'base64'));
  };
  await viewport(1280, 1000, false);
  await send('Network.emulateNetworkConditions', {offline:true, latency:0, downloadThroughput:-1, uploadThroughput:-1});
  await navigate(pathToFileURL(path.join(root, 'index.html')).href);
  await until('document.getElementById("bookmarklet").href.startsWith("javascript:")');
  const bookmark = await evaluate('document.getElementById("bookmarklet").href');
  assert.ok(bookmark.length < 65536, 'Bladwijzer is onnodig lang.');
  assert.equal(network.filter(url => /^https?:/.test(url)).length, 0, 'De lokale pagina probeerde een netwerkverbinding.');
  await capture('pagina-desktop.png');
  await evaluate(`document.getElementById('powered-by').value='PHP/8.3.20';document.getElementById('site-address').value='https://jouwsite.nl/';document.getElementById('manual-form').requestSubmit();`);
  const manualMessage = await evaluate('document.querySelector("#result textarea").value');
  assert.equal(manualMessage, createChecker(data).makeMessage('https://jouwsite.nl/', '8.3.20'));
  assert.match(await evaluate('document.getElementById("result").innerText'), /Een oud PHP-nummer is zichtbaar/);
  await evaluate(`Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>{window.__copied=value}}});document.querySelector('#result button').click();`);
  await until('window.__copied !== undefined');
  assert.equal(await evaluate('window.__copied'), manualMessage);
  await evaluate(`Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('blocked')}}});document.execCommand=()=>false;document.querySelector('#result button').click();`);
  await until(`document.querySelector('#result [role=status]').textContent.includes('geselecteerd')`);
  await evaluate('document.getElementById("powered-by").focus()');
  await send('Input.dispatchKeyEvent', {type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
  await send('Input.dispatchKeyEvent', {type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9});
  assert.equal(await evaluate('document.activeElement.id'), 'cms');
  await viewport(375, 812, true);
  await evaluate('window.scrollTo(0,0)');
  assert.ok(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontale overflow op telefoonbreedte.');
  await capture('pagina-telefoonbreedte.png');
  const browserResults = await evaluate(`(() => {const checker=createChecker(JSON.parse(document.getElementById('rules-data').textContent));return ${JSON.stringify(fixtures.cases)}.map(item=>checker.evaluate({...item,url:${JSON.stringify(fixtures.url)},htmlRecords:checker.collectDOM(new DOMParser().parseFromString(item.html,'text/html'))}));})()`);
  for (let i = 0; i < fixtures.cases.length; i++) {
    for (const [key,value] of Object.entries(fixtures.cases[i].expected)) assert.equal(browserResults[i][key], value, fixtures.cases[i].name);
  }
  assert.equal(network.filter(url => /^https?:/.test(url)).length, 0, 'Route B maakte een netwerkverzoek.');
  await send('Network.emulateNetworkConditions', {offline:false, latency:0, downloadThroughput:-1, uploadThroughput:-1});
  await viewport(1100, 1000, false);
  await navigate(site);
  await evaluate('document.getElementById("previous").focus()');
  const bodyBefore = await evaluate('document.body.innerHTML');
  const cookiesBefore = await evaluate('document.cookie');
  const before = requests.length;
  const activate = async () => evaluate(`(() => {const a=document.createElement('a');a.href=${JSON.stringify(bookmark)};document.body.append(a);a.click();a.remove();})()`);
  await activate();
  await until('document.querySelector("[data-php-lek-check-overlay]")?.shadowRoot.querySelector("textarea") !== null && !!document.querySelector("[data-php-lek-check-overlay]")?.shadowRoot.querySelector("textarea")');
  const overlayText = await evaluate('document.querySelector("[data-php-lek-check-overlay]").shadowRoot.querySelector("dialog").innerText');
  const overlayMessage = await evaluate('document.querySelector("[data-php-lek-check-overlay]").shadowRoot.querySelector("textarea").value');
  assert.match(overlayText, /Een oud PHP-nummer is zichtbaar/);
  assert.match(overlayText, /Beoordeling: kan kwetsbaar zijn/);
  assert.match(overlayText, /generator noemt WordPress/);
  assert.equal(requests.length, before+1);
  assert.deepEqual(requests.at(-1), {url:'/',method:'GET'});
  assert.equal(overlayMessage, createChecker(data).makeMessage(site,'8.3.20'));
  await capture('bladwijzer-overlay.png');
  await evaluate('document.querySelector("[data-php-lek-check-overlay]").shadowRoot.querySelector("header button").click()');
  await until('!document.querySelector("[data-php-lek-check-overlay]")');
  assert.equal(await evaluate('document.body.innerHTML'), bodyBefore);
  assert.equal(await evaluate('document.cookie'), cookiesBefore);
  assert.equal(await evaluate('document.activeElement.id'), 'previous');
  assert.equal(await evaluate('localStorage.length'), 0);
  mode = 'redirect';
  const redirectBefore = requests.length;
  await activate();
  await until('!!document.querySelector("[data-php-lek-check-overlay]")?.shadowRoot.querySelector("textarea")');
  assert.match(await evaluate('document.querySelector("[data-php-lek-check-overlay]").shadowRoot.querySelector("dialog").innerText'), /verwijst door/);
  assert.equal(requests.length, redirectBefore+1);
  assert.ok(!requests.some(request => request.url === '/other'));
  mode = 'csp';
  await navigate(site);
  const cspBefore = requests.length;
  await activate(); await wait(100);
  assert.equal(await evaluate('document.querySelector("[data-php-lek-check-overlay]")'), null);
  assert.equal(requests.length, cspBefore, 'Strenge CSP had de bladwijzer moeten blokkeren.');
  const report = {browser:(await send('Browser.getVersion',{},false)).product, sharedCases:fixtures.cases.length,
    offlinePageNetworkRequests:0, bookmarkletRequests:1, redirectFollowed:false, strictCspBlocked:true,
    mobileWidth:375, clipboard:'geïsoleerde testdubbel; systeemklembord niet gebruikt', overlayText, message:overlayMessage};
  fs.writeFileSync(path.join(output,'report.json'), JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
})().catch(error => { console.error(error); process.exitCode=1; }).finally(async () => {
  if (socket) socket.close();
  if (browser) { browser.kill('SIGTERM'); await Promise.race([once(browser,'exit'),wait(2000)]); }
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
  fs.rmSync(temporary,{recursive:true,force:true});
});
