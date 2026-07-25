# Local development

> Placeholder — fill in during Phase 1 as the solution takes shape.

Will cover:
- .NET 10 SDK install and version check
- Running the Blazor app locally (`dotnet run --project src/TrainingCoach.Web`)
- Local secrets (user-secrets / a local `.env`) — **never** the global shell environment, so that
  `ANTHROPIC_API_KEY` doesn't leak in and silently switch Claude Code to token billing
- Local Azure SQL alternative for dev (SQL Server container / SQLite) if used
- How to run the FIT inspection tools in `tools/`
