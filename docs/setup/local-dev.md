# Local development

## Prerequisites

Install the [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0). The exact version is
pinned in `global.json` (`rollForward: latestPatch` — allows a newer *patch* of the same `10.0.3xx`
band, but not a different feature band or major version), so a mismatched SDK fails the build
loudly instead of silently compiling with whatever's installed. Check what you have against what
the repo expects:

```bash
dotnet --version        # installed SDK
cat global.json          # SDK this repo requires
```

## Run the app

```bash
dotnet run --project src/TrAIning.Web
```

Serves the app locally over HTTPS on a dynamic port (see the console output for the exact URL —
also configurable in `src/TrAIning.Web/Properties/launchSettings.json`).

## Run via Docker

Build from the **repo root** (not the project folder — the Dockerfile expects that build context
so it can `COPY` from `src/TrAIning.Web/`):

```bash
docker build -f src/TrAIning.Web/Dockerfile -t training-web:local .
docker run -p 8080:8080 training-web:local
```

Open <http://localhost:8080>. Unlike `dotnet run`, this serves plain HTTP on a fixed port — the
container never terminates TLS itself; that's Azure Container Apps' ingress's job once deployed
(see the Dockerfile's comments). A few log warnings only show up this way, never during local
`dotnet run`, and are expected:
- `Failed to determine the https port for redirect` — only when hitting the container directly
  with no reverse proxy in front of it (i.e. exactly what you're doing here). In the real
  deployment, Container Apps' ingress adds an `X-Forwarded-Proto` header that tells the app the
  original request was HTTPS, and the warning doesn't fire.
- `Storing keys in a directory '/root/.aspnet/DataProtection-Keys' that may not be persisted...`
  — expected for a single container with no persistent volume; keys regenerate on restart. Not a
  problem yet (nothing depends on stable keys across restarts), but will need a real fix (e.g. a
  shared key ring in Blob/Key Vault) before running multiple replicas or relying on antiforgery
  tokens surviving a restart.

> The rest of this page is a placeholder — fill in during later phases as the solution takes shape.

Will cover:
- Local secrets (user-secrets / a local `.env`) — **never** the global shell environment, so that
  `ANTHROPIC_API_KEY` doesn't leak in and silently switch Claude Code to token billing
- Local Azure SQL alternative for dev (SQL Server container / SQLite) if used
- How to run the FIT inspection tools in `tools/`
