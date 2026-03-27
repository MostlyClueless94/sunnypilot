const AGNOS_REMOTE_PLACEHOLDER = "27182818284590452353602874713526624977572470936999595";
const AGNOS_BRANCH_PLACEHOLDER = "161803398874989484820458683436563811772030917980576286213544862270526046281890244970720720418939113748475408807538689175212663386222353693179318006076672635443338908659593958290563832266131992829026788067520876689250171169620703222104321626954862629631361";
const AGNOS_LOADING_PLACEHOLDER = "314159265358979323846264338327950288419";

const NEOS_OWNER_PLACEHOLDER = "271828182845904523536028747135266249775724709369995957496696762772407663035354759457138217852516642742746639193200305992181741359662904357290033429526059563073813232862794349076323382988075319525101901157383418793070215408914993488416750924476146066808226";
const NEOS_LOADING_PLACEHOLDER = "314159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344612847564823378678316527120190914564";
const NEOS_BRANCH_INSERT_MARKER = "--depth=1 openpilot";
const NEOS_REPO_PLACEHOLDER = "openpilot.git";

const DEFAULT_MAX_GITHUB_USERNAME = 39;
const DEFAULT_MAX_BRANCH = 255;
const DEFAULT_LOADING_MESSAGE = "BluePilot";

export function binaryStringToBytes(binary) {
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i) & 0xff;
  }
  return bytes;
}

function binaryReplaceAll(binary, search, replacement) {
  return binary.split(search).join(replacement);
}

function padRight(value, targetLength, padChar) {
  if (value.length > targetLength) {
    throw new Error(`Value exceeds padded length (${value.length} > ${targetLength})`);
  }

  return value + padChar.repeat(targetLength - value.length);
}

function fillPlaceholder(binary, placeholder, value, padChar) {
  return binaryReplaceAll(binary, placeholder, padRight(value, placeholder.length, padChar));
}

function buildGithubRemote(owner, repoName) {
  return `${owner}/${repoName}.git`;
}

function validateOwner(owner) {
  if (!/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$/.test(owner)) {
    throw new Error("GitHub owner must be 1-39 characters of letters, numbers, or hyphens.");
  }
}

function validateBranch(branch) {
  if (branch.length < 1 || branch.length > DEFAULT_MAX_BRANCH) {
    throw new Error("Branch name must be between 1 and 255 characters.");
  }
  if (/[\\\u0000-\u001f\u007f]/.test(branch)) {
    throw new Error("Branch name contains unsupported control characters.");
  }
}

export function normalizeTarget({ owner, branch, repoName = "bluepilot", brandName = "BluePilot" }) {
  if (!owner || !branch) {
    throw new Error("Both owner and branch are required.");
  }

  validateOwner(owner);
  validateBranch(branch);

  return {
    owner,
    branch,
    repoName,
    brandName,
    remotePath: buildGithubRemote(owner, repoName),
    loadingMessage: DEFAULT_LOADING_MESSAGE,
  };
}

export function buildAgnosInstaller(templateBinary, target) {
  const resolved = normalizeTarget(target);

  let binary = templateBinary;
  binary = fillPlaceholder(binary, AGNOS_REMOTE_PLACEHOLDER, resolved.remotePath, "\0");
  binary = fillPlaceholder(binary, AGNOS_BRANCH_PLACEHOLDER, resolved.branch, "\0");
  binary = fillPlaceholder(binary, AGNOS_LOADING_PLACEHOLDER, resolved.loadingMessage, " ");

  return binary;
}

export function buildNeosInstaller(templateBinary, target) {
  const resolved = normalizeTarget(target);

  let binary = templateBinary;
  binary = binaryReplaceAll(binary, NEOS_OWNER_PLACEHOLDER, resolved.owner);
  binary = binaryReplaceAll(binary, NEOS_REPO_PLACEHOLDER, "bluepilot.git\0");

  const markerIndex = binary.indexOf(NEOS_BRANCH_INSERT_MARKER);
  if (markerIndex < 0) {
    throw new Error("Unable to locate NEOS branch insertion marker.");
  }

  const insertIndex = markerIndex + NEOS_BRANCH_INSERT_MARKER.length;
  const ownerPadding = NEOS_OWNER_PLACEHOLDER.length - resolved.owner.length;
  binary = binary.slice(0, insertIndex) + " ".repeat(ownerPadding) + binary.slice(insertIndex);

  if (resolved.branch) {
    const branchValue = ` -b ${resolved.branch}`;
    const branchStartIndex = binary.indexOf(NEOS_BRANCH_INSERT_MARKER) + NEOS_BRANCH_INSERT_MARKER.length;
    binary = binary.slice(0, branchStartIndex) + branchValue + binary.slice(branchStartIndex + branchValue.length);
  }

  binary = fillPlaceholder(binary, NEOS_LOADING_PLACEHOLDER, resolved.loadingMessage, "\0");

  return binary;
}

export function buildInstallerBinary({ platform, templateBinary, owner, branch, repoName = "bluepilot", brandName = "BluePilot" }) {
  if (platform === "agnos") {
    return buildAgnosInstaller(templateBinary, { owner, branch, repoName, brandName });
  }
  if (platform === "neos") {
    return buildNeosInstaller(templateBinary, { owner, branch, repoName, brandName });
  }

  throw new Error(`Unsupported platform: ${platform}`);
}

