import logging
from abc import ABC, abstractmethod

import pandas as pd
import sqlite3
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('revol_ver')


class OutputsDB:
    def __init__(self, db_file: str):
        self.conn = self.connect_to_db(db_file)

    def connect_to_db(self, db_file: str) -> sqlite3.Connection:
        c = sqlite3.connect(db_file)
        logger.info(f'Connected to database: {c}')
        return c

    def to_db(self, trans: list[dict]) -> None:
        df = pd.DataFrame(trans)
        result = df.to_sql('raw_transactions', self.conn, if_exists='append', index=False)
        logger.info(f'Saved {result} records to DB!')

    def read_existing_records(self) -> list[str]:
        '''
        Returns list of legIds which should be global unique and
        are used to avoid writing duplicated values to outputs
        '''
        try:
            df = pd.read_sql('SELECT legId FROM raw_transactions', self.conn)
        except pd.errors.DatabaseError:
            logger.warning('Cannot find database file, will create new.')
            return []
        return df['legId'].tolist()


class FileOutput(ABC):
    file_extension: str

    @classmethod
    def _generate_filename(cls, date_arg: str, period: str) -> str:
        if period == 'all':
            date = period
        else:
            date = 'month_' + date_arg.replace('.', '_')
        now = re.sub(r'\W', '_', str(datetime.now()))
        return f'{now}_export_{date}.{cls.file_extension}'

    @classmethod
    def _generate_dataframe_and_location(cls, trans: list[dict], date_arg: str,
                                         period: str, path: Path) -> tuple[pd.DataFrame, Path]:
        filename = cls._generate_filename(date_arg, period)
        df = pd.DataFrame(trans)
        file_location = path / 'exports' / filename
        return df, file_location

    @classmethod
    @abstractmethod
    def to_file(cls, trans: list[dict], date_arg: str, period: str, path: Path) -> None:
        raise NotImplementedError()


class OutputsExcel(FileOutput):
    file_extension = 'xlsx'

    @classmethod
    def to_file(cls, trans: list[dict], date_arg: str, period: str, path: Path) -> None:
        df, file_location = cls._generate_dataframe_and_location(trans, date_arg, period, path)
        df.to_excel(file_location, index=False)
        logger.info(f'Saved {len(df)} rows to Excel file {file_location}')


class OutputsCsv(FileOutput):
    file_extension = 'csv'

    @classmethod
    def to_file(cls, trans: list[dict], date_arg: str, period: str, path: Path) -> None:
        df, file_location = cls._generate_dataframe_and_location(trans, date_arg, period, path)
        df.to_csv(file_location, index=False)
        logger.info(f'Saved {len(df)} rows to CSV file {file_location}')
