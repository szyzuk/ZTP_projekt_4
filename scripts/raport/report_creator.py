import raport_funkcje as fun

import argparse
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument("--years", nargs="+", type=int, required=True)
parser.add_argument("--output", type=str, required=True)
args = parser.parse_args()

##fig_path = Path("results/report_misc/")
##fig_path.parent.mkdir(parents=True, exist_ok=True)
fig_path = "results/report_misc"

#years = json.loads(args.years)
years = args.years

#(1) Dni z przekorczeniem
df_ex_days = fun.combine_exceedence_days(years)

#(2) "Literatura"
df_literature = fun.combine_literature(years)

#(3) Ile publications dla query
df_query_hits = fun.combine_summary_by_year(years)

#(4) Trend liczby publikacji w czasie
fig_trend = fun.trend_ppublish(years)

fig_trend.savefig(f'{fig_path}/trend_line.png', dpi=300, bbox_inches="tight")
plt.close(fig_trend)

#(5) Top czasopisma
df_top_journals = fun.combine_top_journals(years)

#(6) Przykładowe tytuły
fig_titles = fun.example_titles(years, 2)

fig_titles.savefig(f'{fig_path}/example_titles.png', dpi=300, bbox_inches="tight")
plt.close(fig_titles)


with open(args.output, "w", encoding="utf-8") as f:
    f.write("# Raport task 4\n\n")
    #(1)
    f.write("## Zestawienie exceedance_days dla wszystkich lat\n\n")
    f.write("Dla każdej stacji w kolumnie oznaczonej odpowiednim rokiem, przedstawiono liczbę dni w których wystąpiło przekroczenie średniej dobowej normy stężenia PM2.5 (15 µg/m³).\n\n")
    f.write("Zostały przedstwione tylko dane stacji dla których istniały pomiary z całego zakresu lat\n\n")
    f.write(fun.df_to_markdown(df_ex_days))
    f.write("\n\n")
    #(2)
    f.write("## Literatura\n\n")
    f.write("Przykładowe publikacje, 10 z każddego roku\n\n")
    f.write(fun.df_to_markdown(df_literature))
    f.write("\n\n")
    #(3)
    f.write("## Liczba publikacji znalezionych dla zadanych zapytań\n\n")
    f.write("Dla każdego zapytania, liczba znalezionych artykułow opublikowanych w danym roku\n\n")
    f.write(fun.df_to_markdown(df_query_hits))
    f.write("\n\n")
    #(4)
    f.write("## Trend liczby publikacji printów\n\n")
    f.write(f"![Linia trendu publikacji]({fig_path}/trend_line.png)\n")
    #(5)
    f.write("## Czasopisma z top 10 ilością publikacji w danych latach\n")
    f.write("Dla każdego czasopisma, przedstawiona: łączna liczba artykułów, liczba artykułów w poszczególnych latach\n\n")
    f.write(fun.df_to_markdown(df_top_journals))
    f.write("\n\n")
    #(6)
    f.write("## Przykładowe tytuły znalezionych publikacji\n\n")
    f.write(f"![Przykładowe tytuły publikacji]({fig_path}/example_titles.png)\n")