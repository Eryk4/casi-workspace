const { spawnSync } = require("node:child_process");
const path = require("node:path");

const tests = [
  "test-dashboard.js",
  "test-daily-brief.js",
  "test-organization-context.js",
  "test-auth-session.js",
  "test-invoices.js",
  "test-work-items.js",
  "test-work-item-detail.js",
  "test-documents.js",
  "test-document-detail.js",
  "test-billing.js",
  "test-boss-assistant.js",
  "test-company-assistant.js",
  "test-crm.js",
  "test-contractor-detail.js",
  "test-reports.js",
  "test-settings.js",
];

const scriptsDir = __dirname;

function waitBeforeRetry(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function runTestScript(testPath, attempts = 3) {
  let lastResult;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const result = spawnSync(process.execPath, [testPath], {
      cwd: path.join(scriptsDir, ".."),
      stdio: "inherit",
      windowsHide: true,
    });

    if (!result.error || result.error.code !== "EPERM" || attempt === attempts) {
      return result;
    }

    lastResult = result;
    console.warn(`[frontend-models] Node spawn returned EPERM, retrying (${attempt + 1}/${attempts})...`);
    waitBeforeRetry(350);
  }

  return lastResult;
}

for (const testFile of tests) {
  const testPath = path.join(scriptsDir, testFile);
  console.log(`\n[frontend-models] Running ${testFile}`);

  const result = runTestScript(testPath);

  if (result.error) {
    console.error(`[frontend-models] Failed to start ${testFile}: ${result.error.message}`);
    process.exit(1);
  }

  if (result.status !== 0) {
    console.error(`[frontend-models] ${testFile} failed with exit code ${result.status}.`);
    process.exit(result.status ?? 1);
  }
}

console.log("\n[frontend-models] All frontend model tests passed.");
