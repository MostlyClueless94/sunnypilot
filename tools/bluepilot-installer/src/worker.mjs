import {
  branchExists,
  buildBinaryResponse,
  buildErrorResponse,
  detectPlatform,
  renderLandingPage,
  resolveTargetFromPath,
} from "./installer.mjs";
import { AGNOS_TEMPLATE_BASE64, NEOS_TEMPLATE_BASE64 } from "./template-data.mjs";

const decodeBase64 = (base64) => {
  if (typeof atob === "function") {
    return atob(base64);
  }

  return Buffer.from(base64, "base64").toString("latin1");
};

const agnosTemplateBinary = decodeBase64(AGNOS_TEMPLATE_BASE64);
const neosTemplateBinary = decodeBase64(NEOS_TEMPLATE_BASE64);

function getDefaults(env) {
  return {
    brandName: env.BRAND_NAME ?? "BluePilot",
    defaultOwner: env.DEFAULT_OWNER ?? "MostlyClueless94",
    defaultBranch: env.DEFAULT_BRANCH ?? "mc-dev",
    repoName: env.REPO_NAME ?? "bluepilot",
  };
}

async function handleRequest(request, env, fetchImpl = fetch) {
  const url = new URL(request.url);
  const defaults = getDefaults(env);

  let target;
  try {
    target = resolveTargetFromPath(url.pathname, defaults);
  } catch (error) {
    return buildErrorResponse(error.message, 400);
  }

  if (target === null) {
    return new Response(
      renderLandingPage({
        origin: url.origin,
        owner: defaults.defaultOwner,
        branch: defaults.defaultBranch,
        brandName: defaults.brandName,
      }),
      {
        status: 200,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      },
    );
  }

  try {
    const exists = await branchExists({
      owner: target.owner,
      branch: target.branch,
      repoName: defaults.repoName,
      fetchImpl,
    });

    if (!exists) {
      return buildErrorResponse(`No public ${defaults.repoName} branch found for ${target.owner}/${target.branch}.`, 404);
    }
  } catch (error) {
    return buildErrorResponse(`Unable to verify ${target.owner}/${defaults.repoName}@${target.branch}: ${error.message}`, 502);
  }

  const platform = detectPlatform(request);
  if (platform === null) {
    return new Response(
      renderLandingPage({
        origin: url.origin,
        owner: target.owner,
        branch: target.branch,
        brandName: defaults.brandName,
      }),
      {
        status: 200,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "public, max-age=300",
        },
      },
    );
  }

  const templateBinary = platform === "agnos" ? agnosTemplateBinary : neosTemplateBinary;
  return buildBinaryResponse({
    platform,
    templateBinary,
    owner: target.owner,
    branch: target.branch,
    repoName: defaults.repoName,
    brandName: defaults.brandName,
  });
}

export default {
  fetch(request, env) {
    return handleRequest(request, env);
  },
};

export { handleRequest };
