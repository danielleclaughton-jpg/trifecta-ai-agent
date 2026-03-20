const path = require('path');

const { chromium } = require('C:\\Users\\TrifectaAgent\\AppData\\Roaming\\npm\\node_modules\\openclaw\\node_modules\\playwright-core');

async function main() {
  const userDataDir = 'C:\\Users\\TrifectaAgent\\.openclaw\\browser\\openclaw\\user-data';
  const executablePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const screenshotPath = path.join(process.cwd(), '.logs', 'godaddy-probe.png');

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    executablePath,
    ignoreDefaultArgs: ['--enable-automation'],
    args: ['--disable-blink-features=AutomationControlled'],
    viewport: { width: 1440, height: 1100 },
  });

  try {
    const page = context.pages()[0] || await context.newPage();
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });
    await page.goto('https://conversations.godaddy.com/conversations', {
      waitUntil: 'domcontentloaded',
      timeout: 45000,
    });
    await page.waitForTimeout(10000);
    await page.screenshot({ path: screenshotPath, fullPage: true });

    const info = await page.evaluate(() => ({
      href: location.href,
      title: document.title,
      bodyText: document.body ? document.body.innerText.slice(0, 1000) : '',
    }));

    const cookies = await context.cookies(['https://conversations.godaddy.com']);
    console.log(JSON.stringify({
      ...info,
      screenshotPath,
      cookieCount: cookies.length,
      cookieNames: cookies.slice(0, 20).map((cookie) => cookie.name),
    }, null, 2));
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
