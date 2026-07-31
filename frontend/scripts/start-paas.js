const { spawn } = require("node:child_process");
const path = require("node:path");

const DEFAULT_PORT = 3000;
const HOST = "0.0.0.0";

function parsePort(rawValue) {
  const value = String(rawValue ?? "").trim();
  if (!value) return DEFAULT_PORT;
  if (!/^[0-9]+$/.test(value)) {
    throw new Error("PORT musi byc liczba calkowita od 1 do 65535.");
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 1 || parsed > 65535) {
    throw new Error("PORT musi byc liczba calkowita od 1 do 65535.");
  }
  return parsed;
}

function buildStartCommand(environment = process.env) {
  const nextBin = path.join(__dirname, "..", "node_modules", "next", "dist", "bin", "next");
  return {
    command: process.execPath,
    args: [nextBin, "start", "--hostname", HOST, "--port", String(parsePort(environment.PORT))],
  };
}

function main(environment = process.env, spawnProcess = spawn) {
  let command;
  try {
    command = buildStartCommand(environment);
  } catch (error) {
    process.stderr.write(`Nie mozna uruchomic frontendu PaaS: ${error.message}\n`);
    return 1;
  }

  const child = spawnProcess(command.command, command.args, {
    env: environment,
    stdio: "inherit",
    windowsHide: true,
  });
  let childFinished = false;

  const forwardSignal = (signal) => {
    if (!childFinished && !child.killed) child.kill(signal);
  };
  process.once("SIGINT", () => forwardSignal("SIGINT"));
  process.once("SIGTERM", () => forwardSignal("SIGTERM"));

  child.once("error", () => {
    childFinished = true;
    process.stderr.write("Nie udalo sie uruchomic produkcyjnego procesu Next.js.\n");
    process.exitCode = 1;
  });
  child.once("exit", (code, signal) => {
    childFinished = true;
    if (signal) {
      process.exitCode = signal === "SIGINT" ? 130 : 143;
      return;
    }
    process.exitCode = Number.isInteger(code) ? code : 1;
  });
  return null;
}

if (require.main === module) {
  const exitCode = main();
  if (Number.isInteger(exitCode)) process.exitCode = exitCode;
}

module.exports = { DEFAULT_PORT, HOST, buildStartCommand, main, parsePort };
