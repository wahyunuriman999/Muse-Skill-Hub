# Finances (Plaid) (`plaid`)

> Use to connect Plaid and read linked financial accounts: metadata, balances, transactions, recurring transactions, liabilities, and investments.

## What is this?

The `plaid` skill is one of Muse's capabilities.

Official description: Use to connect Plaid and read linked financial accounts: metadata, balances, transactions, recurring transactions, liabilities, and investments.

## When to use?

When the user's request matches: Use to connect Plaid and read linked financial accounts: metadata, balances, transactions, recurring

## General pattern

- **Read first, write with approval**: read operations first for verification, write operations always need confirmation.
- **Verify before claiming**: check connection status and access before saying you can.
- **Don't guess**: if live info is needed, check live sources, not memory.

## Example adaptation pattern for other LLMs

```
Skill: plaid
Purpose: Use to connect Plaid and read linked financial accounts: metadata, balances, transactions, recurring transactions, liabi
Input: clear user need + structured parameters
Output: verified result + its source
Rules: separate read vs write, require approval for writes
```

---
*Sanitized from Muse's internal docs — only public patterns shared.*