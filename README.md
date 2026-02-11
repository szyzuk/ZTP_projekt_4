# Projekt 4 na przedmiot "Zaawansowane techniki programowania dla bioinformatyków"

Celem projektu jest połączenie działania dwóch skryptów do analizy danych w jeden pipeline.  
Pipeline zbudowany w **Snakemake** i umożliwia:  

- Analize danych o zawartości pyłu PM2.5 w powietrzu w Polsce  
- Pobranie artykułów z PubMed dla określoncyh lat i zapytań oraz ich analizę ilościową 

Wszystkie parametry można konfigurować w odpowiednich plikach YAML w katalogu `config/`.  
Środowisko potrzebne do uruchomienia pipeline’u jest opisane w `requirements.txt`.

## Instrukcja obsługi i opis działania

Pipeline został zbudowany w **Snakemake** i składa się z trzech głównych części: PM2.5, PubMed oraz raport końcowy.

### 1. Wymagania wstępne

- Python 3.12  
- Snakemake  

Należy utworzyć srodowisko i pobrać wszystkie wymagania z pliku 'requirements.txt'

### 2. Konfiguracja

Przed uruchomieniem pipeline'u należy uzupełnić pliki konfiguracyjne w katalogu config/
a) pm25.yaml:
  - miasta -> wstawić dwie nazwy Polskich miast które będą porównywane na wykresie
b) pubmed.yaml:
  - email -> Należy podać email informacyjny dla PubMed w razie potrzeby kontaku o nieudanym poborze danych
  - lim_wynikow -> limit znalezionych artykułów dla każdego zapytania
  - zapytania -> Słowne zapytania do szukania artykułów (sformatowane tak jak do przeszukiwania serwisu PubMed)
  - top_n -> maksymalna liczba napopularniejszych czasopism
c) task4.yaml:
  - years -> para lat z zakresu {2014, 2015, 2018, 2019, 2021, 2024} do porównania

###  3. Uruchomienie
Warto zacząć od wpisania w konsole komendy:
```bash
snakemake -n
```
W celu weryfikacji wstępnej wykonywanego kroku

Naztępnie:
```bash
snakemake -s Snakefile --cores 1
```


### 4. Wyniki - weryfikacja
Jeśli pipeline wykonał się poprawnie, wyniki możemy znależć w katalogu results. Odpowiednio rozdzielone są wyniki dla każdego segmentu oraz dla poszczególnych lat. Dodatkowo powinien powstać raport zbiorczy "report_task4.md" z danymi z obu lat zestawionymi razem.

Jeśli pipeline nie przebiegł pomyślnie, należy się upewnić, że wszystkie wymagania zostały popranie pobrane a pliki konfiguracyjne odpowiednio uzupełnione.

## Przykładowy scenariusz działania 
1) Odpowiednio pobieram wymagania i zgodnie z instrukcją uzupełniam config/ oraz ustawiam parametr years na [2021, 2024]
2) Uruchamiam odpowiednią komendą pipeline (Podsumowanie liczby rule do wykonania wynosi 6)
3) Pomyślny przebieg powinien mi dać folder "results" z odpowiednimi subfolderami z podziałem na wyniki dla poszczególnych lat oraz zbiorczy raport dla lat 2021 oraz 2024
4) Zmieniam parametr years na [2019, 2024]
5) Ponownie uruchamiam pipeline ze zmienionym parametrem, w konsoli mogę zaobserwować mniejszą ilość rule'i do wykonania (czyli 4). Wynika to z tego, że wyniki dla roku 2024 już istnieją przez co pipeline omija wykonywanie tego samegopo raz drugi. W przypdaku zamiana któregoś z parametrów w innych plikach z folderu config/, pipeline wykonał by się ponownie dla obu lat.
6) Po wykonaniu pipeline'u w folderze "results" dodane zostały wyniki dla roku 2019 oraz zmieniony został "report_task4.md" odpwoiednio dla ostaniego wykonania pipelin'u.

