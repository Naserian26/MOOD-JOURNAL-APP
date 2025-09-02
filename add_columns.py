from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import text
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

with app.app_context():
    with db.engine.begin() as conn:  # begin() handles commit automatically
        # Add columns to "user" table
        conn.execute(
            text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE;')
        )
        conn.execute(
            text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS premium_expiry TIMESTAMP;')
        )
        conn.execute(
            text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email VARCHAR(255);')
        )

        # Add typed_mood column to journal_entry table
        conn.execute(
            text('ALTER TABLE journal_entry ADD COLUMN IF NOT EXISTS typed_mood VARCHAR(255);')
        )

    print("All columns added successfully")
