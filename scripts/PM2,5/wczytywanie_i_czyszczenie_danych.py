import pandas as pd
import requests
import zipfile
import io, os
import sys
import datetime
import re

#----------------------------------------------------------------------------------

#Funkcja do ściągania podanego archiwum
def download_gios_archive(year: int, gios_id: str, gios_archive_url: str, filename: str) -> pd.DataFrame:
    #Pobranie archiwum ZIP do pamięci
    url = f"{gios_archive_url}{gios_id}"
    response = requests.get(url)
    response.raise_for_status()  #Jeśli błąd HTTP, zatrzymaj

    #Otwórz zip w pamięci
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        #Znajdź właściwy plik z PM2.5
        if not filename:
            print(f"Błąd: nie znaleziono {filename}.")
        else:
            #Wczytaj plik do pandas
            with z.open(filename) as f:
                try:
                    df = pd.read_excel(f, header=None)
                except Exception as e:
                    print(f"Błąd przy wczytywaniu {year}: {e}")

    return df

#----------------------------------------------------------------------------------

#Pobranie metadanych
def download_metadane(gios_id: str, gios_archive_url: str, filename: str) -> pd.DataFrame:
    url = f"{gios_archive_url}{gios_id}"
    response = requests.get(url)
    response.raise_for_status()

    try:
        z = io.BytesIO(response.content)
        df = pd.read_excel(z, header=0)
    except Exception as e:
        print(f"Błąd przy wczytywaniu {filename}, {e}")

    #Musialem dodac bo w wystepuja nazwy Kod stacji zawierajace biale znaki - powodowalo bledy
    df["Kod stacji"] = df["Kod stacji"].astype(str).str.strip().str.replace(r'[\n\r\t]', '', regex=True)
    return df

#----------------------------------------------------------------------------------

##Definicje funkcji czyszczących pliki

