import plyvel

db = plyvel.DB("testdb", create_if_missing=True)
# db.put("key", "value")

prefixed = db.prefixed_db("pre-")
p2 = prefixed.prefixed_db("p2")
for key, value in prefixed:
    print key, value

print db.get('key')

# for key, value in db:
#   print key, value

# with db.write_batch() as wb:
#     test = 5
#     for i in xrange(1000000):
#         # test = test + 1
#         wb.put(bytes(i), bytes(i)*100)