import pandas as pd
import yaml
import argparse
import os
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("--year", type=int, required=True)
parser.add_argument("--config",  required=True)

args = parser.parse_args()
year = args.year
config_path = args.config

with open(config_path) as f:
    config = yaml.safe_load(f)


out_path = f"results/pm25/{year}"
fig_dir = f"results/pm25/{year}/figures"

#----------------------------------------ZADANIE_1-------------------------------------------

import wczytywanie_i_czyszczenie_danych as wicd

gios_archive_url = "https://powietrze.gios.gov.pl/pjp/archives/downloadFile/"

gios_url_ids = {2014: '302', 2015: '236', 2018: '603', 2019: '322', 2021: '486',2024: '582'}
gios_pm25_file = {
    2014: '2014_PM2.5_1g.xlsx',
    2015: '2015_PM25_1g.xlsx',
    2018: '2018_PM25_1g.xlsx',
    2019: '2019_PM25_1g.xlsx',
    2021: '2021_PM25_1g.xlsx',
    2024: '2024_PM25_1g.xlsx'
}

zakres_lat = [year]
dane_ze_wszystkich_lat = {rok: wicd.download_gios_archive(rok, gios_url_ids[rok], gios_archive_url, gios_pm25_file[rok]) for rok in zakres_lat}

metadane = wicd.download_metadane('622', gios_archive_url, 'Metadane oraz kody stacji i stanowisk pomiarowych.xlsx')

#Obróbka danych
dfs_obrobione = wicd.wyczysc_pliki(dane_ze_wszystkich_lat, metadane)

#Łączenie dfs
dfs_polaczone = wicd.polacz_dfs(dfs_obrobione)


#----------------------------------------ZADANIE_2-------------------------------------------

import srednie_dla_stacji_i_roku as sdsir

monthly_means = sdsir.srednie_miesieczne_dla_lokalizacji(dfs_polaczone, zakres_lat, False)
monthly_means_file = os.path.join(out_path, "monthly_means.csv")
monthly_means.to_csv(monthly_means_file, index=True)


miasta_do_wizualizacji = config["miasta"]

srednie = sdsir.rysuj_wykres_lin(dfs_polaczone, miasta_do_wizualizacji, zakres_lat)
srednie.savefig(os.path.join(fig_dir, f"srednie_{year}.png"), dpi=300, bbox_inches="tight")
plt.close(srednie)

#----------------------------------------ZADANIE_3-------------------------------------------

import heatmap as hm

dane = hm.przygotuj_dane_do_heatmapy(dfs_polaczone)
heatmap = hm.stworz_heatmape(dane, zakres_lat)
heatmap.savefig(os.path.join(fig_dir, f"heatmap_{year}.png"), dpi=300, bbox_inches="tight")
plt.close(heatmap)

#----------------------------------------ZADANIE_4-------------------------------------------

import grouped_barplot as gbp

exceedance_days = gbp.policz_dni_z_przekroczeniem(dfs_polaczone, zakres_lat)
exceedance_days = exceedance_days.melt(var_name="Miejscowosc_Stacja", value_name=f"Ilosc dni z przekroczeniem")

exceedance_days_file = os.path.join(out_path, "exceedance_days.csv")
exceedance_days.to_csv(exceedance_days_file, index=False)

grouped_bar = gbp.stworz_grouped_barplot(dfs_polaczone, zakres_lat)
grouped_bar.savefig(os.path.join(fig_dir, f"grouped_bar_{year}.png"), dpi=300, bbox_inches="tight")
plt.close(grouped_bar)

#----------------------------------------ZADANIE_5-------------------------------------------

przekroczenia_woj = gbp.policz_przekroczenia_woj(dfs_polaczone, metadane, zakres_lat)

woj_bar = gbp.stworz_barplot_przekroczenia_woj(przekroczenia_woj)
woj_bar.savefig(os.path.join(fig_dir, f"woj_bar_{year}.png"), dpi=300, bbox_inches="tight")
plt.close(woj_bar)















