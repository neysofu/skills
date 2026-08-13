---
name: ibkr-read-only
description: Read Interactive Brokers account data through the Flex Web Service reporting-only capability boundary.
disable-model-invocation: true
---

# IBKR Read Only

Use the bundled `scripts/ibkr_flex.py` client. It calls only Flex Web Service `SendRequest` and `GetStatement`; this boundary can generate and retrieve configured reports but cannot place orders, transfer funds, or change brokerage settings.

## Capability boundary

- Keep all IBKR access inside the bundled client. A request for live quotes, intraday state, TWS, Client Portal API, or order management crosses this boundary; explain that it requires a different integration.
- Treat the Flex token, Query ID, account identifiers, and unredacted reports as secrets. Keep them out of prompts, command arguments, logs, tracked files, and final responses.
- Describe Flex data as a reporting snapshot. State its report date; do not call it live unless the report itself establishes that.

## Credential setup

The client always checks `.env.ibkr.local` beside this `SKILL.md` first. Before the first authenticated run, or whenever credentials are missing, invalid, exposed, or being rotated, read [INSTALL.md](INSTALL.md) completely and follow it. Do not load the install guide for routine successful fetches.

## Operating loop

1. Locate the skill directory containing this file. Run `inspect` without asking the user for an env-file path:

```bash
python3 <skill-dir>/scripts/ibkr_flex.py inspect
```

Proceed when the client reports valid credential shapes and secure file permissions. Only if the adjacent `.env.ibkr.local` is absent, ask whether the user has an env file elsewhere; use its path with `--env-file`. For other credential failures, follow [INSTALL.md](INSTALL.md). Never ask the user to paste credentials into chat.

2. Fetch the aggregate snapshot:

```bash
python3 <skill-dir>/scripts/ibkr_flex.py fetch
```

If network sandboxing blocks IBKR, request approval for this exact Python command and explain that it reaches only the reporting service.

3. For holdings analysis, add `--include-positions`. For other report sections or custom parsing, save a redacted private artifact inside the active workspace:

```bash
python3 <skill-dir>/scripts/ibkr_flex.py fetch \
  --include-positions \
  --save-redacted-xml <workspace-private-path>.xml
```

The client removes account-identifying attributes and writes the artifact with mode `600`. Read only the minimum report sections needed for the request.

4. Report the requested values with currency and report date. Distinguish NAV, cash, position market value, and futures notional. Flag negative cash as a debit balance rather than folding it into a vague “balance.”

The run is complete when the report was retrieved, its date and freshness were stated, every requested metric was answered, and no token, Query ID, raw account identifier, or unredacted report was exposed.

## Failure handling

- `Token has expired`, `Token is invalid`, `Query is invalid`, or `IP restriction`: read [INSTALL.md](INSTALL.md) and guide the user through the corresponding repair.
- Missing NAV or cash: the connection can still be valid; use the query-configuration section of [INSTALL.md](INSTALL.md).
- Non-XML payload: ask the user to configure the Flex Query format as XML.
- Report still generating: let the bundled polling loop finish; respect IBKR pacing limits rather than repeatedly rerunning it.
