#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from sqlalchemy import MetaData
from sqlalchemy.exc import NoSuchTableError

from db_engine import DBEngine


class DatabaseClient(object):
    def __init__(self):
        self.engine = DBEngine.get()
        self.meta = MetaData()

    def _get_table(self, table_name):
        self.meta.reflect(bind=self.engine)
        table = self.meta.tables.get(table_name)
        if table is None:
            raise NoSuchTableError
        return table

    @staticmethod
    def _create_row_dict(row):
        return {
            "id": row["id"],
            "values": {k: v for k, v in row.items() if k != "id"}
        }

    def get_table_list(self):
        self.meta.reflect(bind=self.engine)
        return [str(table) for table in self.meta.tables]

    def create_table(self, table_name, columns):
        column_str = ["id serial PRIMARY KEY"]
        for column in columns:
            c = "{} {}".format(column.get("name"), column.get("type"))
            max_length = column.get("max_len")
            if max_length is not None:
                c += "({})".format(max_length)
            if not column.get("is_nullable", True):
                c += " NOT NULL"
            column_str.append(c)
        statement = "CREATE TABLE {} ({});".format(table_name, ", ".join(column_str))
        self.engine.execute(statement)
        return table_name

    def delete_table(self, table_name):
        table = self._get_table(table_name)
        table.drop(self.engine)
        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)

    def get_columns(self, table_name):
        table = self._get_table(table_name)
        columns = []
        for column in table.columns:
            data_type = str(column.type).split("(")[0]
            max_len = filter(str.isdigit, str(column.type))
            column_info = {
                "name": column.name,
                "type": data_type,
                "is_nullable": column.nullable
            }
            if max_len:
                column_info.update({"max_len": int(max_len)})
            columns.append(column_info)
        return columns

    def get_rows(self, table_name):
        table = self._get_table(table_name)
        statement = table.select()
        result = self.engine.execute(statement)
        rows = []
        for result in result:
            rows.append(self._create_row_dict(result))
        return rows

    def add_row(self, table_name, values_dict):
        table = self._get_table(table_name)
        statement = table.insert().values(**values_dict)
        result = self.engine.execute(statement)
        return {
            "id": result.inserted_primary_key[0]
        }

    def get_row(self, table_name, row_id):
        table = self._get_table(table_name)
        statement = table.select().where(table.c.id == row_id)
        row = self.engine.execute(statement).fetchone()
        if row:
            return self._create_row_dict(row)

    def delete_row(self, table_name, row_id):
        table = self._get_table(table_name)
        statement = table.delete().where(table.c.id == row_id)
        self.engine.execute(statement)

    def update_row(self, table_name, row_id, values_dict):
        table = self._get_table(table_name)
        statement = table.update().where(table.c.id == row_id).values(**values_dict)
        self.engine.execute(statement)
