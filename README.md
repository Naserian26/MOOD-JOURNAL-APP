# Mood Journal – AI-Powered Emotion Tracker

## Overview
**Mood Journal** is a web application that allows users to **log their daily mood and journal entries**. It uses a PostgreSQL database and Flask backend to store users and journal data. Users can track their emotional patterns over time.  

This README documents **the work I did** to enhance and deploy the project.

---

## What I Did

1. **Database Column Updates**
   - Added new columns to the `user` table for premium subscription:
     - `is_premium` (BOOLEAN, default `False`)
     - `premium_expiry` (TIMESTAMP)
     - `email` (VARCHAR)
   - Added missing column `typed_mood` to `journal_entry` table.
   - Used **SQLAlchemy** with `db.engine.begin()` to alter the database safely.

2. **Flask Backend Fixes**
   - Fixed runtime errors related to missing columns (`email`, `typed_mood`) in the database.
   - Ensured SQLAlchemy database connection uses environment variable `DATABASE_URI`.

3. **Deployment**
   - Pushed all changes to GitHub.
   - Deployed the app on **Render**.
   - Verified that the live app works:  
     [Mood Journal Live]https://mood-journal-app-2-c9i5.onrender.com

4. **Environment Setup**
   - Used `.env` to store sensitive data like database URI.
   - Created a virtual environment `.venv` for dependencies.

5. **Manual Database Management**
   - Learned and applied **manual column additions** to avoid migration issues in production.
   - Ensured columns exist before running the app to prevent `ProgrammingError`.

---

## How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mood-journal.git
   cd mood-journal
