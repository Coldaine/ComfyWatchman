// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import { Table } from "./db-tables/WorkspaceDB";
import type { ModelsListRespItem } from "./model-manager/types";
import { api } from "./utils/comfyapp";

export function fetchApi(
  route: string,
  options?: RequestInit,
): Promise<Response> {
  if (api == null) {
    console.error("api is null!");
    throw new Error("api is null!");
  }
  return api.fetchApi(route, options);
}

export async function getDB(table: Table): Promise<string | undefined> {
  console.warn("[workspace deprecated] getDB is deprecated", table);
  try {
    const response = await fetchApi(`/workspace/get_db?table=${table}`);
    if (!response.ok) {
      return undefined;
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching workspace:", error);
    return undefined;
  }
}

export async function fetchMyWorkflowsDir() {
  const resp = await fetchApi("/workspace/get_my_workflows_dir");
  const res = (await resp.json()) as {
    path?: string;
    error?: string;
    os: "win32" | "darwin" | "linux";
  };
  if (res.error) {
    alert(`Failed to fetch my workflows path: ${res.error}`);
  }
  return res;
}
