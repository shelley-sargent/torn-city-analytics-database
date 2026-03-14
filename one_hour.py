import players.df as df
import psycopg2
import pandas as pd

'''
File set to run in cron every hour.
Uploads consistently changing invididual player stats to database.
'''

def upload(df):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
        print("✅ Database connected")
        cursor = conn.cursor()

        cols = list(df.columns)
        values = [tuple(x) for x in df.to_numpy()]

        update_cols = [col for col in cols if col not in ("player_id", "snapshot_date")]
        update_clause = ", ".join(
            [f"{col} = EXCLUDED.{col}" for col in update_cols]
        )

        query = f"""
            INSERT INTO player_stats_daily ({','.join(cols)})
            VALUES %s
            ON CONFLICT (player_id, snapshot_date) DO UPDATE SET {update_clause}
        """

        execute_values(cursor, query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ player_stats_daily updated successfully. {datetime.now()}")

    except Exception as e:
        print(f"❌ Database update failed: {e}")


upload(df)