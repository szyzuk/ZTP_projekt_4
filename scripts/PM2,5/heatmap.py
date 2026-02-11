import pandas as pd
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

def przygotuj_dane_do_heatmapy(df_wejsciowe: pd.DataFrame) -> pd.DataFrame:
    """
    Funkcja obrabiające dane z pliku, by pasowały do wymagań zadania (grupy po miastach, średnie miesięczne)

    Args:
        df_wejsciowe (pd.DataFrame): Zmergowane dane wejściowe z lat 2014, 2019, 2024, odnośnie zanieczyszczeń pyłami PM2.5
    Returns:
        pd.DataFrame: Dane w formacie długim z kolumnami [Rok, Miesiąc, Miasto, PM2.5], gotowe do wizualizacji
    """
    df = df_wejsciowe.copy()

    # Zamiast poprzedniego podejścia z tworzeniem nowych kolumn, najpierw wyciągam informacje o dacie z 'index', a potem usuwam to z df
    df.index = pd.to_datetime(df.pop('Miejscowość_Kod stacji'))

    # Wyciągamy nazwy miast z kolumn i grupujemy po czasie, biorąc średnią (te same zabiegi co w zadaniu 2)
    df_miesieczne = df.resample('ME').mean()
    nazwy_miast = [kol.split('_')[0] for kol in df_miesieczne.columns]

    # Dla ułatwienia najpierw bierzemy nazwy miast i dajemy je jako wiersze, potem liczymy średnie, a potem znowu transponujemy
    df_grupowane_miasta = df_miesieczne.T.groupby(nazwy_miast).mean().T

    # Przenosimy nazwy miast z kolumn do nowej warstwy indeksu
    df_stacked = df_grupowane_miasta.stack()
    df_stacked.index.names = ['Data', 'Miasto']

    # Grupujemy na podstawie tymczasowych obiektów wewnątrz ‘groupby’, gdzie odpowiednie kolumny się pojawią jako indeksy
    df_wynik = (
        df_stacked.groupby([
            df_stacked.index.get_level_values('Data').year.rename('Rok'),
            df_stacked.index.get_level_values('Data').month.rename('Miesiąc'),
            'Miasto'
        ]).mean().reset_index(name='PM2.5')
    )

    return df_wynik


def stworz_heatmape(df_long: pd.DataFrame, lata: list) -> Figure:
    """
    Rysuje panel heatmap w czystym Matplotlib na podstawie danych przygotowanych przez funkcję 'przygotuj_dane_do_heatmapy'

    Args:
        df_long (pd.DataFrame): DataFrame z danymi sformatowanymi pod zoribenie wykresu heatmap
    Returns:
        None: Funkcja nie zwraca wartości, wyświetla jedynie gotowy wykres
    """
    # Pobranie unikalnych miast (bo nazwy w tabeli są zdublowane) i ułożenie ich alfabetycznie
    unikalne_miasta = sorted(df_long['Miasto'].unique())

    # Konfiguracja siatki wykresów - podział na mniejsze 'pola' pod wykresy
    n_cols = 3
    n_rows = math.ceil(len(unikalne_miasta) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows), sharex=True, sharey=True)
    axes = axes.flatten()

    # Ustawienia wizualne
    cmap = plt.get_cmap("RdYlGn_r") # Czerwony-Żółty-Zielony (odwrócona)
    vmin, vmax = 0, 60 # Zakres kolorów

    # Rysowanie wykresu
    for i, miasto in enumerate(unikalne_miasta):
        ax = axes[i]
        miasto_dane = df_long[df_long['Miasto'] == miasto]

        # Tworzymy macierz (pivot):, gdzie wiersze to rok, a kolumny to miesiąc
        pivot_df = miasto_dane.pivot(index='Rok', columns='Miesiąc', values='PM2.5')

        # Wymuszamy, by tabela miała dokładnie 3 lata i 12 miesięcy
        pivot_df = pivot_df.reindex(index=lata, columns=range(1, 13))

        # Zamiana na macierz numpy (pod imshow)
        data_matrix = pivot_df.to_numpy()

        # Rysowanie (imshow)
        im = ax.imshow(data_matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect='auto')

        # Ręcznie dodajemy liczby w kratkach
        rows, cols = data_matrix.shape
        for r in range(rows):
            for c in range(cols):
                val = data_matrix[r, c]
                # Wypisujemy tylko jeśli wartość istnieje (nie jest NaN)
                if not np.isnan(val):
                    ax.text(c, r, f"{val:.0f}", ha="center", va="center", color='white', fontsize=9)

        # Opisy osi i tytuł
        ax.set_title(miasto)
        ax.set_yticks(range(len(lata)))
        ax.set_yticklabels(lata)
        ax.set_ylabel('Rok')
        ax.set_xticks(range(12))
        ax.set_xticklabels(range(1, 13))
        ax.set_xlabel('Miesiąc')

    # Dostosowujemy miejsce na wykresy - zostawiamy wolny margines po prawej na legendę heatmapy
    fig.tight_layout(rect=[0, 0, 0.9, 1])

    # Potem dodajemy pasek w to wolne miejsce
    cbar_ax = fig.add_axes([0.92, 0.3, 0.02, 0.4])
    fig.colorbar(im, cax=cbar_ax, label='Średnie stężenie PM2.5 [µg/m³]')

    fig.suptitle(f'Średnie miesięczne stężenia PM2.5 w {'_'.join(map(str, lata))}', fontsize=20, y=1.02)

    return fig
