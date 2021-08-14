#!/usr/bin/env python
from pathlib import Path

import click
import pandas as pd


def main(id_path: Path, link_path: Path, output: Path):
    ids = pd.read_csv(id_path, usecols=["id", "badge number"])
    links = pd.read_csv(link_path)
    # Collapse the multiple links columns into a single column list
    links["url"] = (
        links[["Links", "last updated: 8/6/2021", "Unnamed: 6"]].values.tolist().head()
    )
    # Make the badge column a string
    links["badge number"] = links["Badge Number"].astype(str)
    # Subset the columns at this point
    links = links[["badge number", "url"]]
    # Explode the list of links into individual rows
    links = links.explode("url", ignore_index=True)
    # Drop any rows where a link doesn't exist (this will be most)
    links = links[links["url"].notna()]
    # Join the two dataframes on badge number, discard any rows with missing values
    merged = links.merge(ids, how="inner").astype({"id": pd.Int64Dtype()})[["id", "url"]]
    # Rename id to "officer_ids", used in importer:
    # https://openoversight.readthedocs.io/en/latest/advanced_csv_import.html#links-csv
    merged.columns = ["officer_ids", "url"]
    # Add the extra column info
    merged["title"] = "Divest SPD Twitter thread"
    merged["link_type"] = "Link"
    merged["author"] = "Divest SPD"
    merged.to_csv(output, index=False)
