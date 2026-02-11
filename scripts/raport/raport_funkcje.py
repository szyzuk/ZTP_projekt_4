import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

#----------------------------------------BAZA-------------------------------------------

def df_to_markdown(df: pd.DataFrame) -> str:
    """
    Funkcja zamienia df na tabele w formacie markdown

    :param df: df do zapisania
    :return: df w zamienionym formacie
    """

    return df.to_markdown(index=False)

def combine_results(years: list[str], path: str) -> pd.DataFrame:
    """
    Funkcja pobiera wyniki z danych lat z odopowiedniej ścieżki, i łączy je w jedną tabele danych,
    gdzie dane z poszczególnych lat będa rozróżniane za pomocą nowej kolumny z rokiem danych

    :param years: Lata z których łączymy wyniki
    :param path: Ścieżka gdzie trzymane są dane do połączenia
    :return: df z połączonymi wynikami
    """

    dfs = []
    for year in years:
        df = pd.read_csv(path.format(year=year))
        df["year"] = year
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

#-----------------------------------TABELA_PRZEKROCZEN-----------------------------------

def combine_exceedence_days(years: list[str]) -> pd.DataFrame:
    """
    Funkcja tworzy tabele z liczbą dni przekroczenia zawartości pyłu PM2.5 w powietrzu z podziałem na lata

    :param years: Lata z których pobieramy dane do złączenia
    :return: Tabela wynikowa
    """
    df_polaczone = combine_results(years, "results/pm25/{year}/exceedance_days.csv")

    df_wynik = (
        df_polaczone
        .pivot(
            index="Miejscowosc_Stacja",
            columns="year",
            values="Ilosc dni z przekroczeniem"
        )
        .reset_index()
        .dropna()
    )

    return df_wynik

#---------------------------------------LITERATURA----------------------------------------

def combine_literature(years: list[str]) -> pd.DataFrame:
    """
    Funkcja wybiera pierwsze 10 tytułów publikacji z każdego roku, i tworzy tabele z nimi

    :param years: Zakres lat
    :return: df z tytułami  i rokiem z którego pochodzi dopasowanie
    """

    df_polaczone = combine_results(years, "results/literature/{year}/pubmed_papers.csv")

    df_wynik = df_polaczone.groupby("year").head(10).reset_index(drop=True)

    df_wynik = df_wynik[["title", "year"]]

    return df_wynik

#-------------------------------DOPASOWANIA_DO_ZAPYTANIA----------------------------------

def combine_summary_by_year(years: list[str]) -> pd.DataFrame:
    """
    Funkcja tworzy tabele z informacją o liczbie znalezionych publikacji dla danych zapytań z podziałem na rok

    :param years: Lata z których łączymy dane
    :return: Tabela wynikowa
    """

    df_polaczone = combine_results(years, "results/literature/{year}/summary_by_year.csv")

    df_wynik = (
        df_polaczone
        .pivot(
            index="query",
            columns="year",
            values="n_publications"
        )
        .reset_index()
        .fillna(0)
    )
    return df_wynik

#----------------------------------TREND_PUBLIKACJI-------------------------------------

def trend_ppublish(years: list[str]) -> Figure:
    """
    Funckja tworzy wykres trendu liczby publikacji printów z w danych latach

    :param years: Zakres lat danych
    :return: Wykres z linią trendu publikacji
    """
    df_polaczone = combine_results(years, "results/literature/{year}/pubmed_papers.csv")

    df_trend = df_polaczone.groupby("ppublish_year").size()

    fig, ax = plt.subplots(figsize=(10, 6))

    df_trend.plot(kind='line', marker='o', color='#2b7bba', ax=ax)

    lata = df_trend.index
    ax.set_xticks(np.arange(min(lata), max(lata) + 1, 1))

    ax.set_title(f'Trend liczby publikacji printów w danych latach', fontsize=14)
    ax.set_xlabel('Rok')
    ax.set_ylabel('Ilość publikajcji printów')
    ax.grid(True, linestyle='--', alpha=0.7)

    fig.tight_layout()

    return fig

#----------------------------------TOP_CZASOPISMA---------------------------------------

def combine_top_journals(years: list[str]) -> pd.DataFrame:
    """
    Funkcja tworzy tabele z czasopisami o największej ilości publikacji w danych latach

    :param years: Zakres lat z danymi
    :return: Tabele z z topowymi czasopismami oraz informacją o sumie publikacji oraz publikacji w danych latach
    """

    df_polaczone = combine_results(years, "results/literature/{year}/top_journals.csv")

    df_lata =(
        df_polaczone
        .pivot(
            index="journal",
            columns="year",
            values="num_publications"
        )
        .fillna(0)
    )

    df_lata["suma_publikacji"] = df_lata.sum(axis=1)

    df_wynik = (
        df_lata
        .sort_values("suma_publikacji", ascending=False)
        .head(10)
        .reset_index()
    )

    kolumny_lat = sorted([kol for kol in df_wynik.columns if isinstance(kol, int)])
    df_wynik = df_wynik[["journal", "suma_publikacji"] + kolumny_lat]

    return df_wynik

#----------------------------------TYTUŁY--------------------------------------------

def example_titles(years: list[str], n: int) -> Figure:
    """
    Funkcja tworzy obrazek z przykładowymi tytułami (pierwsze z listy) dla każdego roku z zakresu

    :param years: Zakres lat
    :param n: Maksymalna liczba wyświetlanych tytułów dla danego roku
    :return: Obrazek z tytułami
    """

    fig, ax = plt.subplots(figsize=(10, 2+2*len(years)))
    ax.axis('off')

    y = 1.0
    line_height = 0.08

    df_polaczone = combine_results(years, "results/literature/{year}/pubmed_papers.csv")

    for year in years:
        df_year = df_polaczone[df_polaczone["year"] == year].head(n)

        ax.text(
            0.01, y,
            f'Dla {year} roku:',
            fontsize=14,
            fontweight='bold',
            transform=ax.transAxes,
        )
        y -= line_height

        for i, title in enumerate(df_year["title"], start=1):
            ax.text(
                0.03, y,
                f'{i}) {title}',
                fontsize=11,
                wrap=True,
                transform=ax.transAxes
            )
            y -= line_height

        y -= line_height / 2

    fig.tight_layout()
    return fig