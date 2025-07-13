from collections import Counter
import app.Catch.data_provider as data_provider
from typing import List


def delete_catch(catch_id: int):
    return data_provider.delete_catch(catch_id)
