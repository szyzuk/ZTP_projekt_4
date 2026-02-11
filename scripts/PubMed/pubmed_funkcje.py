from Bio import Entrez
import pandas as pd
from typing import Any
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns

#-------------------------------------WCZYTYWANIE_DO_PLIKU------------------------------------

def papers_per_query(year: int, config: dict[str, Any]) -> pd.DataFrame:
    """
    Funkcja dla każdego zapytania z configu wyszukuje publikacje z dopasowaniem do zapytania, z danego okresu.

    :param year: Rok określający zakres przeszukiwania
    :param config: słownik reprezentujący config (task4.yaml)
    :return: Df z poszczegolnymi pmid znalezionych publikacji, rok i zapytanie do którego nastąpiło dopasowanie
    """
    Entrez.email = config["email"]

    date_range = f"{year}/01/01:{year}/12/31[PDAT]"
    rows = []

    for q in config["zapytania"]:
        term = f"({q}) AND ({date_range})"
        stream = Entrez.esearch(
            db="pubmed",
            term=term,
            retmax=int(config["lim_wynikow"])
        )
        record = Entrez.read(stream)

        for pmid in record["IdList"]:
            rows.append({
                "year": year,
                "query": q,
                "PMID": pmid
            })

    return pd.DataFrame(rows)


def metadata_table(pmids: list[str], config: dict[str, Any]) -> pd.DataFrame:
    """
    Funkcja pobiera dane parametry z metadanych dla kolejno wszytkihc pmids z wcześniej dopasowanych artykułów.

    :param pmids: Lista id artykułów z dopasowania
    :param config: słownik reprezentujący config (task4.yaml)
    :return: Tabela zawierjąca wszystkie dane parametry dla każdego artykułu
    """
    Entrez.email = config["email"]
    rows = []

    for batch in [pmids[i:i + 200] for i in range(0, len(pmids), 200)]:
        stream = Entrez.esummary(db="pubmed", id=",".join(batch))
        records = Entrez.read(stream)

        for record in records:
            rows.append({
                "PMID": record["Id"],
                "title": record["Title"],
                "journal": record["FullJournalName"],
                "ppublish_year": record["PubDate"].split(" ")[0],
                "authors": ", ".join(record.get("AuthorList", []))
            })

    return pd.DataFrame(rows)


def dl_papers(year: int, config: dict[str, Any]) -> pd.DataFrame:
    """
    Funkcja spinająca pobieranie pmids oraz ich metadanych.

    :param year: Dany rok zakresu przeszukiwania
    :param config: słownik reprezentujący config (task4.yaml)
    :return: Zintegrowane tabele, w taki sposób że zawierają wszystkie metadane oraz wiadomo jakie zapytanie "znalasło" dany artykuł
    """
    df_pmids = papers_per_query(year, config)
    unique_pmids = df_pmids["PMID"].unique().tolist()

    df_meta = metadata_table(unique_pmids, config)

    return df_meta.merge(df_pmids, on="PMID", how="left")

#-----------------------------------SUMMARY_BY_YEAR------------------------------------

def make_summary_by_year(df_data: pd.DataFrame) -> pd.DataFrame:
    """
    Funkcja zwraca df z podsumowaniem ilości publikacji znalezionych dla danego zapytania w danym roku

    :param df_data: tabela wszystkich danych z dopasowania
    :return: Podsumowanie liczby dopasowań dla zapytania
    """
    df_summ = df_data.copy()

    return (
        df_summ
        .groupby(["year", "query"])
        .agg(n_publications=("PMID", "nunique"))
        .reset_index()
        .sort_values(["query", "year"])
    )

#-----------------------------------TOP_JOURNALS------------------------------------

def top_n_journals(df_data: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    """
    Funkcja zwraca top n nazwa czasopism z największą liczbą publikacji (dopasowanych) w danym roku

    :param df_data: tabela wszystkich danych z dopasowania
    :param config: słownik reprezentujący config (task4.yaml)
    :return: nazwy czasopism wraz z ilością publikacji w danym roku
    """
    df_journals = df_data.copy()
    top_n = config["top_n"]

    return (
        df_journals
        .groupby("journal")
        .size()
        .reset_index(name="num_publications")
        .sort_values("num_publications", ascending=False)
        .head(top_n)
    )

#-------------------------------------BARPLOT---------------------------------------

def summary_barplot(df_summ: pd.DataFrame, year: int) -> Figure:
    """
    Funkcja tworzy barplot wizualizujący dane z summary_by_year

    :param df_summ: tabela podsumowania
    :param year: rok dopasowania
    :return: obraz z wykresem typu varplot
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    sns.barplot(
        data=df_summ,
        x="query",
        y="n_publications",
        ax=ax
    )

    ax.set_xlabel("Zapytanie")
    ax.set_ylabel("Liczba publikacji")
    ax.set_title(f"Liczba publikacji dla danych zapytań w {year} roku")
    ax.tick_params(axis="x", rotation=45, labelsize=6)

    fig.tight_layout()
    return fig