---
name: "wallet"
title: "Wallet"
description: Coordinate payments: check wallet connection state, use saved payment methods and addresses through secure provider pages, and run the required purchase review and approval flow.
version: "1.0.0"
license: "AGPL-3.0-only"
compatibility: "Any LLM with tool/function calling"
---

# Wallet

Coordinate payments: check wallet connection state, use saved payment methods and addresses through secure provider pages, and run the required purchase review and approval flow.

## When to Use This Skill

Activate this skill when:
- the user wants to pay, check out, or buy something
- questions about saved cards, payment methods, or shipping addresses
- setting up or disconnecting a payment provider

Do NOT activate for unrelated requests. If unsure, ask the user for clarification.

## Prerequisites

- The wallet provider's connection state (Shop Pay, Stripe Link, etc.)
- The shopping/booking skill that determines the transaction's execution route

## Capabilities Required

- [ ] Function/tool calling (to invoke actions)
- [ ] Secure UI surfaces (for credentials, payments, approvals where relevant)
- [ ] State inspection (to check connection/permission status before acting)

Check which of these your host LLM supports. Adapt the instructions below to your available tools.

## Instructions

### Step 1: Check the wallet state
- Inspect connection state first. If setup is missing, share the provider's secure setup flow — don't improvise card handling.

### Step 2: Never touch raw card data
- Card numbers, expiry, and CVV are entered only on the provider's secure pages. Do not ask for, display, or store them.

### Step 3: Purchase review
- Every purchase goes through the transaction's required final review and approval: item, total price including fees/taxes, delivery terms, and payment method — all shown before approval.

### Step 4: After approval
- Execute through the approved route (browser checkout or direct tool). Report the confirmation with order/booking identifiers copied exactly.

## Input Pattern

```yaml
# Example input structure - adapt to your LLM's function calling format
skill: "wallet"
parameters:
  query: "user's request in structured form"
```

## Output Pattern

```yaml
# What to return to the user
success: true/false
result: "human-readable summary"
details:
  source: "where the data came from"
  checked_at: "ISO-8601 timestamp"
```

## Safety Rules

1. No raw card details in chat — ever
2. Purchases need the full review + explicit approval; a general 'buy it' covers only that exact item/price
3. Copy order/booking identifiers exactly; never invent them

## Example

**User**: "Buy the headphones we found"

**LLM**:
1. Shows the final review: item, total with tax/shipping, delivery estimate, payment method. 2. On explicit approval, completes checkout. 3. Returns the order confirmation code.

---

*Platform capability pattern — documented so any LLM agent can implement an equivalent.*


## Actions

<!-- Auto-generated from the driver's ActionDef contracts
     (v2.1 doc-sync). Kept in sync by `skillhub validate`. -->

- **add_payment_method** — Save a payment-method label record (needs confirm=true).  
  Risk: `financial` · parameters: label, brand, last4 · required: label
- **get_state** — Check wallet connection state.  
  Risk: `read` · parameters: none · required: none
- **list_payment_methods** — List saved payment-method records.  
  Risk: `read` · parameters: none · required: none
