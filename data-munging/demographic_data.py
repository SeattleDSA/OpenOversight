#!/usr/bin/env python
import logging
from pathlib import Path

import click
import pandas as pd


log = logging.getLogger()


def main(id_path: Path, demographic_path: Path, output: Path):
    log.info("Starting import")
    ids = pd.read_csv(id_path, usecols=["id", "badge number"])
    demo = pd.read_csv(
        demographic_path,
        usecols=[
            "Officer ID",
            "Officer Gender",
            "Officer Race",
            "Officer Year of Birth",
        ],
    )
    # Join the two dataframes on badge number
    demo.columns = ["badge", "gender", "race", "dob"]
    demo = demo.drop_duplicates()
    demo.loc[:, "gender"] = demo["gender"].astype("category")
    demo.loc[:, "gender"] = demo["gender"].cat.rename_categories({"N": "Other"})
    races = {
        "White": "WHITE",
        "Asian": "ASIAN",
        "Black or African American": "BLACK",
        "American Indian/Alaska Native": "NATIVE AMERICAN",
        "Nat Hawaiian/Oth Pac Islander": "PACIFIC ISLANDER",
        "Hispanic or Latino": "HISPANIC",
        "Two or More Races": "Other",
        "Not Specified": None,
        "Unknown": None,
    }
    demo.loc[:, "race"] = demo["race"].replace(races)
    demo.loc[:, "dob"] = demo["dob"].str[:4].astype(int)
    demo.loc[:, "badge"] = demo["badge"].str.strip()
    merged = demo.merge(
        ids, how="left", left_on="badge", right_on="badge number"
    ).astype({"id": pd.Int64Dtype()})
    merged = merged[["id", "gender", "race", "dob"]]
    # Rename columns, add required
    # https://openoversight.readthedocs.io/en/latest/advanced_csv_import.html#officers-csv
    merged.columns = ["id", "gender", "race", "birth_year"]
    # Split off the links that don't have an OpenOversight badge associated with them
    _has_id = merged["id"].notna()
    missing = merged[~_has_id]
    # Remove those missing urls
    merged = merged[_has_id]
    # Add the extra column info
    merged["department_name"] = "Seattle Police Department"
    missing_output = output.parent / f"{output.stem}__missing.csv"
    log.info(f"Writing {len(missing)} missing records to {missing_output}")
    missing.to_csv(missing_output, index=False)
    log.info(f"Writing {len(merged)} output records to {output}")
    merged.to_csv(output, index=False)
    log.info("Finished")


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("demographic_path", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, demographic_path: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, demographic_path, output)


if __name__ == "__main__":
    cli()
