from app.mock_database.mock_db import catches_db

def delete_catch(catch_id: int):
    global catches_db
    for i, catch in enumerate(catches_db):
        if catch.id == catch_id:
            del catches_db[i]
            return True
    return False
