# Frontend Drafts

This directory contains frontend work that was restored from earlier ComfyWatchman exploration.

## `comfywatchman-dashboard`

Imported from `MooseGooseConsulting/big-ui/Comfyuimodelmanagementdashboard` at commit `6ed8f21febe388d56defda2f4617d9d2f3da003e`.

The dashboard is a React/Vite draft for ComfyUI model and workflow management. It currently uses mock data and service abstractions. The intended next step is to connect it to the Python `comfywatchman` scanner, search, download, inventory, and status APIs.

The restored source repository also contained current-looking October 2025 design and integration docs. Those were intentionally not imported here because they describe stale ComfyUI assumptions. Treat this directory as runnable prototype source, not as the control plane for current ComfyWatchman architecture.

Run it from this directory:

```bash
cd frontend/comfywatchman-dashboard
npm install
npm run dev
```
