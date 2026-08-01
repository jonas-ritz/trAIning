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

> The rest of this page is a placeholder — fill in during later phases as the solution takes shape.

Will cover:
- Local secrets (user-secrets / a local `.env`) — **never** the global shell environment, so that
  `ANTHROPIC_API_KEY` doesn't leak in and silently switch Claude Code to token billing
- Local Azure SQL alternative for dev (SQL Server container / SQLite) if used
- How to run the FIT inspection tools in `tools/`
