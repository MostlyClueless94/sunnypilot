# SubiPilot Portal Backend

The SubiPilot Portal backend provides HTTP and optional WebSocket APIs for device status, route review, video/log access, raw parameter editing, and route export helpers.

## Process

- Managed process name: `subipilot_portal`
- Manager entrypoint: `sunnypilot.portal.backend.subipilot_portal`
- Main server implementation: `sunnypilot.portal.backend.bp_portal`
- Enable param: `SubiPilotPortalEnabled`
- HTTP port param: `SubiPilotPortalPort`
- Default HTTP port: `8088`
- Optional WebSocket port: `8089`

The server is disabled by default and runs only when `SubiPilotPortalEnabled` is true.

## Data Paths

- Portal data root: `/data/subipilot/portal`
- Route cache: `/data/subipilot/portal/routes`
- Backup filenames: `subipilot-backup-*`
- Log bundles: `subipilot-logs-*`

## API Surface

Stable API paths are preserved for the React app:

- `GET /api/routes`
- `GET /api/routes/{route}`
- `GET /api/params`
- `POST /api/params/set`
- `GET /api/manager-logs`
- `GET /api/logs`
- `GET /api/system`
- `GET /api/cache`

The curated web settings panel is intentionally not part of this first SubiPilot port. The backend returns a safe settings fallback and the web app points users to the raw Parameters page.

## Manual Test

```bash
cd /data/openpilot
python3 -m sunnypilot.portal.backend.subipilot_portal
```
