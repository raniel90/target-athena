"""Methods for writinig different object formats."""

import os
import csv
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import singer

LOGGER = singer.get_logger('target_athena')

def write_csv(filename, record, header=None, delimiter= ",", quotechar='"'):

    file_is_empty = (not os.path.isfile(filename)) or os.stat(
        filename
    ).st_size == 0
    
    if not header and not file_is_empty:
        with open(filename, "r") as csv_file:
            reader = csv.reader(
                csv_file, delimiter=delimiter, quotechar=quotechar
            )
            first_line = next(reader)
            header = (
                first_line if first_line else record.keys()
            )
    else:
        header = record.keys()

    # Athena does not support newline characters in CSV format.
    # Remove `\n` and replace with escaped text `\\n` ('\n')
    for k, v in record.items():
        if isinstance(v, str) and "\n" in v:
            record[k] = v.replace("\n", "\\n")

    with open(filename, "a") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            header,
            extrasaction="ignore",
            delimiter=delimiter,
            quotechar=quotechar,
        )
        if file_is_empty:
            writer.writeheader()

        writer.writerow(record)

def write_jsonl(filename, record):
    with open(filename, 'a', encoding='utf-8') as json_file:
        json_file.write(json.dumps(record, default=str) + '\n')


def write_parquet(record, parquet_metadata):
    df_normalized = pd.json_normalize(record)
    pa_table = pa.Table.from_pandas(df_normalized)
    parquet_metadata.get('writer').write_table(pa_table)
    
    del df_normalized


def get_parquet_metadata(filename, record):
    df_normalized = pd.json_normalize(record)
    pa_table = pa.Table.from_pandas(df_normalized)
    headers = df_normalized.columns.values.tolist()
    writer = pq.ParquetWriter(filename, pa_table.schema)
    
    del df_normalized

    return {
        'schema': pa_table.schema,
        'headers': headers,
        'writer': writer
    }