export function buildBinaryResponse({ platform, templateBinary, owner, branch, repoName, brandName }) {
  const binary = buildInstallerBinary({ platform, templateBinary, owner, branch, repoName, brandName });
  const bytes = binaryStringToBytes(binary);
  return new Response(bytes, {
    status: 200,
    headers: {
      "content-type": "application/octet-stream",
      "content-length": String(bytes.length),
      "content-disposition": 'attachment; filename="installer"',
      "cache-control": "public, max-age=300",
    },
  });
}

export async function branchExists({ owner, branch, repoName = "bluepilot", fetchImpl = fetch }) {
  const apiUrl = `https://api.github.com/repos/${owner}/${repoName}/branches/${encodeURIComponent(branch)}`;
  const response = await fetchImpl(apiUrl, {
    headers: {
      "accept": "application/vnd.github+json",
      "user-agent": "bluepilot-installer",
    },
  });

  if (response.status === 404) {
    return false;
  }

  if (!response.ok) {
    throw new Error(`GitHub branch lookup failed with status ${response.status}.`);
  }

  return true;
}

export function detectPlatform(request) {
  const url = new URL(request.url);
  const forced = url.searchParams.get("platform");
  if (forced === "agnos" || forced === "neos") {
    return forced;
  }

  const userAgent = request.headers.get("user-agent") ?? "";
  if (userAgent.includes("NEOSSetup")) {
    return "neos";
  }
  if (userAgent.includes("AGNOSSetup") || request.headers.has("x-openpilot-device-type")) {
    return "agnos";
  }

  return null;
}

export function isDeviceRequest(request) {
  return detectPlatform(request) !== null;
}

export function resolveTargetFromPath(pathname, defaults) {
  const trimmed = pathname.replace(/^\/+|\/+$/g, "");
  if (!trimmed) {
    return null;
  }

  const segments = trimmed.split("/").map((segment) => decodeURIComponent(segment));
  if (segments[0] === "fork") {
    if (segments.length < 3) {
      throw new Error("Fork installs must use /fork/<owner>/<branch>.");
    }
    return {
      owner: segments[1],
      branch: segments.slice(2).join("/"),
    };
  }

  if (segments.length === 1) {
    return {
      owner: defaults.defaultOwner,
      branch: segments[0],
    };
  }

  throw new Error("Unsupported installer path.");
}

export function renderLandingPage({ origin, owner, branch, brandName }) {
  const agnosUrl = `${origin}/fork/${owner}/${encodeURIComponent(branch)}?platform=agnos`;
  const neosUrl = `${origin}/fork/${owner}/${encodeURIComponent(branch)}?platform=neos`;
  const installUrl = `${origin}/fork/${owner}/${branch}`;

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${brandName} Installer</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #09111d;
        --panel: rgba(14, 31, 52, 0.92);
        --text: #f5f7fa;
        --muted: #b1c2d8;
        --accent: #3ba4ff;
        --accent-2: #5dd6d0;
      }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Segoe UI", sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(59, 164, 255, 0.24), transparent 34%),
          radial-gradient(circle at bottom right, rgba(93, 214, 208, 0.18), transparent 28%),
          linear-gradient(160deg, #050a12 0%, #0b1627 56%, #06101d 100%);
        display: grid;
        place-items: center;
        padding: 24px;
      }
      main {
        width: min(760px, 100%);
        background: var(--panel);
        border: 1px solid rgba(110, 156, 205, 0.22);
        border-radius: 20px;
        box-shadow: 0 26px 60px rgba(0, 0, 0, 0.35);
        padding: 32px;
      }
      h1 {
        margin: 0 0 12px;
        font-size: 2.2rem;
      }
      p {
        color: var(--muted);
        line-height: 1.5;
      }
      code {
        display: block;
        margin: 18px 0;
        padding: 14px 16px;
        border-radius: 12px;
        background: rgba(3, 10, 20, 0.9);
        color: #cbe7ff;
        overflow-wrap: anywhere;
      }
      .buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 20px;
      }
      a.button {
        text-decoration: none;
        color: #031120;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        padding: 12px 18px;
        border-radius: 999px;
        font-weight: 700;
      }
      .meta {
        margin-top: 22px;
        color: var(--muted);
        font-size: 0.95rem;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>${brandName} Installer</h1>
      <p>This host serves custom installers that clone <strong>${owner}/bluepilot</strong> while still installing into <strong>/data/openpilot</strong> on-device.</p>
      <code>${installUrl}</code>
      <div class="buttons">
        <a class="button" href="${agnosUrl}">Download AGNOS Installer</a>
        <a class="button" href="${neosUrl}">Download NEOS Installer</a>
      </div>
      <div class="meta">
        Target branch: <strong>${branch}</strong><br>
        Repo: <strong>${owner}/bluepilot</strong>
      </div>
    </main>
  </body>
</html>`;
}

export function buildErrorResponse(message, status = 400) {
  return new Response(message, {
    status,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}
