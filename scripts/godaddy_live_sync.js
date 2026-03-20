const fs = require('fs');
const path = require('path');
const os = require('os');

function parseArgs(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const part = argv[index];
    if (!part.startsWith('--')) {
      continue;
    }
    const key = part.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith('--')) {
      args[key] = true;
      continue;
    }
    args[key] = next;
    index += 1;
  }
  return args;
}

function requirePlaywright() {
  const candidates = [
    'C:/Users/TrifectaAgent/AppData/Roaming/npm/node_modules/openclaw/node_modules/playwright-core',
    path.join(process.env.APPDATA || '', 'npm', 'node_modules', 'openclaw', 'node_modules', 'playwright-core'),
  ];
  for (const candidate of candidates) {
    if (candidate && fs.existsSync(candidate)) {
      return require(candidate);
    }
  }
  return require('playwright-core');
}

async function fetchJson(page, url) {
  return page.evaluate(async (targetUrl) => {
    const response = await fetch(targetUrl, { credentials: 'include' });
    const text = await response.text();
    let body = null;
    try {
      body = JSON.parse(text);
    } catch (error) {
      body = text;
    }
    return {
      ok: response.ok,
      status: response.status,
      body,
    };
  }, url);
}

async function fetchDebuggerVersion(browserUrl) {
  const response = await fetch(`${browserUrl.replace(/\/$/, '')}/json/version`);
  if (!response.ok) {
    throw new Error(`Debugger endpoint returned ${response.status}`);
  }
  return response.json();
}

function cloneProfile(sourceDir) {
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'godaddy-live-sync-'));
  const files = [
    'Local State',
    'Last Version',
    'First Run',
    path.join('Default', 'Preferences'),
    path.join('Default', 'Secure Preferences'),
    path.join('Default', 'Network', 'Cookies'),
    path.join('Default', 'Network', 'Cookies-journal'),
    path.join('Default', 'Network', 'Network Persistent State'),
    path.join('Default', 'Network', 'TransportSecurity'),
    path.join('Default', 'Local Storage', 'leveldb', 'CURRENT'),
    path.join('Default', 'Local Storage', 'leveldb', 'LOCK'),
    path.join('Default', 'Local Storage', 'leveldb', 'LOG'),
    path.join('Default', 'Local Storage', 'leveldb', 'LOG.old'),
    path.join('Default', 'IndexedDB', 'https_conversations.godaddy.com_0.indexeddb.leveldb', 'CURRENT'),
    path.join('Default', 'IndexedDB', 'https_conversations.godaddy.com_0.indexeddb.leveldb', 'LOG'),
    path.join('Default', 'IndexedDB', 'https_conversations.godaddy.com_0.indexeddb.leveldb', 'LOG.old'),
    path.join('Default', 'Session Storage'),
    path.join('Default', 'WebStorage'),
  ];

  for (const relativePath of files) {
    const sourcePath = path.join(sourceDir, relativePath);
    if (!fs.existsSync(sourcePath)) {
      continue;
    }
    const destinationPath = path.join(tempRoot, relativePath);
    fs.mkdirSync(path.dirname(destinationPath), { recursive: true });
    try {
      fs.cpSync(sourcePath, destinationPath, { recursive: true, force: true, errorOnExist: false });
    } catch (error) {
      // Skip files Chrome currently has open; cookies/local state are enough for the live API fetch.
    }
  }

  for (const dbFolder of [
    path.join('Default', 'Local Storage', 'leveldb'),
    path.join('Default', 'IndexedDB', 'https_conversations.godaddy.com_0.indexeddb.leveldb'),
  ]) {
    const sourcePath = path.join(sourceDir, dbFolder);
    if (!fs.existsSync(sourcePath)) {
      continue;
    }
    const destinationPath = path.join(tempRoot, dbFolder);
    fs.mkdirSync(destinationPath, { recursive: true });
    for (const entry of fs.readdirSync(sourcePath)) {
      if (!/\.(ldb|log)$/i.test(entry)) {
        continue;
      }
      try {
        fs.copyFileSync(path.join(sourcePath, entry), path.join(destinationPath, entry));
      } catch (error) {
        // Ignore in-use LevelDB files and continue with whatever is readable.
      }
    }
  }

  return tempRoot;
}

