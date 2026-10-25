(function startPage() {
  const checker = createChecker(JSON.parse(document.getElementById('rules-data').textContent));
  const source = document.getElementById('bookmarklet-source').textContent.trim();
  const bookmark = document.getElementById('bookmarklet');
  bookmark.href = 'javascript:' + encodeURIComponent(source);
  const bookmarkCode = document.getElementById('bookmark-url');
  bookmarkCode.value = bookmark.href;
  document.getElementById('readable-code').textContent = source;
  bookmark.addEventListener('click', event => {
    event.preventDefault();
    const details = document.getElementById('bookmark-code');
    details.open = true;
    details.querySelector('summary').focus();
  });
  document.getElementById('copy-bookmark').addEventListener('click', async () => {
    const copied = await copyText(document, bookmarkCode);
    document.getElementById('bookmark-status').textContent = copied ?
      'Bladwijzercode gekopieerd. Plak deze als adres van je nieuwe bladwijzer.' :
      'De code is geselecteerd. Kopieer zelf met Ctrl+C of Cmd+C.';
  });
  document.getElementById('manual-form').addEventListener('submit', event => {
    event.preventDefault();
    const result = checker.evaluate({
      headers: {'X-Powered-By': document.getElementById('powered-by').value.trim()},
      cms: document.getElementById('cms').checked,
      url: document.getElementById('site-address').value.trim()
    });
    document.getElementById('result-body').replaceChildren(resultView(document, result));
    const container = document.getElementById('result');
    container.hidden = false;
    document.getElementById('manual-status').textContent = 'Je uitslag en bericht staan hieronder.';
    container.focus({preventScroll: true});
    container.scrollIntoView({block: 'start'});
  });
})();
