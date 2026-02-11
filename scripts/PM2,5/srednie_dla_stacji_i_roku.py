import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

#--------------------------------------------------------------------------------------------

def srednie_miesieczne_dla_lokalizacji(df: pd.DataFrame, lata: list[int], czy_miasto: bool) -> pd.DataFrame:
    """
    Funkcja wylicza średnią miesięczną zawartość pyłu pm2.5 w róznych lokalizacjach (miasta/stacje)

    :param df: df z danymi pomiarowymi
    :param lata: lata z których interesują nas dokonane pomiary
    :param czy_miasto: jeśli "True", to liczy średnią dla miast, dla "False" liczy dla stacji
    :return: df z uśrednionymi danymi pomiarowymi
    """
    df = df.copy()
    df.index = pd.to_datetime(df.pop('Miejscowość_Kod stacji'))
    #df.index = pd.to_datetime(df.index)

    #Ustalam czy intersować będą mnie dane z konkretnych stacji czy z miast
    if czy_miasto:
        df.columns = [kol.split('_')[0] for kol in df.columns]
    else:
        df.columns = [kol.split('_')[-1] for kol in df.columns]

    #Uśredniam względem miesięcy
    df = df.resample('ME').mean()

    # Uśredniam kolumny z tych samych lokacji (tutaj dla miast)
    df = df.T.groupby(level=0).mean().T

    #zmiany stylistyczne
    df = df[df.index.year.isin(lata)]
    df.index = df.index.to_period('M')

    return df

#--------------------------------------------------------------------------------------------

def rysuj_wykres_lin(df: pd.DataFrame, miasta: list[str], lata: list[int]) -> Figure:
    """
    Funkcja rysuje wykres liniowy z danymi o średnim zanieczysczeniu powietrza pyłem Pm2.5 w sprecyzowanych miastach i latach

    :param df: df zawierający dane pomiarowe z różnch miast i lat
    :param miasta: miasta które zostaną zwizualizowane na wykresie
    :param lata: lata dla których zostaną utworzone wykresy
    """
    df = df.copy()
    df = srednie_miesieczne_dla_lokalizacji(df, lata, True)

    #Tworze liste kolorów do kolorwania wykresów
    l_roznych = len(miasta)*len(lata)
    cmap = plt.get_cmap('tab20', l_roznych)
    kolory = cmap(np.arange(l_roznych))


    fig, ax = plt.subplots(figsize=(12, 6))
    miesiac = [i for i in range(1, 13)]

    ktory_kolor = 0
    for mi in miasta:
        for rok in lata:
            ax.plot(miesiac, df[mi][df.index.year == rok], 'o-', linewidth=2, markersize=5, color=kolory[ktory_kolor], label=f'{mi} w {rok} roku')
            ktory_kolor += 1

    ax.set_xlabel(f'Miesiąc', size=12)
    ax.set_ylabel(f'Średnie stężenie Pm2.5', size=12)
    ax.set_xticks(miesiac)
    ax.set_title(f'Średnie miesięczne wartości stężenia pyłu PM2.5 w powietrzu w {'_'.join(map(str, lata))}', size=15, weight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()

    return fig