async function main() {
  const args = parseArgs(process.argv);
  const brand = args.brand || process.env.GODADDY_REAMAZE_BRAND_URL;
  const userDataDir = args['user-data-dir'] || process.env.GODADDY_BROWSER_USER_DATA_DIR;
  const executablePath = args.chrome || process.env.GODADDY_CHROME_PATH;
  const browserUrl = args['browser-url'] || process.env.GODADDY_BROWSER_DEBUG_URL || 'http://127.0.0.1:18800';
  const maxPages = Math.max(1, parseInt(args.pages || process.env.GODADDY_LIVE_SYNC_MAX_PAGES || '1', 10));
  const pageSize = Math.max(1, Math.min(parseInt(args['page-size'] || process.env.GODADDY_LIVE_SYNC_PAGE_SIZE || '30', 10), 100));

  if (!brand) {
    throw new Error('Missing GoDaddy Reamaze brand URL');
  }
  if (!userDataDir || !fs.existsSync(userDataDir)) {
    throw new Error(`Browser profile not found: ${userDataDir || '<empty>'}`);
  }
  if (!executablePath || !fs.existsSync(executablePath)) {
    throw new Error(`Chrome executable not found: ${executablePath || '<empty>'}`);
  }

  const { chromium } = requirePlaywright();
  const baseUrl = `https://${brand}.reamaze.godaddy.com/api/v2/conversations`;
  let browser = null;
  let context = null;
  let cleanupDir = null;
  try {
    await fetchDebuggerVersion(browserUrl);
    browser = await chromium.connectOverCDP(browserUrl);
    context = browser.contexts()[0];
  } catch (error) {
    cleanupDir = cloneProfile(userDataDir);
    context = await chromium.launchPersistentContext(cleanupDir, { executablePath, headless: true });
  }
  try {
    const page = context.pages()[0] || await context.newPage();
    await page.goto(`https://conversations.godaddy.com/overview/${brand}`, {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    }).catch(() => {});

    const conversations = [];
    const messageMap = {};
    for (let pageNumber = 1; pageNumber <= maxPages; pageNumber += 1) {
      const response = await fetchJson(page, `${baseUrl}?page=${pageNumber}&status=open&view=inbox&count_per_page=${pageSize}`);
      if (!response.ok || !response.body || !Array.isArray(response.body.conversations)) {
        throw new Error(`Conversation fetch failed on page ${pageNumber} with status ${response.status}`);
      }
      const pageItems = response.body.conversations;
      conversations.push(...pageItems);
      if (pageItems.length < pageSize) {
        break;
      }
    }

    for (const conversation of conversations) {
      const conversationId = conversation && conversation.id;
      if (!conversationId) {
        continue;
      }
      const response = await fetchJson(page, `${baseUrl}/${conversationId}/messages?count_per_page=10&page=1`);
      if (response.ok && response.body && Array.isArray(response.body.messages)) {
        messageMap[String(conversationId)] = response.body.messages;
      } else {
        messageMap[String(conversationId)] = [];
      }
    }

    console.log(JSON.stringify({
      success: true,
      fetched_at: new Date().toISOString(),
      brand,
      total_count: conversations.length,
      conversations,
      messages: messageMap,
    }));
  } finally {
    if (browser) {
      await browser.close();
    } else if (context) {
      await context.close();
    }
    if (cleanupDir) {
      fs.rmSync(cleanupDir, { recursive: true, force: true });
    }
  }
}

main().catch((error) => {
  console.error(JSON.stringify({
    success: false,
    error: error && error.message ? error.message : String(error),
  }));
  process.exit(1);
});
