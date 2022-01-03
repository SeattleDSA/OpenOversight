#!/usr/bin/env python
import json
import logging
from io import StringIO
from pathlib import Path
from typing import Dict

import click
import common
import numpy as np
import pandas as pd
import requests


log = logging.getLogger(__name__)

URL = "https://data.seattle.gov/api/views/99yi-dthu/rows.csv?accessType=DOWNLOAD"


def _nan(value):
    if value is None or (isinstance(value, (int, float)) and np.isnan(value)):
        return ""
    return value


def create_address(series):
    parts = [
        series["Incident Precinct"],
        series["Incident Sector"],
        series["Incident Beat"],
    ]
    parts = [part for part in parts if part]
    return " - ".join(parts)


def create_description(series):
    desc = f"""\
Source: {_nan(series.Source)}
Case Status: {_nan(series["Case Status"])}
"""
    subincident_count = len(series.Allegation)
    for idx in range(subincident_count):
        if subincident_count > 1:
            desc += f"\n==Report {idx + 1}=="
        desc += f"""
Badge Number: {series["badge number"][idx]}
Unique Id: {_nan(series["Unique Id"][idx])}
Allegation: {_nan(series["Allegation"][idx])}
Incident Type: {_nan(series["Incident Type"][idx])}
Disposition: {_nan(series["Disposition"][idx])}
Finding: {_nan(series["Finding"][idx])}
Discipline: {_nan(series["Discipline"][idx])}
"""
    return desc.strip()


def write_output(df: pd.DataFrame, output: Path, name: str) -> None:
    path = output.parent / f"{output.stem}__{name}.csv"
    log.info(f"Writing {len(df)} missing records to {path}")
    df.to_csv(path, index=False)


def match_incidents(ids: pd.DataFrame, nid_mapping: pd.DataFrame) -> pd.DataFrame:
    log.info("Fetching OPA data")
    response = requests.get(URL)
    buffer = StringIO(response.text)
    complaints = pd.read_csv(buffer, na_values="-")
    mapped = complaints.merge(nid_mapping, how="inner").drop_duplicates()
    log.info("Combining with OO IDs")
    with_ids = mapped.merge(
        ids[["id", "badge number"]],
        how="inner",
        left_on="ID #",
        right_on="badge number",
    )
    col_to_keep = [
        "Unique Id",
        "File Number",
        "Occurred Date",
        "Incident Precinct",
        "Incident Sector",
        "Incident Beat",
        "Source",
        "Incident Type",
        "Allegation",
        "Disposition",
        "Discipline",
        "Case Status",
        "Finding",
        "badge number",
        "id",
    ]
    list_cols = {
        "Incident Type",
        "Allegation",
        "Disposition",
        "Discipline",
        "Finding",
        "Unique Id",
        "badge number",
        "id",
    }
    col_to_agg = ["File Number", "Occurred Date"]
    log.info("Aggregating by OPA case")
    squished = (
        with_ids[col_to_keep]
        .groupby(col_to_agg)
        .agg(
            {
                col: (list if col in list_cols else "first")
                for col in (set(col_to_keep) - set(col_to_agg))
            }
        )
        .reset_index()
    )
    log.info("Formatting columns")
    squished.loc[:, "Occurred Date"] = pd.to_datetime(squished["Occurred Date"])
    squished["Address"] = squished.apply(create_address, axis=1)
    squished["Description"] = squished.apply(create_description, axis=1)
    log.info("Conforming to OO standard")
    reduced = squished[["File Number", "Occurred Date", "Address", "Description", "id"]]
    reduced["officer_ids"] = (
        reduced["id"].apply(lambda x: [str(y) for y in set(x)]).str.join("|")
    )
    reduced.columns = [
        "report_number",
        "date",
        "street_name",
        "description",
        "id",
        "officer_ids",
    ]
    reduced["id"] = reduced.apply(lambda r: f"#{r.name}", axis=1)
    reduced["department_name"] = "Seattle Police Department"
    reduced["city"] = "Seattle"
    reduced["state"] = "WA"
    final = reduced[reduced["date"] > "1950-01-01"]
    return final


def match_links(incidents: pd.DataFrame, opas: Dict[str, str]) -> pd.DataFrame:
    log.info("Merging OPA links with incident data")
    opa_links = pd.DataFrame(opas.items(), columns=["name", "url"])
    prep_merge = incidents[["report_number", "id", "officer_ids"]]
    prep_merge["name"] = prep_merge["report_number"].str.replace("OPA", "")
    matched_opas = opa_links.merge(prep_merge, how="inner", on="name")
    matched_opas = matched_opas[["url", "report_number", "id", "officer_ids"]]
    matched_opas.columns = ["url", "title", "incident_id", "officer_ids"]
    matched_opas["link_type"] = "Link"
    matched_opas["author"] = "Seattle Office of Police Accountability"
    matched_opas["id"] = None
    return matched_opas


def main(id_path: Path, mapping_path: Path, opa_link_path: Path, output: Path):
    log.info("Starting import")
    ids = pd.read_csv(id_path)
    named_employee_mapping = pd.read_csv(mapping_path)
    opa_links = json.loads(opa_link_path.read_text())
    incidents = match_incidents(ids, named_employee_mapping)
    links = match_links(incidents, opa_links)
    write_output(incidents, output, "incidents")
    write_output(links, output, "links")


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("mapping_path", type=click.Path(exists=True, path_type=Path))
@click.argument("opa_link_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, mapping_path: Path, opa_link_path: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, mapping_path, opa_link_path, output)


if __name__ == "__main__":
    cli()
