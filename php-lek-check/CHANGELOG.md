# Changelog

## 1.0.0 (2026-10-25)

First public version.

- The README opens with the message to send to your host. For most owners that message
  is all they need; the tool is optional.
- Python script: one GET to the given page, no packages, no files written. Reads
  `X-Powered-By`, `Server`, `Link`, the `PHPSESSID` cookie name and HTML signals, and
  rates a visible PHP version against the fix per branch (8.2.35, 8.3.36, 8.4.27,
  8.5.12), with stricter outcomes for 7.4 to 8.1 and for 7.3 and older.
- Skill `php-lek-check` that runs the script and explains the outcome in plain Dutch.
- Standalone page `index.html` with a bookmarklet and a paste field. The page itself
  makes no connection (CSP `connect-src 'none'`); the bookmarklet makes exactly one
  same-origin request.
- One rule source (`rules.json`) for Python and JavaScript, 70 shared test cases, 50
  Python and 75 JavaScript tests, a mutation check on the 8.4.27 boundary and an
  optional headless browser run.
- Version table checked on 2026-10-24 against the PHP advisories and the PHP
  announcement of 2026-10-21.
