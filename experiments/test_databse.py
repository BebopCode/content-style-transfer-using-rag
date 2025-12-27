from sqlalchemy import func
from .models import EmailDB
from .database import get_db


def get_top_10_senders(db):
    return (
        db.query(EmailDB.sender, func.count(EmailDB.id))
        .group_by(EmailDB.sender)
        .order_by(func.count(EmailDB.id).desc())
        .limit(10)
        .all()
    )


def get_top_10_receivers(db):
    return (
        db.query(EmailDB.receiver, func.count(EmailDB.id))
        .group_by(EmailDB.receiver)
        .order_by(func.count(EmailDB.id).desc())
        .limit(10)
        .all()
    )


if __name__ == "__main__":
    db = next(get_db())

    print("Top 10 Senders:", get_top_10_senders(db))
    print("Top 10 Receivers:", get_top_10_receivers(db))
