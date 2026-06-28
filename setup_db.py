"""Run once to create tables and seed data."""
import psycopg2, pathlib, os

conn = psycopg2.connect(
    f"postgresql://postgres.aeukqvuiatderruqlphr:{os.environ['DB_PASS']}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
)
conn.autocommit = True
cur = conn.cursor()
sql = pathlib.Path("schema.sql").read_text()
cur.execute(sql)
print("Done.")
cur.close()
conn.close()
