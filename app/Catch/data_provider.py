from sqlalchemy.orm import Session

import app.PersonalBests.service as personal_best_service
from app.models.db_models import CatchEntry as CatchRow


def delete_catch(db: Session, catch_id: int, user_id: int):
    row = (
        db.query(CatchRow)
        .filter(CatchRow.id == catch_id, CatchRow.user_id == user_id)
        .first()
    )
    if row is None:
        return False
    species_name = row.species
    species_pairs = personal_best_service.species_pairs_for_deleted_pb_catches(
        db, user_id, [catch_id]
    )
    db.delete(row)
    db.commit()
    personal_best_service.recompute_after_catch_deletes(
        db, user_id, [catch_id], species_pairs
    )
    personal_best_service.recompute_historical_pb_flags_for_species(
        db, user_id, species_name
    )
    return True
