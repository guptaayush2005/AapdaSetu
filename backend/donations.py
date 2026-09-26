from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime, timezone

router = APIRouter(tags=['Donations'])
DB_PATH = Path(__file__).with_name('donations.db')


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donation_id TEXT UNIQUE NOT NULL,
            donor_name TEXT NOT NULL,
            amount REAL NOT NULL,
            purpose TEXT NOT NULL,
            message TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    con.commit()
    con.close()


class DonationCreate(BaseModel):
    donor_name: str = Field(min_length=2, max_length=80)
    amount: float = Field(gt=0, le=10000000)
    purpose: str = Field(min_length=2, max_length=40)
    message: Optional[str] = Field(default=None, max_length=250)


@router.post('/donations')
def create_donation(payload: DonationCreate):
    init_db()
    donation_id = 'AS-DON-' + uuid.uuid4().hex[:8].upper()
    created_at = datetime.now(timezone.utc).isoformat()
    con = db()
    try:
        con.execute(
            '''INSERT INTO donations
               (donation_id, donor_name, amount, purpose, message, created_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (donation_id, payload.donor_name.strip(), payload.amount,
             payload.purpose.strip(), (payload.message or '').strip() or None,
             created_at)
        )
        con.commit()
    finally:
        con.close()
    return {
        'success': True,
        'donation_id': donation_id,
        'message': 'Thank you for supporting AapdaSetu relief.'
    }


@router.get('/donations')
def list_donations(limit: int = 50):
    init_db()
    limit = max(1, min(limit, 100))
    con = db()
    rows = con.execute(
        '''SELECT donation_id, donor_name, amount, purpose, message, created_at
           FROM donations ORDER BY id DESC LIMIT ?''', (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


@router.get('/donations/summary')
def donation_summary():
    init_db()
    con = db()
    row = con.execute(
        'SELECT COUNT(*) AS count, COALESCE(SUM(amount), 0) AS total FROM donations'
    ).fetchone()
    con.close()
    return {'donors': row['count'], 'total_amount': row['total']}


init_db()
