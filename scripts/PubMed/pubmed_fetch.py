import pubmed_funkcje as fun

import yaml
import argparse
import os
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument ("--year", type=int, required=True)
parser.add_argument("--config",  required=True)

args = parser.parse_args()
year = args.year
config_path = args.config

with open(config_path) as f:
    config = yaml.safe_load(f)

cfg = config["PubMed_search_params"]

out_dir = f'results/literature/{year}'

pubmed_data = fun.dl_papers(year, cfg)

#-------------------------------------PUBLIKACJE_DO_PLIKU------------------------------------

pubmed_papers = pubmed_data.iloc[:, :-2]
papers_file = os.path.join(out_dir, "pubmed_papers.csv")
pubmed_papers.to_csv(papers_file, index=False)

#------------------------------------------SUMMARY------------------------------------------

summary_by_year = fun.make_summary_by_year(pubmed_data)

summary_file = os.path.join(out_dir, "summary_by_year.csv")
summary_by_year.to_csv(summary_file, index=False)

#-------------------------------------TOP_10_JOURNALS---------------------------------------

top_journals = fun.top_n_journals(pubmed_data, cfg)

top_journals_file = os.path.join(out_dir, "top_journals.csv")
top_journals.to_csv(top_journals_file, index=False)

#-------------------------------------BARPLOT---------------------------------------

papers_barplot = fun.summary_barplot(summary_by_year, year)
papers_barplot.savefig(os.path.join(out_dir, f"papers_per_year.png"), dpi=300, bbox_inches="tight")
plt.close(papers_barplot)


