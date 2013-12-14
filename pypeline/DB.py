import json
import copy
import random
from functools import reduce
import plyvel

class DB:
    def __init__(self, database_path, create_if_missing=False):
        self.db=plyvel.DB(database_path, 
            create_if_missing=create_if_missing)

        self.collections_set=self.db.prefixed_db(b'collections/')
        self.collection_items_set=self.db.prefixed_db(b'collection-items/')
        self.collections_cache = {}

    def collection(self, collection_name, reset_collection=False, create_if_missing=True, error_if_exists=False):
        if collection_name not in self.collections_cache:
            data = self.collections_set.get(collection_name.encode())
            if data == None:
                if create_if_missing == False:
                    raise ValueError("Collection '{0}' does not exist".format(collection_name))
                self.collections_set.put(collection_name.encode(), b'true')
            self.collections_cache[collection_name] = Collection(self, self.collection_items_set, collection_name)
        elif error_if_exists:
            raise ValueError("Collection '{0}' already exists".format(collection_name))

        if reset_collection:
            self.collections_cache[collection_name].delete_all()

        return self.collections_cache[collection_name]

    def collections(self):
        for name in self.collections_set.iterator(include_value=False):
            if name.decode() not in self.collections_cache:
                self.collections_cache[name.decode()] = Collection(self, self.collection_items_set, name.decode())

        return [value for value in self.collections_cache.values()]

    def copy_collection(self, old_collection, new_collection, start=None, end=None, **kwargs):
        old = self.collection(old_collection, create_if_missing=False)
        new = self.collection(new_collection, reset_collection=True, **kwargs)
        new.append_all(old.iterator(start, end))

        return new

    def delete(self, collection_name):
        self.collection(collection_name).delete_all()
        self.collections_set.delete(collection_name.encode())
        del self.collections_cache[collection_name]

    def close(self):
        self.db.close()

    def open(self):
        self.db.open()

class Collection:
    def __init__(self, database, items_set, name):
        if '!!' in name:
            raise ValueError("Disallowed character sequence '!!' in collection name")

        self.name = name
        self.db = items_set.prefixed_db(name.encode()+b'!!')
        self.parent_db = database

        self.refresh()

    def append(self, record):
        self.last_index += 1
        key = str(self.last_index).encode()
        self.db.put(key, self.encode(record))
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
        self.keys = []
        self.last_index = 0

    def append_all(self, iterable):
        for instance in iterable:
            self.append(instance)

    def map(self, function, new_collection, **kwargs):
        collection = None
        if new_collection in [None, self.name]:
            collection = self
            for key in self.keys:
                new_value = function(self.decode(self.db.get(key)))
                self.db.put(key, self.encode(new_value))
        else:
            collection = self.parent_db.collection(new_collection, reset_collection=True, **kwargs)
            for instance in self:
                collection.append(function(instance))

        return collection

    def filter(self, function, new_collection, **kwargs):
        collection = None
        if new_collection in [None, self.name]:
            collection = self
            new_keys = []
            for key in self.keys:
                if function(self.decode(self.db.get(key))):
                    new_keys.append(key)
                else:
                    self.db.delete(key)
            self.keys = new_keys

        else:
            collection = self.parent_db.collection(new_collection, reset_collection=True, **kwargs)
            for instance in self:
                if function(instance):
                    collection.append(instance)

        return collection

    def reduce(self, function, new_collection, initializer=None, **kwargs):
        reduced = None
        if initializer != None:
            reduced = reduce(function, self.iterator(), initializer)
        else:
            reduced = reduce(function, self.iterator())

        collection = None
        if new_collection in [None, self.name]:
            collection = self
        else:
            collection = self.parent_db.collection(new_collection, reset_collection=True, **kwargs)
        
        collection.append(reduced)
        return collection

    def random_subset(self, number, new_collection, **kwargs):
        collection = None
        if new_collection in [None, self.name]:
            collection = self
            random.shuffle(self.keys)
            for key in self.keys[number:]:
                self.db.delete(key)
            self.keys = self.keys[:number]
            list.sort(self.keys)

        else:
            new_keys = copy.copy(self.keys)
            random.shuffle(new_keys)
            new_keys = new_keys[:number]
            list.sort(new_keys)
            collection = self.parent_db.collection(new_collection, **kwargs)
            collection.delete_all()
            for key in new_keys:
                collection.append(self.decode(self.db.get(key)))

        return collection


    def iterator(self, start=None, end=None):
        return Iterator(self, start, end)

    @staticmethod
    def encode(obj):
        return json.dumps(obj).encode()

    @staticmethod
    def decode(string):
        return json.loads(string.decode())

    def __iter__(self):
        return self.iterator()

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self.decode(self.db.get(key)) for key in self.keys[key]]
        else:
            return self.decode(self.db.get(self.keys[key]))

    def __setitem__(self, key, value):
        self.db.put(self.keys[key], json.dumps(value).encode())

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.name)

    def __len__(self):
        return len(self.keys)

class Iterator:
    def __init__(self, collection, start=None, end=None):
        self.key_iterator = iter(collection.keys[start:end])
        self.collection = collection

    def __iter__(self):
        return self

    def next(self):
        return json.loads(self.collection.db.get(self.key_iterator.next()).decode())

    def __next__(self):
        return json.loads(self.collection.db.get(self.key_iterator.__next__()).decode())
