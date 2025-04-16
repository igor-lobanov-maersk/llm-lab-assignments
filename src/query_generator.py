import os
import sqlalchemy
import json
import pandas as pd
import re

from string import Template
from openai import OpenAI

# this could have been generated from the schema, but foreign keys are not there
relationships = {
    "orders": [
        {
            "has_many": "order_items",
            "foreign_key": "order_id",
        },
        {
            "has_many": "order_payments",
            "foreign_key": "order_id",
        },
    ],
    "customers": [
        {
            "has_many": "orders",
            "foreign_key": "customer_id",
        },
    ],
    "sellers": [
        {
            "has_many": "orders",
            "foreign_key": "seller_id",
        },
    ],
}

class QueryGenerator:
    def __init__(self):
        self.engine = sqlalchemy.create_engine("sqlite:///./.data/olist.sqlite")
        self.metadata = sqlalchemy.MetaData()
        self.metadata.reflect(bind=self.engine)

        tables_info = []

        with self.engine.connect() as connection:
            for table_name, table in self.metadata.tables.items():
                rows_count = connection.execute(sqlalchemy.text(f"SELECT count(*) FROM {table_name}")).fetchone()[0]

                columns_info = []
                for column in table.columns:
                    # take 11 distinct values from the column
                    # if there are more than 10, then indicate that the list is only a sample
                    # otherwise, specify that the list contains all the values
                    # order values so that the schema is reproducible and we get cached prompts
                    rows = connection.execute(sqlalchemy.text(f"SELECT DISTINCT {column.name} FROM {table_name} WHERE {column.name} IS NOT NULL ORDER BY 1 LIMIT 11")).fetchall()
                    sample_values = [row[0] for row in rows]
                    sampling_result = {}
                    if len(sample_values) > 10:
                        sampling_result = {"sampleValue": sample_values[0]}
                    else:
                        sampling_result = {"distinctValues": sample_values}

                    # check if the column has null values
                    null_values = connection.execute(sqlalchemy.text(f"SELECT count(*) FROM {table_name} WHERE {column.name} IS NULL")).fetchone()[0]
                    sampling_result["nullable"] = null_values > 0

                    columns_info.append({
                        "columnName": column.name,
                        "type": str(column.type),
                        **sampling_result,
                    })
                
                tables_info.append({
                    "tableName": table_name,
                    "columns": columns_info,
                    "rowsCount": rows_count,
                    "relationships": relationships.get(table_name, []),
                })

        schema_json_string = json.dumps(tables_info, indent=2)

        with open(os.path.join(os.path.dirname(__file__), "prompt-template.md"), "r") as f:
            prompt_template = f.read()
            self.prompt = Template(prompt_template).safe_substitute(
                schema_json_string=schema_json_string
            )

        # dump schema to file if requested
        if os.getenv("DUMP_SCHEMA"):
            with open(".data/schema.json", "w") as f:
                f.write(schema_json_string)

        self.client = OpenAI()

    def make_query(self, question: str) -> pd.DataFrame:
        completion = self.client.chat.completions.create(
            model="gpt-4.1",
            store=False,
            messages=[
                {"role": "developer", "content": self.prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
        )

        query = completion.choices[0].message.content

        # remove Markdown
        if query.startswith("```sql"):
            query = query[len("```sql"):].strip()
        if query.endswith("```"):
            query = query[:-len("```")]

        print(f"Query: {query}")
        return pd.read_sql_query(query, self.engine)
