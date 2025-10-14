# Standards: Domain Architecture Documents

**Owner:** Architecture Team
**Status:** Active

---

## 1. Purpose

This document establishes the standard for creating and maintaining detailed architectural plans for distinct "domains" within the `ComfyFixerSmart` project. A domain represents a major, self-contained feature or capability, such as the "Automated Download Workflow."

The primary goal of this standard is to ensure that our core architectural documentation remains clean, high-level, and readable, while providing a clear path for developers to access deep, exhaustive details when necessary.

## 2. The Standard

### 2.1. Principle of Separation

-   **High-Level Summary:** The main `docs/architecture.md` document **MUST** only contain a summarized, high-level description of each major component or domain. This summary should be concise (typically 3-5 bullet points) and focus on the component's role and its primary interactions with the rest of the system.

-   **Exhaustive Framework:** The complete, detailed, and exhaustive technical plan for a domain **MUST** be placed in its own dedicated file within the `docs/domains/` subdirectory.

### 2.2. Document Location and Naming

-   All exhaustive domain frameworks **MUST** be located in the `/docs/domains/` directory.
-   The filename **MUST** be descriptive and use all capital letters with underscores, for example: `AUTOMATED_DOWNLOAD_WORKFLOW.md`.

### 2.3. Required Linkage

-   The summary of a component in `docs/architecture.md` **MUST** conclude with a direct, relative link to its corresponding exhaustive framework document.
-   **Example:**
    ```markdown
    - Automated Download & Verification Service
      - Evolves the Downloader into a "fire-and-forget" background service.
      - Uses a persistent job queue to manage pending downloads.
      - Employs an agentic worker for asynchronous downloading and verification.
      - **Exhaustive Framework:** For a complete breakdown of this service, see the detailed domain document: **[Automated Download & Verification Workflow](domains/AUTOMATED_DOWNLOAD_WORKFLOW.md)**.
    ```

### 2.4. Content Requirements for Domain Documents

Each exhaustive framework document in `docs/domains/` **MUST** contain, at a minimum, the following sections:

1.  **Header:** Including the `Owner` of the domain and the `Status` of the document (e.g., Proposed, Active, Deprecated).
2.  **Overview:** A detailed explanation of the feature, its purpose, and the problem it solves.
3.  **Architectural Components:** A breakdown of all the major classes, modules, or services that make up the domain.
4.  **Detailed Lifecycle / Workflow:** A step-by-step description of the data flow and user journey through the system. This is the most critical section.
5.  **Tooling and Maintenance:** A description of any new CLI tools, logging, configuration, or maintenance processes associated with the domain.

By adhering to this standard, we ensure our documentation is layered, scalable, and easy to navigate for all team members.
