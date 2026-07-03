const { spawnSync } = require("node:child_process");
const path = require("node:path");

const nextBin = path.join(__dirname, "..", "node_modules", "next", "dist", "bin", "next");
const env = { ...process.env };

if (process.platform === "win32" && !env.NEXT_PRIVATE_BUILD_WORKER) {
  env.NEXT_PRIVATE_BUILD_WORKER = "0";
}

const result = spawnSync(process.execPath, [nextBin, "build"], {
  env,
  stdio: "inherit",
});

process.exit(result.status ?? 1);
