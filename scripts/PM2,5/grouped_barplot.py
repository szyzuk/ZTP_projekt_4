import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure


def policz_dni_z_przekroczeniem(df_wejsciowe: pd.DataFrame, lata: list) -> pd.DataFrame:
    """
    Oblicza liczbę dni w konkretnych latach, w których średnie dobowe stężenie PM2.5 przekroczyło 15 µg/m³

    Args:
        df_wejsciowe (pd.DataFrame): DataFrame z danymi godzinnymi o stężeniu PM2.5
    Returns:
        pd.DataFrame: Tabela indeksowana latami, zawierająca liczbę dni z przekroczeniami dla każdej stacji
    """
    df = df_wejsciowe.copy()

    # Zamiast poprzedniego podejścia z tworzeniem nowych kolumn, najpierw wyciągam informacje o dacie z 'index', a potem usuwam to z df
    df.index = pd.to_datetime(df.pop('Miejscowość_Kod stacji'))

    # Liczymy średnią dzienną
    df_dzienne = df.resample('D').mean()

    # Jeśli norma przekroczona, oznaczamy to jako 1. Następnie grupujemy po latach i sumujemy (sprowadza się to do sumy jedynek).
    oznacz_przekroczenie = df_dzienne > 15

    # Grupujemy po roku wyciągniętym z indeksu (sumowanie od razu jako sum() zamiast dodatkowej linijki)
    wynik = oznacz_przekroczenie.groupby(oznacz_przekroczenie.index.year).sum()

    wynik_koncowy = wynik.reindex(lata)

    return wynik_koncowy


def top3_przekroczen(zestawienie_przekroczen: pd.DataFrame) -> (list[str], list[str]):
    """
    Wyznacza 3 stacje z najmniejszą oraz 3 z największą sumaryczną liczbą dni z przekroczeniami normy

    Args:
        zestawienie_przekroczen (pd.DataFrame): Tabela indeksowana latami, zawierająca liczbę dni z przekroczeniami dla każdej stacji
    Returns:
        tuple[list[str], list[str]]: Krotka zawierająca dwie listy: pierwsza z nazwami 3 najczystszych stacji, druga z nazwami najbardziej zanieczyszczonych
    """
    # Sortujemy od najmniejszego do największego sume dni z przekroczeń z każdej stacji
    posortowane_wyniki = zestawienie_przekroczen.sum().sort_values()

    najlepsze_wyniki = posortowane_wyniki.head(3) # najczyste
    najgorsze_wyniki = posortowane_wyniki.tail(3).iloc[::-1] # najbardziej zanieczyszczone

    lista_najlepszych = [stacja for stacja in najlepsze_wyniki.index]
    lista_najgorszych = [stacja for stacja in najgorsze_wyniki.index]

    return lista_najlepszych, lista_najgorszych


def stworz_grouped_barplot(df: pd.DataFrame, lata: list) -> Figure:
    """
    Wyświetla zgrupowany wykres słupkowy dla 3 stacji o najmniejszej i 3 o największej liczbie dni z przekroczeniami normy WHO.

    Args:
        df (pd.DataFrame): DataFrame z danymi godzinnymi o stężeniu PM2.5 (dane wejściowe do obliczeń)
    Returns:
        None: Funkcja nie zwraca wartości, wyświetla jedynie gotowy wykres
    """
    df_wyniki = policz_dni_z_przekroczeniem(df, lata)
    najlepsze, najgorsze = top3_przekroczen(df_wyniki)

    # Bierzemy dane tylko dla tych sześciu stacji
    df_plot = df_wyniki[najlepsze + najgorsze].copy()

    # Konfiguracja osi i danych
    # Wyświetlamy zarówno nazwy miejscowości jak i kody stacji
    stacje = [f"{kol.split('_')[0]},\n{kol.split('_')[1]}" for kol in df_plot.columns]
    x = np.arange(len(stacje)) # rozmieszczenie na osi x
    width = 0.8 / len(lata)
    offsets = np.linspace(-0.4 + width / 2, 0.4 - width / 2, len(lata))
    colors = plt.cm.get_cmap('tab10', len(lata)).colors

    # Rysowanie wykresu
    fig, ax = plt.subplots(figsize=(12, 8))

    for i, rok in enumerate(lata):
        # Rysujemy słupki i dodajemy nad nimi liczby
        rects = ax.bar(x + offsets[i], df_plot.loc[rok].values, width, label=str(rok), color=colors[i], edgecolor='black')
        ax.bar_label(rects, fontsize=9)

    # Dodanie podpisów osi, tytułów, linii oddzielającej dwie części wykresu, podpisów do każdej grupy stacji
    ax.set_ylabel('Liczba dni z przekroczeniem (>15 µg/m³)', fontsize=12)
    ax.set_title('Porównanie liczby dni smogowych w 3 najlepszych i 3 najgorszych stacjach', fontsize=14, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stacje, fontsize=10)
    ax.axvline(x=2.5, color='gray', linestyle='--', linewidth=1)
    ax.text(1, ax.get_ylim()[1]*0.95, "Najczystsze", ha='center', color='green')
    ax.text(4, ax.get_ylim()[1]*0.95, "Najbardziej zanieczyszczone", ha='center', color='red')
    ax.legend(title='Rok')

    fig.tight_layout()
    return fig

