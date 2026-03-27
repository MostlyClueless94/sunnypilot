import assert from "node:assert/strict";

function usage() {
  console.error("Usage: node scripts/verify-live.mjs <base-url> [owner] [branch]");
  process.exit(1);
}

const [, , baseUrl, owner = "MostlyClueless94", branch = "mc-dev"] = process.argv;
if (!baseUrl) {
  usage();
}

async function fetchBinary(url, headers) {
  const response = await fetch(url, { headers });
  assert.equal(response.status, 200, `Expected 200 from ${url}, got ${response.status}`);
  const buffer = new Uint8Array(await response.arrayBuffer());
  return Buffer.from(buffer).toString("latin1");
}

const remote = `https://github.com/${owner}/bluepilot.git`;
const path = `${baseUrl.replace(/\/$/, "")}/fork/${owner}/${branch}`;

const agnos = await fetchBinary(path, {
  "user-agent": "AGNOSSetup-test",
  "x-openpilot-serial": "test",
  "x-openpilot-device-type": "tici",
});
assert(agnos.includes(remote), "AGNOS installer did not include the bluepilot remote");
assert(agnos.includes(branch), "AGNOS installer did not include the target branch");
assert(!agnos.includes("openpilot.git"), "AGNOS installer still includes openpilot.git");
assert(!agnos.includes("sunnypilot.git"), "AGNOS installer still includes sunnypilot.git");

const neos = await fetchBinary(path, {
  "user-agent": "NEOSSetup-test",
});
assert(neos.includes(remote), "NEOS installer did not include the bluepilot remote");
assert(neos.includes(branch), "NEOS installer did not include the target branch");
assert(!neos.includes("openpilot.git"), "NEOS installer still includes openpilot.git");
assert(!neos.includes("sunnypilot.git"), "NEOS installer still includes sunnypilot.git");

console.log(`Live installer verified for ${owner}/bluepilot@${branch}`);
