#!/usr/bin/env python
import logging
from pathlib import Path

import click
import numpy as np
import pandas as pd


log = logging.getLogger()


def main(id_path: Path, data: Path, output: Path):
    log.info("Starting import")
    df = pd.read_csv(data, usecols=["Name", "Base Pay", "Overtime"])
    df["last"] = df.Name.str.split(",").str[0]
    df["first"] = df.Name.str.split(",").str[1].str.split(" ").str[0]
    ids = pd.read_csv(
        id_path,
        usecols=["id", "first name", "last name"],
    )
    ids.columns = ["id", "last", "first"]
    merged = df.merge(ids, how="left", on=["last", "first"]).astype(
        {"id": pd.Int64Dtype()}
    )
    merged = merged[["Name", "Base Pay", "Overtime", "first", "last", "id"]]
    # Split off the links that don't have an OpenOversight badge associated with them
    _has_id = merged["id"].notna()
    missing = merged[~_has_id]
    missing_output = output.parent / f"{output.stem}__missing.csv"
    log.info(f"Writing {len(missing)} missing records to {missing_output}")
    missing.to_csv(missing_output, index=False)
    merged = merged[_has_id]
    merged = merged[["Base Pay", "Overtime", "id"]]
    merged.columns = ["salary", "overtime_pay", "officer_id"]
    merged["id"] = None
    merged["year"] = 2020
    merged = merged[~merged.officer_id.isna()]
    merged.loc[:, "salary"] = (
        merged["salary"].replace("[\$,]", "", regex=True).astype(float)
    )
    merged.loc[:, "overtime_pay"] = (
        merged["overtime_pay"]
        .replace("[\$, ]", "", regex=True)
        .replace("", np.nan)
        .astype(float)
    )
    log.info(f"Writing {len(merged)} output records to {output}")
    merged.to_csv(output, index=False)
    log.info("Finished")


@click.command()
@click.argument("id_path", type=click.Path(exists=True, path_type=Path))
@click.argument("data", type=click.Path(exists=True, path_type=Path))
@click.argument("output", type=click.Path(path_type=Path))
def cli(id_path: Path, data: Path, output: Path):
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(lineno)3d][%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    main(id_path, data, output)


if __name__ == "__main__":
    cli()
