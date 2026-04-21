import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from django.conf import settings
from pathlib import Path


class DBConnection:
    def __init__(self):
        self._connect()

    def _connect(self):
        env_path = Path(settings.BASE_DIR).joinpath('.dbenv')
        load_dotenv(env_path, override=True)
        self.connection = psycopg2.connect(
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            cursor_factory=RealDictCursor,
        )

    def _format_uri(self):
        return (
            f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
    
    def _get_schema(self):
        cursor = self.connection.cursor()
        columns_query = """
        SELECT
            t.table_name,
            c.column_name
        FROM information_schema.tables t
        JOIN information_schema.columns c
            ON t.table_name = c.table_name
        WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position;
        """
        cursor.execute(columns_query)
        columns = cursor.fetchall()
        schema = dict()
        for column in columns:
            if column['table_name'] not in schema:
                schema[column['table_name']] = list()
            schema[column['table_name']].append(column['column_name'])
        return schema

    def _check_for_injection(self, query):
        invalid_char = ("--", "/*", "*/", "\\")
        if any(char in query.lower() for char in invalid_char):
            raise Exception(f'Injection character found in SQL Statement: {query}')

    def _check_for_ddl_and_dol(self, query):
        invalid_commands = ('create', 'update', 'insert', 'drop', 'delete', 'add')
        if any(command in query.lower() for command in invalid_commands):
            raise Exception(f'Invalid command found in SQL Statement: {query}')

    def _check_query(self, query):
        self._check_for_injection(query)
        self._check_for_ddl_and_dol(query)

    def query(self, query):
        cursor = self.connection.cursor()
        self._check_query(query)
        cursor.execute(query)
        results = cursor.fetchall()
        return [dict(row) for row in results]
        

if __name__ == '__main__':
    query = 'select * from actor limit 5;'
    db = DBConnection()
    # print(db._format_uri())
    # print(db._get_schema())
    db._check_query(query)
    print(db.query(query))
