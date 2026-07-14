# ADR-0009: Plan-first, chat optional

**Status:** Accepted
**Date:** 2026-07

## Context

An earlier framing described the system as "chat-first" — a coach you talk to. On reflection that
was wrong, and the distinction has real architectural consequences.

## Decision

The system is **plan-first**. The agent plans autonomously from data alone: history, metrics,
wellness, goals. If the user never writes a single message, the app still ingests, measures,
interprets, plans, and fills the calendar.

Chat is an **optional steering layer** on top of an autonomous system. When the user says something
("knee hurts", "only Tuesday this week"), the plan adapts.

The primary UI surface is the plan and the metrics. Chat is one tap away, not the front door.

## Consequences

- **Build order matters: the autonomous planner comes before the chat box.** If the agent cannot
  produce a sensible week from data alone, chat becomes a way to paper over a weak planner. A coach
  you *must* negotiate with every week has failed; a coach you *can* negotiate with is good.
- Notifications follow the same philosophy. Exactly four triggers — the Sunday proposal, a single
  nudge after five silent days, a genuine question, and an optional reaction to a notable session.
  **Silence is the default.** A coach that pings daily gets muted, and a muted coach is useless.
- Cost scales with conversation, not with training. Baseline running cost is low and predictable;
  chat is what varies.
