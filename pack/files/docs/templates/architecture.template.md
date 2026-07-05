# Architecture

<!-- repo-seed-template:start -->
**Document role**: Managed project-document template
**Template source**: `docs/templates/architecture.template.md`
**Scaffold destination**: `docs/project/architecture.md`
**Scaffold behavior**: The live file is project-owned and never overwritten by sync
<!-- repo-seed-template:end -->

**Project**: [Project Name]
**Version**: [Version]
**Status**: [Draft | Review | Approved]
**Last Updated**: [Date]

---

## Overview

Brief description of the system's purpose and high-level architecture style (monolith, microservices, layered, event-driven, etc.).

---

## System Context

Describe the system boundary and its external actors, systems, and integrations.

| Actor / System | Type | Description |
|---|---|---|
| [User / External System] | [Human / External API / DB] | [What it does with this system] |

---

## Component Structure

List the major components, services, or layers.

| Component | Responsibility |
|---|---|
| [Component A] | [What it does] |
| [Component B] | [What it does] |

Optionally include a diagram (ASCII, Mermaid, or linked image):

```
[Client] → [API Layer] → [Service Layer] → [Data Layer]
```

---

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | | |
| Backend | | |
| Database | | |
| Auth | | |
| CI/CD | | |
| Hosting | | |

---

## Data Flow

Describe key data flows through the system. Focus on flows that span multiple components or have non-obvious behavior.

---

## Key Design Decisions

Document significant architectural choices and the reasoning behind them.

| Decision | Options Considered | Chosen | Reason |
|---|---|---|---|
| | | | |

---

## Deployment Architecture

Describe how the system is deployed: environments, hosting, infrastructure dependencies, and network topology.

---

## Integrations

List external integrations, APIs, services, and third-party dependencies.

| Integration | Purpose | Auth Method | Notes |
|---|---|---|---|
| | | | |

---

## Security Considerations

Note security responsibilities, trust boundaries, auth/authz patterns, and known risks.

---

## Known Constraints and Limitations

Document known technical constraints, capacity limits, or architectural trade-offs.

---

## Open Questions

Track unresolved architectural questions or decisions pending approval.

-
