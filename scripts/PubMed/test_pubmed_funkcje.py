from pubmed_funkcje import metadata_table

import pandas as pd
import pytest

@pytest.fixture
def mock_record():
    return [
        {
            "Id": "12345678",
            "Title": "Fake title",
            "FullJournalName": "Fake journal name",
            "PubDate": "2021 Jan",
            "AuthorList": ["Jan Nowak", "Andrzej Kowalski"],
        }
    ]

def test_metadata_table(monkeypatch, mock_record):
    def mock_esummary(db, id):
        return "fake_stream"

    def mock_read(stream):
        assert stream == "fake_stream"
        return mock_record

    monkeypatch.setattr("pubmed_funkcje.Entrez.esummary", mock_esummary)
    monkeypatch.setattr("pubmed_funkcje.Entrez.read", mock_read)

    pmids = ["12345678"]
    config = {"email": "random@mail.com"}

    df = metadata_table(pmids, config)

    assert isinstance(df, pd.DataFrame)

    row =df.iloc[0]

    assert row["PMID"] == "12345678"
    assert row["title"] == "Fake title"
    assert row["journal"] == "Fake journal name"
    assert row["ppublish_year"] == "2021"
    assert row["authors"] == "Jan Nowak, Andrzej Kowalski"















