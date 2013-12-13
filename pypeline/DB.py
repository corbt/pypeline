import json
import plyvel

class DB:
    def __init__(self, database_path, create_if_missing=False):
        self.db=plyvel.DB(database_path, 
            create_if_missing=create_if_missing)

        self.collections_set=self.db.prefixed_db(b'collections/')
        self.collection_items_set=self.db.prefixed_db(b'collection-items/')

    def collection(self, collection_name):
        data = self.collections_set.get(collection_name)
        if data == None:
            self.collections_set.put(collection_name, 'true')

        return Collection(self.collection_items_set, collection_name)

    def collections(self):
        collections = []
        for name, value in self.collections_set:
            collections.append(Collection(self.collection_items_set, name))

        return collections

    def close(self):
        self.db.close()

    def open(self):
        self.db.open()

class Collection:
    def __init__(self, items_set, name):
        if '!!' in name:
            raise ValueError("Disallowed character sequence '!!' in collection name")

        self.name = name
        self.db = items_set.prefixed_db(name+b'!!')

        self.length = 0
        last_instance = '0'
        for key in self.db.iterator(include_value=False):
            length += 1
            last_instance = key
            print last_instance

        self.last_index = 0

    def append(self, record):
        self.db.put(str(self.last_index), json.dumps(record))
        self.last_index += 1
        if self.length:
            self.length += 1

    def __iter__(self):
        return Iterator(self.db.iterator(include_key=False))

    def __getitem__(self, key):
        pass

    def __setitem__(self, key):
        pass

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.name)

    def __len__(self):
        return self.length

class Iterator:
    def __init__(self, base_iterator):
        self.base_iterator = base_iterator

    def __iter__(self):
        return self

    def next(self):
        return json.loads(self.base_iterator.next())