#Usuwa niepotrzebne wiersze
def usun_wiersze(df: pd.DataFrame) -> pd.DataFrame:
    """
    Funkcja buduje maskę dla df, zawierającą tylko dane formatu datetime.datetime oraz pojedyńczą wartość "Kod stacji". Dzięki czemu czyśći df z niepotrzbnych wierszy

    :param df: Data frame, w którym wyselektuje zbędne wiersze
    :return: Data frame tylko z danymi o jakości powietrza lub o kodach stacji
    """
    df = df.copy()
    col = df.iloc[:, 0]

    maska_daty = col.apply(lambda x: isinstance(x, datetime.datetime))
    maska_kod = col == "Kod stacji"
    maska = maska_daty | maska_kod
    df.drop(df.index[~maska], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

#Jednolity format
def ujed_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Funkcja ustawia odpowiednie wiersze/kolumny na indeksowe, ujednolica ich format oraz format wartości.

    :param df: data frame, gdzie dokonane zostaną zmiany formatowania
    :return: zaktualizowany data frame
    """
    df=df.copy()
    df.columns = df.iloc[0] #pierwszy wiersz "Kod stacji", ustawiam jako nagłówkowy
    df = df.iloc[1:].copy() #wycinam ten wiersz z wartości df
    df.reset_index(drop=True, inplace=True)

    #Niektóre Kody stacji, zawieraja biale znaki -> usuwam je
    df = df.T
    df.index = df.index.astype(str).str.strip().str.replace(r'[\n\r\t]', '', regex=True)
    df = df.T

    #Wszystkie wartości pierwszej kolumny zamieniam na typ datetime
    pier_kol = df.columns[0]
    df[pier_kol] = pd.to_datetime(df[pier_kol], errors='coerce')
    df[pier_kol] = df[pier_kol].dt.floor("min")

    #Ustawiam pierwszą kolumne jako indeks
    df.set_index(pier_kol, inplace=True)

    #Czyszcze/ujednolicam nazwy kolumn
    df.columns = (
        df.columns.astype(str)
        .str.strip()
    )

    #zamiana wartości na liczby
    df = df.replace(',', '.', regex=True)
    df = df.apply(pd.to_numeric, errors='coerce')

    return df

#Aktualizacja kodów stacji
def aktualizuj_kod(df: pd.DataFrame, met: pd.DataFrame) -> pd.DataFrame:
    """
    Funkcja zamienia przestarzałe kody stacji na nowe, zgodnie z informacjami z metadanych.

    :param df: data frame, gdzie wykonywana jest podmiana
    :param met: data frame, z metadanymi danych pomiarowych
    :return: zaktualizowany data frame
    """
    df = df.copy()
    #Biore tylko wiersze gdzie stary kod NIE jest NaN (ani "" w kilku przypadkach)
    mapa_nazw = {}
    for stare_polaczone, nowy in zip(met.loc[0:, 'Stary Kod stacji \n(o ile inny od aktualnego)'], met.loc[0:, 'Kod stacji']):
        if pd.notna(stare_polaczone) and stare_polaczone != "":
            #Niektóre stacje mają kilka starych kodów
            stare_kody = [s.strip() for s in stare_polaczone.split(",")]
            for stary in stare_kody:
                mapa_nazw[stary] = nowy

    # SANITY CHECK 3: Sprawdzenie, czy mapa nie jest całkowicie pusta
    if not mapa_nazw:
        print("Ostrzeżenie: Nie znaleziono żadnych starych kodów do zmapowania (wszystkie były puste). Mapa kodów pusta.")

    df = df.rename(columns=mapa_nazw)#Podmiana nazw kolumn zgodnie z mapą nazw stacji

    return df

#Usunięcie unikalnych kodów
def usun_uniq(df: pd.DataFrame, wspolne_kody: list[str]) -> pd.DataFrame:
    """
    Funkcja zwraca data frame bez kolumn oznaczonych kodem stacji, który nie występuje we wszystkich innych data frameach.

    :param df: data frame, gdzie usuwane są kolumny
    :param wspolne_kody: lista kodów, które powtarzają się każdym innym data framie
    :return: zaktualizowany data frame
    """
    df = df.copy()

    return df[wspolne_kody]


#Tworzenie MultiIndex w nagłówkach
def polacz_nagl(df: pd.DataFrame, polaczone_nagl: list[tuple[str, str]]) -> pd.DataFrame:
    """
    Funkcja tworzy nagłówki typu MultiIndex (Miejscowosc, Kod stacji).

    :param df: data frame, gdzie dodany zostanie MultiIndex
    :param polaczone_nagl: lista zawierająca krotki Kodów stacji i odpowiadające im miejscowości
    :return: zaktualizowany data frame
    """
    df = df.copy()
    df.columns = pd.MultiIndex.from_tuples(polaczone_nagl, names=['Miejscowosc', 'Kod stacji'])

    return df


#Zamiana dat z godziny 00:00:00 na dzień poprzedni
def poprzedni_dzien(df: pd.DataFrame) -> pd.DataFrame:
    """
    Funkcja znajduje daty w kolumnie indeksowej, gdzie godzina równa 00:00:00 i cofa dzień kalendarzowy o 1.

    :param df: data frame, gdzie zostaną dokonane zmiany
    :return: zaktualizowany data frame
    """
    df=df.copy()
    maska_czasow = df.index.time == pd.to_datetime('00:00:00').time()
    #Odejumje od kolumny ideksowej 1 lub 0 dni
    df.index = df.index - pd.to_timedelta(maska_czasow.astype(int), unit='d')

    return df


#Sprawdzenie czy pliki mają równą liczbę kolumn
def czy_rowna_l_stacji(dfs: dict[int, pd.DataFrame]) -> None:
    """
    Funkcja sprawdza czy czyszczenie przebiegło pomyślnie - czy pliki mają równą liczbę kolumn.
    W przypadku niedopasowania kończy działanie programu.

    :param dfs: lista data frameów do porównania
    """
    ile_stacji = [df.shape[1] for df in dfs.values()]
    czy_rowne = len(set(ile_stacji)) == 1
    if not czy_rowne:
        sys.exit('Błąd: Liczba kolumn w plikach jest różna')


#Sprawdzenie czy pliki mają odpowiednią liczbę dni w roku
def czy_poprawna_l_dni(dfs: dict[int, pd.DataFrame]) -> None:
    """
    Funkcja sprawdza czy czyszczenie przebiegło pomyślnie - czy każdy plik ma poprawną liczbę dni(kalendarzowo).
    W przypadku niedopasowania kończy działanie programu.

    :param dfs: lista data frameów do sprawdzenia
    """
    from calendar import isleap
    for df in dfs.values():
        rok = df.index.year[0]
        l_dni = df.index.normalize().unique() #wszystkie godziny -> 00:00:00, tylko unikalne wartosci
        l_dni_poprawnie = 366 if isleap(rok) else 365
        if len(l_dni) != l_dni_poprawnie:
            sys.exit(f"Bład: Liczba dni w pliku {rok}_PM2.5_1g.xlsx jest niepoprawna")

#----------------------------------------------------------------------------------

#Wywołanie funkcji czyszczących
def wyczysc_pliki(dfs: dict[int, pd.DataFrame], met: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """
    Funkcja wywołuje inne funkcje odpowiadające za modyfikacje każdego rozpatrywanego data framea.

    :param dfs: słownik zawierający jako wartości data framey, na których wykonane zostaną funkcje oraz odpowiadające im lata jako klucze
    :param met: data frame z metadanymi pogodowymi
    :return: lista odpowiednio zmodyfikowanych data frameów
    """
    #Ujednolicam format i aktualizuje nazwy kodow stacji
    for rok, df in dfs.items():
        dfs[rok] = usun_wiersze(df)

    for rok, df in dfs.items():
        dfs[rok] = ujed_format(df)

    for rok, df in dfs.items():
        dfs[rok] = aktualizuj_kod(df, met)

    #Tworze set wspolnych kodow stacji
    wspolne_kody=set()
    for rok, df in dfs.items():
        if not wspolne_kody:
            wspolne_kody = set(df.columns)
        else:
            wspolne_kody &= set(df.columns)

    #Usuwam unikalne kody stacji z każdej listy danych
    for rok, df in dfs.items():
        dfs[rok] = usun_uniq(df, list(wspolne_kody))

    #Multi indeksowanie(miejscowosc | Kod stacji)
    stacja_miejscowosc = dict(zip(met.loc[:, 'Kod stacji'], met.loc[:, 'Miejscowość']))
    multi_index = [(stacja_miejscowosc[kod], kod) for kod in wspolne_kody]

    for rok, df in dfs.items():
        dfs[rok] = polacz_nagl(df, multi_index)


    #Zamiana - północ jako dzień poprzedni

    for rok, df in dfs.items():
        dfs[rok] = poprzedni_dzien(df)

    #Sprawdzanie sanity checks
    czy_rowna_l_stacji(dfs)
    czy_poprawna_l_dni(dfs)

    return dfs

#----------------------------------------------------------------------------------

#Łączenie kilku df's w całość
def polacz_dfs(dfs: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """
    Funkcja łączy wcześniej przygotowane data frame i tworzy z nich plik typu xlsx

    :param dfs: lista data frameów do połączenia
    :return: jeden df utworzony z połączonych składowych df's
    """
    #Łącze pliki według wierszy
    dfs_polaczone = pd.concat(dfs.values(), axis=0)

    #Multi indeksowanie zostało rozłączone => łącze z powrotem
    dfs_polaczone.columns = [f'{miejscowosc}_{stacja}' for miejscowosc, stacja in dfs_polaczone.columns]
    dfs_polaczone.columns.name = None

    #Zamieniam daty z powrotem na wartość aby ich nie stracić przy zapisie
    dfs_polaczone = dfs_polaczone.reset_index(names='Miejscowość_Kod stacji')

    return dfs_polaczone

#----------------------------------------------------------------------------------

#Zapis do pliku xlsx
def zapisz_do_excel(dfs_polaczone: pd.DataFrame, lata: list[int]) -> None:
    #zapis jako plik xlsx
    dfs_polaczone.to_excel(f"pomiarPM25_lata_{'_'.join(map(str, lata))}.xlsx", index=False)