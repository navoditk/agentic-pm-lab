from typing import ClassVar

from src.ingestion.public_investment import (
    fetch_json,
    normalize_alfred_csv,
    normalize_alfred_observations,
    normalize_cftc_positioning,
    normalize_french_factors,
    normalize_sec_company_facts,
    normalize_sec_submissions,
    normalize_sofr,
    normalize_treasury_auctions,
    normalize_treasury_yield_curve_xml,
    sec_headers,
)


class _CompressedResponse:
    headers: ClassVar[dict[str, str]] = {"Content-Encoding": "gzip"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        import gzip

        return gzip.compress(b'{"ok": true}')


def test_fetch_json_decodes_gzip_provider_responses():
    assert fetch_json(
        "https://example.test", opener=lambda *_args, **_kwargs: _CompressedResponse()
    ) == {"ok": True}


def test_sec_company_facts_flatten_units_and_filing_metadata():
    records = normalize_sec_company_facts(
        {
            "facts": {
                "us-gaap": {
                    "Assets": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2025-12-31",
                                    "val": 10,
                                    "filed": "2026-02-01",
                                    "form": "10-K",
                                    "accn": "000-1",
                                }
                            ]
                        }
                    }
                }
            }
        },
        cik="1234",
    )
    assert records[0]["cik"] == "0000001234"
    assert records[0]["concept"] == "Assets"
    assert records[0]["unit"] == "USD"


def test_sec_submissions_build_canonical_filing_url():
    records = normalize_sec_submissions(
        {
            "filings": {
                "recent": {
                    "accessionNumber": ["0000000001-26-000001"],
                    "filingDate": ["2026-02-01"],
                    "form": ["10-K"],
                    "reportDate": ["2025-12-31"],
                    "primaryDocument": ["annual.htm"],
                }
            }
        },
        cik="1234",
    )
    assert records[0]["source_url"].endswith("/000000000126000001/annual.htm")


def test_alfred_skips_missing_values_and_keeps_vintage():
    records = normalize_alfred_observations(
        {
            "realtime_start": "2020-02-01",
            "observations": [
                {"date": "2020-01-01", "value": "1.8"},
                {"date": "2020-02-01", "value": "."},
            ],
        },
        series_id="DGS10",
    )
    assert records[0]["release_date"] == "2020-02-01"
    assert records[0]["value"] == 1.8
    assert len(records) == 1


def test_alfred_csv_normalizer_assigns_explicit_vintage():
    records = normalize_alfred_csv(
        "observation_date,DGS10_20240102\n2023-01-03,3.73\n2023-01-04,.\n",
        series_id="DGS10",
        vintage_date="2024-01-02",
        source_url="https://alfred.stlouisfed.org/graph/alfredgraph.csv",
    )
    assert records[0]["vintage"] == "2024-01-02"
    assert records[0]["value"] == 3.73
    assert len(records) == 1


def test_treasury_yield_curve_xml_normalizer_flattens_tenors():
    xml = """<feed xmlns='http://www.w3.org/2005/Atom'
      xmlns:d='http://schemas.microsoft.com/ado/2007/08/dataservices'
      xmlns:m='http://schemas.microsoft.com/ado/2007/08/dataservices/metadata'>
      <entry><content><m:properties>
        <d:NEW_DATE>2026-08-14T00:00:00</d:NEW_DATE>
        <d:BC_2YEAR>3.75</d:BC_2YEAR>
      </m:properties></content></entry>
    </feed>"""
    records = normalize_treasury_yield_curve_xml(xml, source_url="https://example.test")
    assert records[0]["series_id"] == "BC_2YEAR"
    assert records[0]["observation_date"] == "2026-08-14"
    assert records[0]["value"] == 3.75


def test_treasury_and_sofr_normalizers_preserve_provider_fields():
    auctions = normalize_treasury_auctions(
        {"data": [{"cusip": "9128", "auction_date": "2026-08-12"}]}
    )
    sofr = normalize_sofr(
        {"refRates": [{"effectiveDate": "2026-08-12", "percentPercentile": "5.31"}]}
    )
    assert auctions[0]["source"] == "treasury-fiscal-data-auctions"
    assert auctions[0]["cusip"] == "9128"
    assert sofr[0]["value"] == 5.31


def test_cftc_and_french_factor_normalizers_create_analysis_records():
    cot = normalize_cftc_positioning(
        [{"report_date_as_yyyy_mm_dd": "2026-08-11", "contract_market_name": "UST"}]
    )
    french = normalize_french_factors(
        "Mkt-RF,SMB,HML,RF\n202601,1.00,0.20,-0.30,0.10\n"
    )
    assert cot[0]["series_id"] == "UST"
    assert french[0]["series_id"] == "Mkt-RF"
    assert french[0]["value"] == 0.01


def test_sec_user_agent_requires_contact():
    assert sec_headers("agentic-pm-lab test@example.com")["User-Agent"].endswith(
        "test@example.com"
    )
