# Langchain Libraries
from langchain_community.llms import LlamaCpp
from langchain_text_splitters import TokenTextSplitter
from langchain_community.utilities import SQLDatabase

# Project Modules
from .database import DBConnection

# Built in libraries
from datetime import datetime
import json
import re


class ChatBot:
    def __init__(self):
        """
        """
        self.llm = self._create_llm()
        
    def _create_llm(self):
        """
        """
        return LlamaCpp(
            model_path='/models/google_gemma_3_4b_it_Q6_K.gguf',
            temperature=0.7,
            max_tokens=512,
            n_ctx=4096,
            verbose=False,
            stop=['<end_of_turn>',]
        )

    def _process_schema(self, query):
        schema = DBConnection()._get_schema()
        schema_prompt = f'''<start_of_turn>user
            Extract the relevant table names from the schema.

            Schema:
            {schema}

            Question:
            {query}

            Return JSON:
            {{"table_names": []}}
            <end_of_turn>
            <start_of_turn>model
        '''
        result = self.llm.invoke(schema_prompt).strip()
        result = self._process_result(result, 'json')
        return result

    def _get_sql_query(self, query):
        tables_dict = self._process_schema(query)
        db = SQLDatabase.from_uri(DBConnection()._format_uri())
        schema = db.get_table_info(table_names=tables_dict['table_names'])
        prompt = f'''<start_of_turn>user
        Generate the PostgreSQL query to answer the question.
        Use "ILIKE" always instead of "LIKE".

        Schema:
        {schema}

        Question:
        {query}

        Return SQL:
        <end_of_turn>user
        <start_of_turn>model
        '''
        result = self.llm.invoke(prompt)
        result = self._process_result(result, 'sql')
        return result

    def _process_result(self, result, data_type):
        if data_type in result.strip().lower():
            pattern = rf'```{data_type}\s*(.*?)\s*```'
            result = re.search(pattern, result, re.DOTALL)
            if result:
                result = result.group(1)
        if data_type == 'json':
            result = json.loads(result)
        return result

    def query(self, query):
        sql = self._get_sql_query(query)
        results = DBConnection().query(sql)
        return results, sql


if __name__ == '__main__':
    bot = ChatBot()
    query = 'give me the first and last name of all actors whose first name starts with "M".'
    # bot._get_sql_query(query)
    # print(bot._process_schema(query))
    # print(bot._get_sql_query(query))
    # print(bot.query(query))

    