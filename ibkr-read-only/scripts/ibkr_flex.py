#!/usr/bin/env python3
"""Fetch and summarize IBKR Flex reports without exposing credentials."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


BASE_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
USER_AGENT = "ibkr-read-only/1.0 Python"
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = SKILL_DIR / ".env.ibkr.local"
REQUIRED_KEYS = ("IBKR_FLEX_TOKEN", "IBKR_FLEX_ACTIVITY_QUERY_ID")
TRANSIENT_CODES = {"1001", "1018", "1019", "1020", "1021"}
REDACT_ATTRIBUTE_FRAGMENTS = ("account", "acctid", "clientid")


class FlexError(RuntimeError):
    pass


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FlexError("Env file does not exist or is not a regular file.")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise FlexError(f"Env file permissions are {oct(mode)}; set them to 0o600.")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] in "'\"" and value[-1] == value[0]:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def load_config(env_file: Path | None) -> tuple[dict[str, str], str]:
    selected_env_file = env_file
    if selected_env_file is None and DEFAULT_ENV_FILE.is_file():
        selected_env_file = DEFAULT_ENV_FILE

    values = parse_env_file(selected_env_file) if selected_env_file else {}
    if selected_env_file == DEFAULT_ENV_FILE:
        source = "default-env-file"
    elif selected_env_file:
        source = "env-file"
    else:
        source = "process-environment"
    for key in (*REQUIRED_KEYS, "IBKR_FLEX_VERSION"):
        if os.environ.get(key):
            values[key] = os.environ[key].strip()

    token = values.get("IBKR_FLEX_TOKEN", "")
    query_id = values.get("IBKR_FLEX_ACTIVITY_QUERY_ID", "")
    version = values.get("IBKR_FLEX_VERSION", "3")
    if selected_env_file is None and (not token or not query_id):
        raise FlexError(
            f"Default env file was not found at {DEFAULT_ENV_FILE}. "
            "Provide --env-file only when credentials are stored elsewhere."
        )
    if not token.isdigit() or len(token) < 10:
        raise FlexError("IBKR_FLEX_TOKEN is missing or is not a numeric Flex token.")
    if not query_id.isdigit():
        raise FlexError("IBKR_FLEX_ACTIVITY_QUERY_ID is missing or nonnumeric.")
    if version != "3":
        raise FlexError("IBKR_FLEX_VERSION must be 3.")
    return {"token": token, "query_id": query_id, "version": version}, source


def request(path: str, params: dict[str, str]) -> bytes:
    url = f"{BASE_URL}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise FlexError(f"IBKR returned HTTP {exc.code}.") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", "network error")
        raise FlexError(f"Could not reach IBKR: {reason}") from None


def response_fields(root: ET.Element) -> dict[str, str]:
    return {child.tag: (child.text or "") for child in root}


def fetch_report(config: dict[str, str]) -> ET.Element:
    first_payload = request(
        "SendRequest",
        {"t": config["token"], "q": config["query_id"], "v": config["version"]},
    )
    try:
        first_root = ET.fromstring(first_payload)
    except ET.ParseError:
        raise FlexError("IBKR returned a non-XML generation response.") from None
    first = response_fields(first_root)
    if first.get("Status") != "Success":
        raise FlexError(
            f"IBKR rejected the report request: {first.get('ErrorCode', '?')} — "
            f"{first.get('ErrorMessage', 'unknown error')}"
        )
    reference = first.get("ReferenceCode", "")
    if not reference.isdigit():
        raise FlexError("IBKR did not return a valid report reference code.")

    last_error = "Report was not ready before polling ended."
    for wait_seconds in (2, 4, 8, 12, 20):
        time.sleep(wait_seconds)
        payload = request(
            "GetStatement",
            {"t": config["token"], "q": reference, "v": config["version"]},
        )
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            raise FlexError("IBKR returned a non-XML report; configure the query format as XML.") from None
        if root.tag != "FlexStatementResponse":
            return root
        fields = response_fields(root)
        code = fields.get("ErrorCode", "")
        last_error = f"{code or '?'} — {fields.get('ErrorMessage', 'unknown error')}"
        if code not in TRANSIENT_CODES:
            raise FlexError(f"IBKR report retrieval failed: {last_error}")
    raise FlexError(last_error)


def first_attr(root: ET.Element, names: tuple[str, ...]) -> str | None:
    for elem in root.iter():
        for name in names:
            if elem.attrib.get(name):
                return elem.attrib[name]
    return None


def summarize(root: ET.Element, include_positions: bool) -> dict[str, object]:
    report_dates = sorted(
        {
            value
            for elem in root.iter()
            for key, value in elem.attrib.items()
            if key in {"reportDate", "fromDate", "toDate", "date"} and value
        }
    )
    base_currency = first_attr(root, ("baseCurrency",))
    if not base_currency:
        statement = next((elem for elem in root.iter() if elem.tag == "FlexStatement"), None)
        base_currency = statement.attrib.get("currency") if statement is not None else None

    nav: list[dict[str, str]] = []
    nav_fields = ("endingValue", "netLiquidation", "netLiquidationValue", "total")
    nav_tags = {"ChangeInNAV", "NetAssetValue", "NetAssetValueInBase", "EquitySummaryByReportDateInBase"}
    seen_nav: set[tuple[str, str, str]] = set()
    for elem in root.iter():
        if elem.tag not in nav_tags:
            continue
        for field in nav_fields:
            value = elem.attrib.get(field)
            if not value:
                continue
            key = (elem.tag, field, value)
            if key in seen_nav:
                continue
            seen_nav.add(key)
            item = {"section": elem.tag, "field": field, "value": value}
            for context in ("currency", "reportDate"):
                if elem.attrib.get(context):
                    item[context] = elem.attrib[context]
            nav.append(item)

    cash: list[dict[str, str]] = []
    for elem in root.iter():
        if elem.tag != "CashReportCurrency" or not elem.attrib.get("endingCash"):
            continue
        cash.append(
            {
                "currency": elem.attrib.get("currency", "unknown"),
                "ending_cash": elem.attrib["endingCash"],
            }
        )

    if not base_currency and nav:
        base_currency = nav[-1].get("currency")

    summary: dict[str, object] = {
        "status": "success",
        "report_type": root.tag,
        "report_dates": report_dates,
        "base_currency": base_currency,
        "nav_candidates": nav,
        "cash": cash,
    }

    if include_positions:
        positions: list[dict[str, str]] = []
        allowed = (
            "symbol",
            "description",
            "assetCategory",
            "currency",
            "position",
            "markPrice",
            "positionValue",
            "fxRateToBase",
            "percentOfNAV",
        )
        for elem in root.iter():
            if elem.tag == "OpenPosition":
                positions.append({key: elem.attrib[key] for key in allowed if elem.attrib.get(key)})
        summary["positions"] = positions
    return summary


def redact(root: ET.Element) -> ET.Element:
    redacted = copy.deepcopy(root)
    for elem in redacted.iter():
        for key in list(elem.attrib):
            folded = key.casefold()
            if any(fragment in folded for fragment in REDACT_ATTRIBUTE_FRAGMENTS):
                del elem.attrib[key]
    return redacted


def write_private_xml(root: ET.Element, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            ET.ElementTree(redact(root)).write(handle, encoding="utf-8", xml_declaration=True)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    path.chmod(0o600)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="validate configuration without contacting IBKR")
    inspect_parser.add_argument("--env-file", type=Path, help="override the adjacent .env.ibkr.local")

    fetch_parser = subparsers.add_parser("fetch", help="fetch and summarize a Flex report")
    fetch_parser.add_argument("--env-file", type=Path, help="override the adjacent .env.ibkr.local")
    fetch_parser.add_argument("--include-positions", action="store_true")
    fetch_parser.add_argument("--save-redacted-xml", type=Path)

    parse_parser = subparsers.add_parser("parse", help="summarize an existing XML report")
    parse_parser.add_argument("xml_file", type=Path)
    parse_parser.add_argument("--include-positions", action="store_true")
    parse_parser.add_argument("--save-redacted-xml", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "inspect":
            _, source = load_config(args.env_file)
            print(json.dumps({"status": "ready", "source": source, "credential_shapes": "valid"}))
            return 0

        if args.command == "fetch":
            config, _ = load_config(args.env_file)
            root = fetch_report(config)
        else:
            if not args.xml_file.is_file():
                raise FlexError("XML report file does not exist.")
            try:
                root = ET.parse(args.xml_file).getroot()
            except ET.ParseError:
                raise FlexError("Report file is not valid XML.") from None

        if args.save_redacted_xml:
            write_private_xml(root, args.save_redacted_xml)
        print(json.dumps(summarize(root, args.include_positions), indent=2, sort_keys=True))
        return 0
    except FlexError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
