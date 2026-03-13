---
phase: quick
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - .github/workflows/build-container.yml
autonomous: true
requirements: [QUICK-1]
must_haves:
  truths:
    - "Push to main builds and pushes image to ghcr.io with SHA tag and :latest"
    - "Pull request builds image but does not push"
    - "Image is tagged with short git SHA on main pushes"
  artifacts:
    - path: ".github/workflows/build-container.yml"
      provides: "GitHub Actions workflow for container build and GHCR push"
  key_links:
    - from: ".github/workflows/build-container.yml"
      to: "Dockerfile"
      via: "docker/build-push-action context"
      pattern: "context: \\."
---

<objective>
Create a GitHub Actions workflow that builds the Docker container from the existing multi-stage Dockerfile and pushes it to GitHub Container Registry (ghcr.io).

Purpose: Enable automated container builds on every push to main and CI validation on PRs.
Output: `.github/workflows/build-container.yml`
</objective>

<execution_context>
@/home/kris/.claude/get-shit-done/workflows/execute-plan.md
@/home/kris/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@Dockerfile
@.planning/quick/1-create-github-actions-to-build-container/1-CONTEXT.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create GitHub Actions container build workflow</name>
  <files>.github/workflows/build-container.yml</files>
  <action>
Create `.github/workflows/build-container.yml` with the following configuration:

**Triggers:**
- `push` to `main` branch
- `pull_request` targeting `main` branch

**Permissions:**
- `contents: read`
- `packages: write`

**Job: build-and-push** (runs on `ubuntu-latest`)

Steps:
1. `actions/checkout@v4`
2. `docker/setup-buildx-action@v3` — enables BuildKit and layer caching
3. `docker/login-to-ghcr` — use `docker/login-action@v3` with:
   - `registry: ghcr.io`
   - `username: ${{ github.actor }}`
   - `password: ${{ secrets.GITHUB_TOKEN }}`
   - Condition: only run on push to main (`if: github.event_name == 'push'`)
4. `docker/metadata-action@v5` — generate tags:
   - `type=sha,format=short` (short git SHA tag, e.g. `abc1234`)
   - `type=raw,value=latest,enable=${{ github.event_name == 'push' }}` (`:latest` only on main push)
   - images: `ghcr.io/${{ github.repository }}`
5. `docker/build-push-action@v3` with:
   - `context: .`
   - `push: ${{ github.event_name == 'push' }}` (push only on main, not on PR)
   - `tags: ${{ steps.meta.outputs.tags }}`
   - `labels: ${{ steps.meta.outputs.labels }}`
   - `platforms: linux/amd64`
   - `cache-from: type=gha`
   - `cache-to: type=gha,mode=max`

Use GitHub Actions cache (`type=gha`) for Docker layer caching — this uses the GHA cache backend built into BuildKit, no extra config needed.

Name the steps clearly: "Checkout", "Set up Docker Buildx", "Log in to GHCR", "Extract metadata", "Build and push".
  </action>
  <verify>
    <automated>cd /home/kris/git/fathom && cat .github/workflows/build-container.yml | head -80 && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/build-container.yml')); print('YAML valid')"</automated>
  </verify>
  <done>
    - `.github/workflows/build-container.yml` exists and is valid YAML
    - Triggers on push to main and pull_request to main
    - Pushes to ghcr.io only on main push (not on PR)
    - Tags with short SHA and :latest (latest only on push)
    - Uses GHA cache for Docker layer caching
    - Single platform: linux/amd64
  </done>
</task>

</tasks>

<verification>
- Workflow file parses as valid YAML
- Workflow uses correct GHCR registry URL pattern (`ghcr.io/${{ github.repository }}`)
- Push conditional is correct (`github.event_name == 'push'`)
- Login step is conditional on push events only
- Cache strategy uses `type=gha`
</verification>

<success_criteria>
A single-file GitHub Actions workflow that will build the container on every PR (validation only) and build+push to GHCR on every merge to main, tagged with short SHA and :latest.
</success_criteria>

<output>
After completion, create `.planning/quick/1-create-github-actions-to-build-container/1-SUMMARY.md`
</output>
