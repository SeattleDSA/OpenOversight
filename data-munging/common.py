import logging
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests


log = logging.getLogger(__name__)


def write_files_with_missing(
    df: pd.DataFrame, missing: pd.DataFrame, output: Path
) -> None:
    """
    Write out two dataframes: one for the original data and one for the records which
    could not be matched to the missing data. The latter will be written to a file
    with the name "<output>__missing.csv"
    """
    missing_output = output.parent / f"{output.stem}__missing.csv"
    log.info(f"Writing {len(missing)} missing records to {missing_output}")
    missing.to_csv(missing_output, index=False)
    log.info(f"Writing {len(df)} output records to {output}")
    df.to_csv(output, index=False)
    log.info("Finished")


def nan_sting(value) -> str:
    """Create a string based off a value. If the value is NaN, return an empty string."""
    if value is None or (isinstance(value, (int, float)) and np.isnan(value)):
        return ""
    return value


def read_from_seattle_data_url(url: str, **kwargs) -> pd.DataFrame:
    """Read a CSV from the Seattle Data website"""
    log.info(f"Reading {url}")
    response = requests.get(url)
    buffer = StringIO(response.text)
    return pd.read_csv(buffer, **kwargs)
