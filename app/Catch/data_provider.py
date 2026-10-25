from sqlalchemy.orm import Session

from app.models.db_models import CatchEntry as CatchRow


def delete_catch(db: Session, catch_id: int, user_id: int):
    row = (
        db.query(CatchRow)
        .filter(CatchRow.id == catch_id, CatchRow.user_id == user_id)
        .first()
    )
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
