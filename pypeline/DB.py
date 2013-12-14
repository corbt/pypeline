import json
import plyvel

class DB:
    def __init__(self, database_path, create_if_missing=False):
        self.db=plyvel.DB(database_path, 
            create_if_missing=create_if_missing)

        self.collections_set=self.db.prefixed_db(b'collections/')
        self.collection_items_set=self.db.prefixed_db(b'collection-items/')
        self.collections_cache = {}

    def collection(self, collection_name, create_if_missing=True, error_if_exists=False):
        if collection_name not in self.collections_cache:
            data = self.collections_set.get(collection_name)
            if data == None:
                if create_if_missing == False:
                    raise ValueError("Collection '{0}' does not exist".format(collection_name))
                self.collections_set.put(collection_name, 'true')
            self.collections_cache[collection_name] = Collection(self.collection_items_set, collection_name)
        elif error_if_exists:
            raise ValueError("Collection '{0}' already exists".format(collection_name))

        return self.collections_cache[collection_name]

    def collections(self):
        for name in self.collections_set.iterator(include_value=False):
            if name not in self.collections_cache:
                self.collections_cache[name] = Collection(self.collection_items_set, name)

        return [value for value in self.collections_cache.itervalues()]

    def copy_collection(self, old_collection, new_collection):
        old = self.collection(old_collection, create_if_missing=False)
        new = self.collection(new_collection, error_if_exists=True)
        for entry in old:
            new.append(entry)
        return new

    def delete(self, collection_name):
        self.collection(collection_name).delete_all()
        self.collections_set.delete(collection_name)
        del self.collections_cache[collection_name]

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

        self.refresh()

    def append(self, record):
        self.last_index += 1
        key = str(self.last_index)
        self.db.put(key, json.dumps(record))
        self.keys.append(key)

    def refresh(self):
        self.keys = []
        for key in self.db.iterator(include_value=False):
            self.keys.append(key)

        if len(self.keys) > 0:
            self.last_index = int(self.keys[-1])
        else:
            self.last_index = 0

    def delete(self, index):
        self.db.delete(self.keys[index])
        self.keys.pop(index)

    def delete_all(self):
        for key in self.keys:
            self.db.delete(key)

    def __iter__(self):
        return Iterator(self.db.iterator(include_key=False))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [json.loads(self.db.get(key)) for key in self.keys[key]]
        else:
            return json.loads(self.db.get(self.keys[key]))

    def __setitem__(self, key, value):
        self.db.put(self.keys[key], json.dumps(value))

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.name)

    def __len__(self):
        return len(self.keys)

class Iterator:
    def __init__(self, base_iterator):
        self.base_iterator = base_iterator

    def __iter__(self):
        return self

    def next(self):
        return json.loads(self.base_iterator.next())