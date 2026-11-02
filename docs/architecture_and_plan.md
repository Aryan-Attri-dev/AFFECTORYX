# AFFECTORYX: Engineering Intelligence Platform
## Implementation & Architecture Plan

### 1. System Vision & Architecture Overview
AFFECTORYX is an enterprise-grade engineering intelligence platform that evaluates the consequences of software changes prior to deployment. It computes an evidence-based dependency graph across services, APIs, databases, customers, and business workflows.

#### Core Tenets
1. **Evidence-Based & Deterministic**: Every link in the dependency graph references concrete evidence (OpenAPI schema, callsite analysis, DB migration, customer contract). Never mark an unknown dependency as safe.
2. **True Multi-Tenancy**: Strict organization-level data isolation at the storage, service, and API boundaries.
3. **Engineering-Grade Aesthetics**: Deep midnight navy and charcoal surfaces, restrained emerald/cyan accents, dense high-signal data tables and network topologies, without generic flashy clutter.
4. **Modular Monolith**: Clean domain boundaries (Auth, Orgs, Projects, Ingestion, Graph Engine, Evidence Registry, Change Analyzer, Impact Simulation, Reporting).

---

### 2. Five-Phase Implementation Roadmap

- **Phase 1: Foundations, Multi-Tenancy, Auth & Project Management [ACTIVE]**
  - Backend: FastAPI, SQLAlchemy 2.0, Pydantic v2, JWT RBAC, Tenant Isolation
  - Frontend: Next.js (App Router), TypeScript, Tailwind CSS, Dark Midnight Theme
  - Testing: Automated test suite for Auth, Multi-tenant Isolation, Projects
- **Phase 2: Dependency Graph Engine, Evidence Registry & Ingestion**
  - NetworkX + SQLAlchemy graph modeling (Services, Endpoints, Schemas, Tables)
  - OpenAPI v3 & JSON Schema parser with breaking change analyzer
  - GitHub / Git repository AST & callsite ingestion parser
  - Evidence provenance registry (confirmed, inferred, unknown)
- **Phase 3: Change Analyzer, Impact Simulator & Explainable Reporting**
  - Blast radius calculation (transitive dependencies, downstream consumers)
  - Breaking change detector (API removal, field type mutation, DB migration risk)
  - Customer Impact mapping (contracted workflows, SLO breaches)
  - Deterministic impact report generation with exportable manifests
- **Phase 4: Enterprise Dashboard, React Flow Graph Visualizer & Public API**
  - Interactive React Flow dependency topology canvas with evidence inspector
  - Customer intelligence matrix & impact simulator UI
  - Developer API (CLI & CI/CD webhook integrations)
- **Phase 5: Containerization, Synthetic Dataset, Comprehensive Verification & QA**
  - Docker Compose orchestration (PostgreSQL, Redis, Backend, Frontend)
  - End-to-end integration tests (Playwright + Pytest)
  - Production hardening audit & documentation
