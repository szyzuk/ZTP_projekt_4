import yaml

configfile: "config/task4.yaml"

YEARS = config["years"]

rule all:
    input:
        # PM2.5
        expand("results/pm25/{Y}/exceedance_days.csv",Y=YEARS),
        # PubMed
        expand("results/literature/{Y}/pubmed_papers.csv",Y=YEARS),
        expand("results/literature/{Y}/summary_by_year.csv",Y=YEARS),
        expand("results/literature/{Y}/top_journals.csv",Y=YEARS),
        # Raport końcowy
        "results/report_task4.md"


with open("config/pm25.yaml") as f:
    pm25_config = yaml.safe_load(f)

rule pm25_year:
    input:
        config="config/pm25.yaml"
    output:
        exceedance_days = "results/pm25/{Y}/exceedance_days.csv",
    conda:
        "env.yaml"
    shell:
        """
            mkdir -p results/pm25/{wildcards.Y}/figures
            python3 scripts/PM2,5/main.py \
                --year {wildcards.Y} \
                --config config/pm25.yaml \
        """


with open("config/pubmed.yaml") as f:
    pubmed_config = yaml.safe_load(f)

rule pubmed_year:
    input:
       config="config/pubmed.yaml"
    output:
        papers="results/literature/{Y}/pubmed_papers.csv",
        summary="results/literature/{Y}/summary_by_year.csv",
        top="results/literature/{Y}/top_journals.csv"
    conda:
        "env.yaml"
    shell:
        """
            mkdir -p results/literature/{wildcards.Y}
            python3 scripts/PubMed/pubmed_fetch.py \
                --year {wildcards.Y} \
                --config config/pubmed.yaml \
        """


rule report_task4:
    input:
        exceedance_days=expand("results/pm25/{Y}/exceedance_days.csv",Y=YEARS),
        papers=expand("results/literature/{Y}/pubmed_papers.csv",Y=YEARS),
        summary=expand("results/literature/{Y}/summary_by_year.csv",Y=YEARS),
        top=expand("results/literature/{Y}/top_journals.csv",Y=YEARS),
        config="config/task4.yaml"
    output:
        "results/report_task4.md"
    params:
        years=YEARS
    shell:
        """
        mkdir -p results/report_misc
        python3 scripts/raport/report_creator.py \
            --years {params.years} \
            --output {output}
        """
