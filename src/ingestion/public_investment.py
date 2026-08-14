"""Provider-neutral clients and normalizers for high-feasibility public sources.

The fetch functions are deliberately small and dependency-light. Unit tests call
the normalizers with recorded payloads; no test in this module needs network
access. Every returned record keeps source identity and timing visible so the
records can be placed behind the repository's provenance checks.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Callable, Iterable, Mapping
from typing import Any

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
ALFRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
TREASURY_AUCTIONS_URL = (
    "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
    "v2/accounting/od/auctions_query"
)
NYFED_SOFR_URL = "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json"
CFTC_LEGACY_ALL_URL = "https://publicreporting.cftc.gov/resource/srt6-5q2f.json"
FRENCH_FACTORS_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_CSV.zip"
)


class PublicDataError(RuntimeError):
    """Raised when a public provider response cannot be normalized safely."""


def fetch_json(
    url: str,
    *,
    headers: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Fetch a JSON document using an injectable opener for deterministic tests."""
    request = urllib.request.Request(url, headers=dict(headers or {}))
    try:
        with opener(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise PublicDataError(f"public provider request failed: {url}") from exc
    if not isinstance(payload, (dict, list)):
        raise PublicDataError(f"provider returned a non-JSON object: {url}")
    return payload


def sec_headers(user_agent: str | None = None) -> dict[str, str]:
    """Return the descriptive User-Agent required for SEC public access."""
    value = user_agent or os.getenv("SEC_USER_AGENT")
    if not value or "@" not in value:
        raise PublicDataError(
            "SEC_USER_AGENT must identify the application and a contact email"
        )
    return {"User-Agent": value, "Accept-Encoding": "gzip, deflate"}


def normalize_sec_company_facts(
    payload: Mapping[str, Any], *, cik: str
) -> list[dict[str, Any]]:
    """Flatten SEC Company Facts units into source-attributed records."""
    facts = payload.get("facts")
    if not isinstance(facts, Mapping):
        raise PublicDataError("SEC Company Facts payload has no facts object")
    records: list[dict[str, Any]] = []
    normalized_cik = str(cik).zfill(10)
    for taxonomy, concepts in facts.items():
        if not isinstance(concepts, Mapping):
            continue
        for concept, definition in concepts.items():
            units = (
                definition.get("units", {}) if isinstance(definition, Mapping) else {}
            )
            if not isinstance(units, Mapping):
                continue
            for unit, observations in units.items():
                if not isinstance(observations, list):
                    continue
                for item in observations:
                    if not isinstance(item, Mapping) or "val" not in item:
                        continue
                    records.append(
                        {
                            "source": "sec-edgar-companyfacts",
                            "cik": normalized_cik,
                            "taxonomy": str(taxonomy),
                            "concept": str(concept),
                            "unit": str(unit),
                            "value": item["val"],
                            "observation_date": item.get("end"),
                            "filing_date": item.get("filed"),
                            "form": item.get("form"),
                            "accession_number": item.get("accn"),
                            "frame": item.get("frame"),
                            "source_url": SEC_COMPANY_FACTS_URL.format(
                                cik=normalized_cik
                            ),
                        }
                    )
    return records


def fetch_sec_company_facts(
    cik: str,
    *,
    user_agent: str | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Fetch public SEC XBRL facts for one issuer."""
    normalized_cik = str(cik).zfill(10)
    payload = fetch_json(
        SEC_COMPANY_FACTS_URL.format(cik=normalized_cik),
        headers=sec_headers(user_agent),
        opener=opener,
    )
    if not isinstance(payload, Mapping):
        raise PublicDataError("SEC Company Facts response must be an object")
    return normalize_sec_company_facts(payload, cik=normalized_cik)


def normalize_sec_submissions(
    payload: Mapping[str, Any], *, cik: str
) -> list[dict[str, Any]]:
    """Normalize the recent-filing arrays from an SEC submissions response."""
    filings = payload.get("filings", {})
    recent = filings.get("recent", filings) if isinstance(filings, Mapping) else {}
    if not isinstance(recent, Mapping):
        raise PublicDataError("SEC submissions payload has no filings object")
    arrays = {key: value for key, value in recent.items() if isinstance(value, list)}
    required = {
        "accessionNumber",
        "filingDate",
        "form",
        "reportDate",
        "primaryDocument",
    }
    if not required.issubset(arrays):
        raise PublicDataError("SEC submissions payload is missing filing arrays")
    length = len(arrays["accessionNumber"])
    records = []
    for index in range(length):
        accession = arrays["accessionNumber"][index]
        accession_path = str(accession).replace("-", "")
        records.append(
            {
                "source": "sec-edgar-submissions",
                "cik": str(cik).zfill(10),
                "accession_number": accession,
                "form": arrays["form"][index],
                "filing_date": arrays["filingDate"][index],
                "period_of_report": arrays["reportDate"][index],
                "primary_document": arrays["primaryDocument"][index],
                "source_url": (
                    f"https://www.sec.gov/Archives/edgar/data/{int(str(cik))}/"
                    f"{accession_path}/{arrays['primaryDocument'][index]}"
                ),
            }
        )
    return records


def fetch_sec_submissions(
    cik: str,
    *,
    user_agent: str | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Fetch public recent filing metadata for one issuer."""
    normalized_cik = str(cik).zfill(10)
    payload = fetch_json(
        SEC_SUBMISSIONS_URL.format(cik=normalized_cik),
        headers=sec_headers(user_agent),
        opener=opener,
    )
    if not isinstance(payload, Mapping):
        raise PublicDataError("SEC submissions response must be an object")
    return normalize_sec_submissions(payload, cik=normalized_cik)


def normalize_alfred_observations(
    payload: Mapping[str, Any], *, series_id: str
) -> list[dict[str, Any]]:
    """Normalize ALFRED observations while retaining vintage timing."""
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise PublicDataError("ALFRED payload has no observations list")
    default_vintage = payload.get("realtime_start")
    records = []
    for item in observations:
        if not isinstance(item, Mapping) or item.get("value") in (None, "."):
            continue
        vintage = item.get("realtime_start") or default_vintage
        if not vintage:
            raise PublicDataError("ALFRED observation has no vintage/release date")
        records.append(
            {
                "source": "alfred",
                "series_id": series_id,
                "observation_date": item.get("date"),
                "release_date": vintage,
                "vintage": vintage,
                "value": float(item["value"]),
                "unit": "provider-defined",
                "source_url": ALFRED_OBSERVATIONS_URL,
            }
        )
    return records


def fetch_alfred_series(
    series_id: str,
    *,
    api_key: str | None = None,
    realtime_start: str | None = None,
    realtime_end: str | None = None,
    vintage_dates: str | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Fetch an ALFRED series for an explicit real-time period or vintage."""
    key = api_key or os.getenv("FRED_API_KEY")
    if not key:
        raise PublicDataError("FRED_API_KEY is required for ALFRED")
    params = {"series_id": series_id, "api_key": key, "file_type": "json"}
    for name, value in {
        "realtime_start": realtime_start,
        "realtime_end": realtime_end,
        "vintage_dates": vintage_dates,
    }.items():
        if value:
            params[name] = value
    url = f"{ALFRED_OBSERVATIONS_URL}?{urllib.parse.urlencode(params)}"
    payload = fetch_json(url, opener=opener)
    if not isinstance(payload, Mapping):
        raise PublicDataError("ALFRED response must be an object")
    return normalize_alfred_observations(payload, series_id=series_id)


def _first(record: Mapping[str, Any], *names: str) -> Any:
    lowered = {str(key).lower(): value for key, value in record.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def normalize_treasury_auctions(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalize Treasury Fiscal Data auction rows without dropping raw terms."""
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise PublicDataError("Treasury payload has no data list")
    records = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        record = dict(row)
        record.update(
            {
                "source": "treasury-fiscal-data-auctions",
                "source_url": TREASURY_AUCTIONS_URL,
                "record_date": _first(row, "record_date"),
                "auction_date": _first(row, "auction_date"),
                "issue_date": _first(row, "issue_date"),
                "maturity_date": _first(row, "maturity_date"),
                "security_type": _first(row, "security_type"),
                "security_term": _first(row, "security_term"),
                "cusip": _first(row, "cusip"),
            }
        )
        records.append(record)
    return records


def fetch_treasury_auctions(
    *,
    fields: str | None = None,
    filter_expression: str | None = None,
    page_size: int = 100,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Fetch a bounded page of Treasury auction records."""
    params: dict[str, str | int] = {"page[size]": page_size}
    if fields:
        params["fields"] = fields
    if filter_expression:
        params["filter"] = filter_expression
    url = f"{TREASURY_AUCTIONS_URL}?{urllib.parse.urlencode(params)}"
    payload = fetch_json(url, opener=opener)
    if not isinstance(payload, Mapping):
        raise PublicDataError("Treasury response must be an object")
    return normalize_treasury_auctions(payload)


def normalize_sofr(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Normalize New York Fed SOFR search results."""
    rows = payload.get("ref rates") or payload.get("refRates") or payload.get("data")
    if not isinstance(rows, list):
        raise PublicDataError("NY Fed response has no rate list")
    records = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        observation_date = _first(row, "effectiveDate", "effective_date", "date")
        value = _first(row, "percentPercentile", "percentile", "rate")
        if observation_date is None or value is None:
            continue
        records.append(
            {
                "source": "new-york-fed-sofr",
                "series_id": "SOFR",
                "observation_date": observation_date,
                "release_date": observation_date,
                "vintage": observation_date,
                "value": float(value),
                "unit": "percent",
                "source_url": NYFED_SOFR_URL,
                "raw": dict(row),
            }
        )
    return records


def fetch_sofr(
    *,
    start_date: str,
    end_date: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Fetch a bounded New York Fed SOFR date range."""
    params = {"startDate": start_date, "endDate": end_date, "type": "rate"}
    url = f"{NYFED_SOFR_URL}?{urllib.parse.urlencode(params)}"
    payload = fetch_json(url, opener=opener)
    if not isinstance(payload, Mapping):
        raise PublicDataError("NY Fed response must be an object")
    return normalize_sofr(payload)


def normalize_cftc_positioning(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize CFTC COT rows while preserving the provider's classification fields."""
    records = []
    for row in rows:
        report_date = _first(
            row, "report_date_as_yyyy_mm_dd", "report_date_as_mm_dd_yyyy"
        )
        if report_date is None:
            continue
        record = dict(row)
        record.update(
            {
                "source": "cftc-commitments-of-traders",
                "series_id": _first(
                    row, "cftc_contract_market_code", "contract_market_name"
                ),
                "observation_date": report_date,
                "source_url": CFTC_LEGACY_ALL_URL,
            }
        )
        records.append(record)
    return records


def fetch_cftc_positioning(
    *,
    query: str | None = None,
    limit: int = 100,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Fetch a bounded CFTC public-reporting page."""
    params = {"$limit": str(limit)}
    if query:
        params["$query"] = query
    url = f"{CFTC_LEGACY_ALL_URL}?{urllib.parse.urlencode(params)}"
    payload = fetch_json(url, opener=opener)
    if not isinstance(payload, list):
        raise PublicDataError("CFTC response must be a list")
    return normalize_cftc_positioning(payload)


def normalize_french_factors(text: str) -> list[dict[str, Any]]:
    """Parse the monthly Fama/French research-factor CSV text."""
    lines = [line.strip() for line in text.splitlines()]
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith("Mkt-RF")),
        None,
    )
    if header_index is None:
        raise PublicDataError("French factor file has no monthly factor header")
    reader = csv.reader(lines[header_index:])
    header = ["observation_date", *next(reader)]
    records = []
    for row in reader:
        if not row or not re.fullmatch(r"\d{6}", row[0].strip()):
            if records:
                break
            continue
        for name, value in zip(header[1:], row[1:], strict=False):
            if value.strip():
                records.append(
                    {
                        "source": "kenneth-french-data-library",
                        "series_id": name.strip(),
                        "observation_date": f"{row[0][:4]}-{row[0][4:]}-01",
                        "value": float(value) / 100.0,
                        "unit": "decimal_return",
                        "source_url": FRENCH_FACTORS_URL,
                    }
                )
    return records


def fetch_french_factors(
    *, opener: Callable[..., Any] = urllib.request.urlopen
) -> list[dict[str, Any]]:
    """Fetch the public monthly Fama/French research-factor archive."""
    request = urllib.request.Request(FRENCH_FACTORS_URL)
    try:
        with opener(request, timeout=30) as response:
            archive = response.read()
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            csv_name = next(
                name for name in bundle.namelist() if name.lower().endswith(".csv")
            )
            text = bundle.read(csv_name).decode("latin-1")
    except (OSError, StopIteration, zipfile.BadZipFile) as exc:
        raise PublicDataError("Kenneth French archive could not be read") from exc
    return normalize_french_factors(text)
