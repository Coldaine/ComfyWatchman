// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

//@ts-ignore
import { api } from "../../scripts/api.js";

setTimeout(() => {
  import(api.api_base + "/copilot_web/input.js");
  const fontsLink = document.createElement("link");
  fontsLink.rel = "stylesheet";
  fontsLink.href = api.api_base + "/copilot_web/fonts.css";
  document.head.appendChild(fontsLink);
}, 500);
