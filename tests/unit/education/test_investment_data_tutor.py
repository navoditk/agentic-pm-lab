from src.education.investment_data_tutor import list_sources, read_sample, teach_source


def test_catalog_links_each_source_to_a_browsable_sample():
    sources = list_sources()
    assert len(sources) == 6
    for source in sources:
        taught = teach_source(source["id"])
        assert taught["sample_file"].startswith("data/samples/public_investment/")
        assert taught["investment_advice"] is False


def test_browse_returns_records_for_json_and_csv_samples():
    assert read_sample("alfred")[0]["vintage"] == "2020-01-03"
    assert read_sample("kenneth-french")[0]["Mkt-RF"] == "0.0100"
    assert len(teach_source("sofr", browse_sample=True)["sample_records"]) == 1