#-------------------------------------------------------------------------------------------


def policz_przekroczenia_woj(df_wejsciowe, metadane, lata):
    #Mapowanie województw
    stacje_wojewodztwa = metadane[["Kod stacji", "Województwo"]].dropna().copy()
    stacje_wojewodztwa.drop_duplicates(inplace=True)
    stacje_wojewodztwa["Kod stacji"] = stacje_wojewodztwa["Kod stacji"].str.strip() #usunięcie spacji

    #kopia
    df = df_wejsciowe.copy()

    #Ustawienie daty jako indeksu
    kolumna_daty = df.columns[0]
    df[kolumna_daty] = pd.to_datetime(df[kolumna_daty]) #konwersja na datetime
    df.set_index(kolumna_daty, inplace=True)

    #Filtrowanie
    df = df.select_dtypes(include=['number'])

    #Obliczenia - zapożyczony kod
    df_dzienne = df.resample('D').mean()
    przekroczenia = (df_dzienne > 15).astype(int)
    wynik_stacje = przekroczenia.groupby(przekroczenia.index.year).sum()

    #Ograniczenie danych do danych lat
    wynik_stacje = wynik_stacje.reindex([int(l) for l in lata])

    #Przekształcenie do formatu long
    wynik_long = wynik_stacje.stack().reset_index()
    wynik_long.columns = ['Rok', 'Kod stacji', 'Liczba_dni']

    # Czyszczenie nazw (wycinanie "Miasto_") - wyciągnięcie tylko kodu stacji
    wynik_long['Kod stacji'] = wynik_long['Kod stacji'].apply(lambda x: x.split('_')[-1] if '_' in str(x) else x)

    #Dołączenie kolumny województw na podstawie kodów stacji
    polaczone = wynik_long.merge(stacje_wojewodztwa, on='Kod stacji')

    #Średnia liczba dni z przekroczeniem dla wszystkich stacji w danym województwie
    wynik_koncowy = polaczone.groupby(['Województwo', 'Rok'])['Liczba_dni'].mean().unstack(level=1)

    return wynik_koncowy


def stworz_barplot_przekroczenia_woj(df_do_wykresu):

    # Tworzenie wykresu słupkowego
    ax = df_do_wykresu.plot(kind='bar', figsize=(16, 8), width=0.8, color=['#2d6a4f', '#74c69d', '#b7e4c7', '#d8f3dc'])

    # Dodanie tytułów
    ax.set_title('Liczba dni z przekroczeniem normy PM2.5 w województwach', fontsize=16, pad=20)
    ax.set_ylabel('Średnia liczba dni z przekroczeniem', fontsize=12)
    ax.set_xlabel('Województwo', fontsize=12)

    # Dodanie wartości nad słupkami
    for p in ax.patches:
        if p.get_height() > 0: #pobranie wysokości słupka
            ax.annotate(f'{p.get_height():.0f}', #wstawienie napisu
                        (p.get_x() + p.get_width() / 2., p.get_height()), #współrzędne napisu
                        ha='center',
                        xytext=(0, 9), #przesunięcie napisu względem końca słupka
                        textcoords='offset points', #drukarskie jednostki
                        fontsize=8, rotation=90) #wielkość czcionki; obrót napisu o 90 stopni

    # Stylizacja osi i legendy
    ax.legend(title='Rok pomiaru', bbox_to_anchor=(1, 1), loc='upper left')
    #plt.xticks(rotation=45, ha='right')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(axis='y', linestyle='-', alpha=0.3)

    # Usunięcie górnej i prawej ramki dla lepszej czytelności
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig = ax.get_figure()
    fig.tight_layout()
    return fig


