# Credential setup

Read this guide completely before creating, replacing, or repairing the skill's IBKR credentials.

Flex Web Service is a reporting interface: its token can generate and retrieve saved Flex Query reports, not place trades. The reports may expose sensitive account data, including data for linked accounts selected by the query, so protect the token and Query ID as secrets.

## 1. Create the Activity Flex Query

1. Sign in to IBKR Client Portal.
2. Open **Reporting → Flex Queries**.
3. Create an **Activity Flex Query** and deliberately select the intended accounts.
4. For a useful balance and portfolio snapshot, include:
   - `Account Information`
   - `Net Asset Value (NAV) in Base`
   - `Cash Report`
   - `Forex Balances`
   - `Open Positions`
   - `Change in NAV`
5. Set the output format to `XML`. For an end-of-day snapshot, use `Last Business Day`; include currency rates for base-currency reconciliation.
6. Save the query, open its info popover, and copy the numeric **Query ID**.

The query controls what the token can retrieve. Add trades, fees, transfers, or accrual sections only when those reports are needed.

## 2. Enable Flex Web Service and generate a token

1. On **Reporting → Flex Queries**, open **Flex Web Service Configuration**.
2. Enable **Flex Web Service Status** and save.
3. Generate a token with the shortest practical expiry. IBKR supports expiries from six hours to one year.
4. Optionally restrict the token to the public IP that will run the client. A mismatched or changing egress IP produces an `IP restriction` failure.
5. Copy the numeric **Current Token** without placing it in chat, shell arguments, notes, or tracked files.

For linked-account structures, configure the service from the master account and verify that the query includes only the intended accounts.

## 3. Store the credentials locally

Use the hardcoded private file beside `SKILL.md`:

```text
<skill-dir>/.env.ibkr.local
```

From the skill directory, create the file and make it owner-only:

```bash
touch .env.ibkr.local
chmod 600 .env.ibkr.local
```

Open the file in a local editor and add:

```text
IBKR_FLEX_TOKEN=<numeric token>
IBKR_FLEX_ACTIVITY_QUERY_ID=<numeric query ID>
IBKR_FLEX_VERSION=3
```

The skills repository ignores `.env.*`, so this adjacent file remains untracked. The client reads it automatically; do not `source` it or pass either credential as a command-line argument.

Only if this default file is absent and the user already stores the same variables elsewhere, ask for that file's path and pass it with `--env-file <path>`.

## 4. Verify the setup

Validate credentials and permissions without contacting IBKR:

```bash
python3 <skill-dir>/scripts/ibkr_flex.py inspect
```

Expected result:

```json
{"status": "ready", "source": "default-env-file", "credential_shapes": "valid"}
```

Then run one reporting-only fetch:

```bash
python3 <skill-dir>/scripts/ibkr_flex.py fetch
```

Setup is complete when the fetch returns `"status": "success"`, a report date, and the configured NAV or cash fields without printing credentials or account identifiers.

## Rotation and repair

- Exposed, expired, or invalid token: generate a replacement token, update only `IBKR_FLEX_TOKEN`, restore mode `600`, and rerun `inspect` then `fetch`.
- Invalid query: copy the Query ID from the saved Activity Flex Query's info popover and update `IBKR_FLEX_ACTIVITY_QUERY_ID`.
- IP restriction: use the configured public IP or generate a token with the correct restriction.
- Missing NAV, cash, or positions: edit the saved Flex Query sections; the token can remain unchanged.
- Non-XML response: change the query output format to XML.

Official references: [Enable and create an access token](https://www.interactivebrokers.com/docs/web-api/flex-web-service/flex-web-service/client-portal-configuration/enable-and-create-access-token) and [Flex Web Service](https://www.interactivebrokers.com/campus/ibkr-api-page/flex-web-service/).
