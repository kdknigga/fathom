# Quick Task 1: Create GitHub Actions to build container and store in GHCR - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Task Boundary

Create a GitHub Actions workflow that builds the Docker container image from the existing Dockerfile and pushes it to GitHub Container Registry (ghcr.io).

</domain>

<decisions>
## Implementation Decisions

### Trigger Events
- Build on push to main branch (build + push image)
- Build on pull requests (build only, no push — serves as a CI check)

### Image Tagging
- Tag with short git SHA (e.g., ghcr.io/owner/fathom:abc1234)
- Update `:latest` tag on main branch pushes only
- PR builds validate but do not push tags

### Build Platforms
- Single platform: linux/amd64 only
- No multi-arch build needed

### Claude's Discretion
- Workflow file naming and structure
- Cache strategy for Docker layer caching
- Permissions and GHCR authentication approach

</decisions>

<specifics>
## Specific Ideas

- Existing Dockerfile is multi-stage (builder + runtime) at repo root
- Project uses `uv` for dependency management with `uv.lock`
- Repository name for GHCR should derive from GitHub repo context variables

</specifics>
