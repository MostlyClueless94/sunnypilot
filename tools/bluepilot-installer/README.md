# BluePilot Installer Host

This folder contains a standalone custom installer host for the BluePilot dual-vehicle fork.

## Why this exists

`installer.comma.ai/<owner>/<branch>` always generates an installer that clones `https://github.com/<owner>/openpilot.git`. That works for `MostlyClueless94/openpilot`, but it cannot install the new BluePilot project from `MostlyClueless94/bluepilot` without disturbing the existing SubiPilot install surface.

This worker keeps the device checkout path at `/data/openpilot`, but it patches the installer binary so the clone source is:

`https://github.com/<owner>/bluepilot.git`

## Supported URLs

- Device install: `https://<host>/fork/<github-owner>/<branch>`
- Short alias for the default owner: `https://<host>/<branch>`
- Browser download helpers:
  - `?platform=agnos`
  - `?platform=neos`

For your current project, the intended install URL is:

`https://<host>/fork/MostlyClueless94/mc-dev`

## Local verification

Run the binary patch tests:

```powershell
node --test test/*.test.mjs
```

Regenerate the embedded template module after changing the template binaries:

```powershell
node scripts/embed-templates.mjs
```

Verify a deployed endpoint:

```powershell
node scripts/verify-live.mjs https://<host> MostlyClueless94 mc-dev
```

## Deployment

Install Wrangler:

```powershell
npm.cmd install
```

Deploy to a temporary `workers.dev` URL:

```powershell
npx.cmd wrangler deploy
```

After the worker is live, attach your custom domain such as `install.bluepilot.ai` in Cloudflare and point users to:

`https://install.bluepilot.ai/fork/MostlyClueless94/mc-dev`

## Template source

The base AGNOS and NEOS template installers in `templates/` are derived from the MIT-licensed `sshane/openpilot-installer-generator` project and are patched at request time for the BluePilot repo and target branch.
