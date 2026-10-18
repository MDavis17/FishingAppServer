import app.Catch.data_provider as data_provider


def delete_catch(catch_id: int, user_id: int):
    return data_provider.delete_catch(catch_id, user_id)
