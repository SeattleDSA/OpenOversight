#!/usr/bin/env python
"""
FIXME
Assignment Creation Script.

This script takes the historic SPD data and converts it into two new CSVs: a list of
officers currently missing from OpenOversight, and a list of assignments for all
officers. The missing officers are all officers who were not part of the 2021-06-30
roster and were on the force prior to 2020.

The original upload included some assignment/job information. *That data will need to be
deleted before this insertion can run!!*. The following is the SQL needed to accomplish
this:

DELETE FROM assignments WHERE department_id = 1;
DELETE FROM jobs WHERE department_id = 1;

Alternatively, if there are no other departments to worry about:
TRUNCATE jobs, assignments RESTART IDENTITY;

Additionally, the now-defunct units can be removed with the following command:
DELETE FROM unit_types WHERE id IN (
    SELECT u.id
    FROM unit_types u
    LEFT JOIN assignments a
        ON u.id = a.unit_id
        WHERE a.id IS NULL
);
"""
import logging
from functools import partial
from pathlib import Path
from typing import NamedTuple

import click
import pandas as pd

import assignments as assignments_module
import first_employed_date as first_employed_date_module
import spd_2021_salary_data as spd_2021_salary_data_module
import demographic_data as demographic_module


log = logging.getLogger(__name__)


class DataFiles(NamedTuple):
    oo_officers: Path
    historical_roster: Path
    spd_2021_salary: str = (
        "https://data.seattle.gov/api/views/2khk-5ukd/rows.csv?accessType=DOWNLOAD"
    )
    demographic_data: str = (
        "https://data.seattle.gov/api/views/i2q9-thny/rows.csv?accessType=DOWNLOAD"
    )


def _data_path(csv_name: str) -> click.command:
    return click.argument(csv_name, type=click.Path(exists=True, path_type=Path))


def _output_data(df: pd.DataFrame, output: Path, name: str) -> None:
    path = output.parent / f"{output.stem}__{name}.csv"
    log.info(f"Writing {name} data to {path}")
    df.to_csv(path, index=False)


def main(files: DataFiles, output: Path):
    log.info("Starting import")
    officers = pd.read_csv(files.oo_officers)
    hist = pd.read_csv(files.historical_roster, low_memory=False)
    # Compute assignments and any new officers
    log.info("Computing assignments and new officers")
    assignments, new_officers = assignments_module.extract_all_assignments(
        officers[["id", "badge number"]].copy(), hist
    )
    log.info("Computing first employed date")
    # For new officers, compute the first employed date
    first_employed_date = first_employed_date_module.get_first_employed(
        assignments.copy(), space_in_name=False
    )
    new_officers = new_officers.merge(
        first_employed_date, on=["id", "department_name"], how="left"
    )
    ids_for_salary = new_officers[["id", "last_name", "first_name"]].copy()
    log.info("Computing 2021 salary")
    salary_2021, _ = spd_2021_salary_data_module.match_salary_data(
        ids=ids_for_salary,
        url=files.spd_2021_salary,
        convert_id=False,
    )
    # The new officers don't include badge numbers (those are populated by
    # assignments), so we need to temporarily add it here
    log.info("Computing demographics")
    demo_match = new_officers.copy()
    demo_match["badge number"] = new_officers["id"].str.strip("#")
    demographics, _ = demographic_module.match_demographics(
        ids=demo_match,
        url=files.demographic_data,
        convert_badge=False,
    )
    new_officers = new_officers.merge(
        demographics, on=["id", "department_name"], how="left"
    )
    log.info("Writing output files")
    _output_data(new_officers, output, "officers")
    _output_data(assignments, output, "assignments")
    _output_data(salary_2021, output, "salary_2021")


@click.command()
@_data_path("oo_officers")
@_data_path("historical_roster")
@click.argument("output", type=click.Path(path_type=Path))
def cli(
    oo_officers: Path,
    historical_roster: Path,
    output: Path,
):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    files = DataFiles(
        oo_officers=oo_officers,
        historical_roster=historical_roster,
    )
    main(files, output)


if __name__ == "__main__":
    cli()
