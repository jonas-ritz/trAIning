# Azure subscription setup

Practical steps for creating and checking the Azure subscription this project deploys into.

## The one rule that matters

**Claude in Microsoft Foundry needs a pay-as-you-go subscription** (real payment method) or a
commercial/enterprise agreement. Trial, student, and credit-only subscriptions are rejected.

Foundry isn't used until Phase 5. Phases 1–4 run on free-tier resources and cost nothing on any
subscription type. So the subscription must be pay-as-you-go **by Phase 5**, not necessarily today.

## Creating the subscription

1. Go to <https://azure.microsoft.com> and sign in with a Microsoft account (create one if needed).
2. Start the signup. Take whatever it offers — free credit or pay-as-you-go both work for Phases 1–4.
3. A payment method is required either way (even trials ask for a card for identity verification;
   they just don't charge it during the trial).

## Checking what you've got

Azure Portal → search **"Subscriptions"** → click your subscription → **Overview**. The type is shown there.

| What it says | Foundry-ready? | Action |
|---|---|---|
| Pay-As-You-Go | Yes | Nothing to do |
| Microsoft Customer Agreement / EA | Yes | Nothing to do |
| Free Trial / Azure Pass | No | Upgrade before Phase 5 |
| Azure for Students | No | Upgrade before Phase 5 |

## Upgrading a trial to pay-as-you-go

Azure Portal → your subscription → look for **"Upgrade"** in the toolbar or overview.
Adding a payment method converts it; any remaining trial credit carries over.

Do this **before** starting Phase 5. It's a two-minute change, but discovering it late means the
agent won't deploy and it isn't obvious why.

## Gotchas

- **Multiple subscriptions.** If you ever had a student or trial account, you may have more than one.
  When you write Bicep later, target the *right* one — deploying into the wrong subscription is a
  common early mistake and Foundry will reject a non-PAYG one with an unhelpful error.
- **Trial expiry.** An expired trial disables its resources. If the running system lives on a trial
  that lapses, it goes down — not just new deploys. Another reason to be on PAYG before anything runs
  continuously.
- **Region.** Foundry model deployments need a supported region. Not a subscription setting, but keep
  it in mind when you provision Foundry in Phase 5.
