class BaseRepository:
    def __init__(self, db, collection_name: str):
        self.collection = db[collection_name]