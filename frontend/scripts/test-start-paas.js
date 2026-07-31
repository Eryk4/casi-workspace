const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { EventEmitter } = require("node:events");
const path = require("node:path");
const { HOST, buildStartCommand, main, parsePort } = require("./start-paas");

assert.equal(HOST, "0.0.0.0");
assert.equal(parsePort(undefined), 3000);
assert.equal(parsePort("43123"), 43123);
for (const value of ["abc", "0", "65536", "-1", "3.14"]) {
  assert.throws(() => parsePort(value), /PORT/);
}

const built = buildStartCommand({ PORT: "41234" });
assert.equal(built.command, process.execPath);
assert.deepEqual(
  built.args.slice(-5),
  ["start", "--hostname", "0.0.0.0", "--port", "41234"],
);
assert.ok(!built.args.includes("dev"));

const script = path.join(__dirname, "start-paas.js");
const invalid = spawnSync(process.execPath, [script], {
  env: { ...process.env, PORT: "invalid" },
  encoding: "utf8",
  timeout: 10_000,
});
assert.notEqual(invalid.status, 0);
assert.match(invalid.stderr, /PORT/);

const child = new EventEmitter();
child.killed = false;
child.kill = () => true;
let spawnOptions;
const previousExitCode = process.exitCode;
process.exitCode = undefined;
assert.equal(
  main({ ...process.env, PORT: "41235" }, (_command, _args, options) => {
    spawnOptions = options;
    return child;
  }),
  null,
);
child.emit("exit", 7, null);
assert.equal(process.exitCode, 7);
assert.equal(spawnOptions.env.PORT, "41235");
process.exitCode = previousExitCode;

console.log("PaaS frontend start tests passed.");
