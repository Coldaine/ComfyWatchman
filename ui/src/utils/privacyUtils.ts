// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import type { EWorkflowPrivacy } from "../types/dbTypes";

export function getPrivacyEmoji(privacy: EWorkflowPrivacy) {
  switch (privacy) {
    case "PRIVATE":
      return "🔒";
    case "PUBLIC":
      return "🌐";
    case "UNLISTED":
      return "🔗";
    default:
      return "";
  }
}
