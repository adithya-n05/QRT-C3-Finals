# OpenAPI Intelligence Notes

## Why we use OpenAPI first

The published OpenAPI spec gives us:

- schema-backed payload requirements for `/participate`, `/broadcast`, `/action`,
- error contract shape (`detail`) for malformed submissions,
- defaults and read-only endpoint behavior,
- endpoint list that can be checked against the crawler each run.

## Practical leverage for round 2

1. **Schema guardrail generation**
   - use the spec to generate a minimal field checker and reject invalid payloads locally.
2. **Endpoint drift watch**
   - keep a tiny diff check between local `docs/C3_GAME_PROTOCOL.md` and latest spec for:
   - required parameters,
   - changed defaults,
   - response object fields used by runner acceptance handling.
3. **Payload confidence**
   - validate that `bet_proposition` parsing handles only supported proposition grammar from spec-level behavior,
   - confirm action domains remain integers 0/1/2.
4. **Backtest reconciliation**
   - confirm `/logs` payload contract changed less likely during round 2.
5. **Recovery playbooks**
   - if parser breaks after schema changes, disable non-essential call paths first:
     keep opt-in/action minimal and keep dry-run fallback active.

## Implementation action

- Add a local parser that checks all request payload keys against OpenAPI-defined required/optional fields.
- In replay mode, load `/openapi.json` and validate that strategy logs still emit all fields
  needed for a minimal fallback.
- If any required response field disappears, degrade to phase-based safe mode:
  - no betting,
  - conservative one-action policy,
  - no missing-opponent steering logic until validated.
