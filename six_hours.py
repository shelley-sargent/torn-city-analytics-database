import api
import pandas as pd
import time
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime
from dotenv import load_dotenv
from attacks import full_attack_info as df

'''
File set to run in cron every six hours.
Focused on collecting data that must be updated more than once per day during high volume events
Currently focused on collecting faction attacks data from attacks.py
'''

load_dotenv()


# -- connect to database
def upload():
    try:
        conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
        )
        
        print("✅ Database connected")

        cursor = conn.cursor()

        cols = list(df.columns)
        print(df.head())
        print(cols)
        values = [tuple(x) for x in df.to_numpy()]

        update_cols = [col for col in cols if col != "id"]

        update_clause = ", ".join(
            [f"{col} = COALESCE(EXCLUDED.{col}, attacks.{col})" for col in update_cols]
        )

        query = f"""
                INSERT INTO attacks({','.join(cols)})
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET {update_clause}
        """

        execute_values(cursor, query, values)
        print(f"✅ Query executed successfully. {datetime.now()}")

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Connection closed successfully.")
    except Exception as e:
        print(f"❌ Database update failed: {e}")

upload()