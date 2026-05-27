# Copilot Graft Provenance

Date: 2026-05-27

## Repository State

- Canonical repository: `Coldaine/ComfyWatchman`.
- Pre-graft tag: `pre-copilot-graft-2026-05-27`.
- Pre-graft PR: `#16`, `Document Copilot investigation spike findings`.
- Pre-graft archive path: `archive/comfywatchman-pre-copilot-graft/`.

## Donor Code

- Donor repository: `vehoelite/ComfyUI-Copilot`.
- Donor commit imported as active root:
  `2916691782d159b1327b93ac6662c37051e657aa`.
- Upstream project: `AIDC-AI/ComfyUI-Copilot`.
- Relevant upstream PR: `AIDC-AI/ComfyUI-Copilot#130`, head
  `vehoelite:main`.

## Import Method

The graft branch archives the old ComfyWatchman tree first, then merges the
donor repository with unrelated history so both lineages remain auditable. The
donor tree becomes the active root because Copilot already owns the ComfyUI
custom-node runtime, chat UI, canvas context, workflow cards, Agent Mode route,
provider configuration, and workflow save/execute tool loop.

## License and Attribution

- Active root license and attribution are inherited from ComfyUI-Copilot:
  `LICENSE`, `NOTICE.txt`, and `Authors.txt`.
- The archived ComfyWatchman license remains at
  `archive/comfywatchman-pre-copilot-graft/LICENSE`.
- The archived ComfyWatchman submodule boundary remains at
  `archive/comfywatchman-pre-copilot-graft/.gitmodules` and
  `archive/comfywatchman-pre-copilot-graft/src/copilot_backend`.

## Follow-Up Policy

- Do not reintroduce old ComfyWatchman shell code unless it directly supports
  Copilot as the active shell.
- Reintroduce read-only tools first: scanner, inventory, readiness report.
- Add search and install planning only after the read-only tool contract is
  stable.
- Keep mutation behind explicit approval and prefer ComfyUI-Manager for
  snapshots/install operations where possible.

