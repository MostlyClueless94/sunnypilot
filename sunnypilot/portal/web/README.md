# SubiPilot Portal Web App

React/Vite frontend for the local SubiPilot Portal.

## Features

- Dashboard and device status
- Local route and video review
- Manager log viewing
- Raw parameter review and editing
- Safe Settings fallback that links to Parameters when curated panel JSON is unavailable

## Building

```bash
cd sunnypilot/portal/web
npm ci
npm run build:no-clean
```

The built output is committed under `public/` so the device can serve the portal without running Node.
