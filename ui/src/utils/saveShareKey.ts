// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { encodeKey } from "./encryptUtils";

export function saveShareKey(sharekey: string) {
  const key = encodeKey(sharekey);
  localStorage.setItem("workspace_manager_shareKey", key);
}
