import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  branchExists,
  buildAgnosInstaller,
  buildNeosInstaller,
  renderLandingPage,
  resolveTargetFromPath,
} from "../src/installer.mjs";
import { handleRequest } from "../src/worker.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");

async function readBinary(relativePath) {
  const buffer = await readFile(path.join(root, relativePath));
  return buffer.toString("latin1");
}

test("AGNOS patching swaps repo and branch", async () => {
  const template = await readBinary("templates/installer_openpilot_agnos.bin");
  const binary = buildAgnosInstaller(template, { owner: "MostlyClueless94", branch: "mc-dev" });

  assert(binary.includes("https://github.com/MostlyClueless94/bluepilot.git"));
  assert(binary.includes("mc-dev"));
  assert(!binary.includes("openpilot.git"));
  assert(!binary.includes("sunnypilot.git"));
});

test("NEOS patching swaps repo and branch", async () => {
  const template = await readBinary("templates/installer_openpilot_neos.bin");
  const binary = buildNeosInstaller(template, { owner: "MostlyClueless94", branch: "mc-dev" });

  assert(binary.includes("https://github.com/MostlyClueless94/bluepilot.git"));
  assert(binary.includes("mc-dev"));
  assert(!binary.includes("openpilot.git"));
  assert(!binary.includes("sunnypilot.git"));
});

test("path resolver supports fork and short alias routes", () => {
  assert.deepEqual(resolveTargetFromPath("/fork/MostlyClueless94/mc-dev", {
    defaultOwner: "MostlyClueless94",
    defaultBranch: "mc-dev",
  }), {
    owner: "MostlyClueless94",
    branch: "mc-dev",
  });

  assert.deepEqual(resolveTargetFromPath("/mc-dev", {
    defaultOwner: "MostlyClueless94",
    defaultBranch: "mc-dev",
  }), {
    owner: "MostlyClueless94",
    branch: "mc-dev",
  });
});

test("landing page includes the expected install surface", () => {
  const html = renderLandingPage({
    origin: "https://install.example.com",
    owner: "MostlyClueless94",
    branch: "mc-dev",
    brandName: "BluePilot",
  });

  assert(html.includes("https://install.example.com/fork/MostlyClueless94/mc-dev"));
  assert(html.includes("Download AGNOS Installer"));
  assert(html.includes("Download NEOS Installer"));
});

test("branch lookup accepts a found branch", async () => {
  const exists = await branchExists({
    owner: "MostlyClueless94",
    branch: "mc-dev",
    repoName: "bluepilot",
    fetchImpl: async () => new Response(JSON.stringify({ name: "mc-dev" }), { status: 200 }),
  });

  assert.equal(exists, true);
});

test("branch lookup returns false on 404", async () => {
  const exists = await branchExists({
    owner: "MostlyClueless94",
    branch: "missing",
    repoName: "bluepilot",
    fetchImpl: async () => new Response("{}", { status: 404 }),
  });

  assert.equal(exists, false);
});

test("worker returns a patched AGNOS installer for device requests", async () => {
  const request = new Request("https://install.example.com/fork/MostlyClueless94/mc-dev", {
    headers: {
      "user-agent": "AGNOSSetup-test",
      "x-openpilot-device-type": "tici",
      "x-openpilot-serial": "test",
    },
  });

  const response = await handleRequest(request, {
    BRAND_NAME: "BluePilot",
    DEFAULT_OWNER: "MostlyClueless94",
    DEFAULT_BRANCH: "mc-dev",
    REPO_NAME: "bluepilot",
  }, async () => new Response(JSON.stringify({ name: "mc-dev" }), { status: 200 }));

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "application/octet-stream");

  const binary = Buffer.from(new Uint8Array(await response.arrayBuffer())).toString("latin1");
  assert(binary.includes("https://github.com/MostlyClueless94/bluepilot.git"));
  assert(binary.includes("mc-dev"));
});
