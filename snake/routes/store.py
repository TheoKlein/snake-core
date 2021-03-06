""" The store route module.

Attributes:
    StoreRoute (tuple): The StoreRoute.
"""

from webargs import tornadoparser

from snake import db
from snake import enums
from snake import fields
from snake import schema
from snake.core import snake_handler


# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class StoreSampleHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    async def get(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document:
            self.write_warning("store - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({'sample': document})
        self.finish()


class StoreHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args({
        # filter[field]: str
        'file_type': fields.Enum(type=enums.FileType, required=False, missing=None),
        'limit': fields.Int(required=False, missing=None),
        'operator': fields.Str(required=False, missing='and'),
        'order': fields.Int(required=False, missing=-1),
        'sort': fields.Str(required=False, missing=None)
    })
    async def get(self, data):
        documents = []
        filter_ = self.create_filter(self.request.arguments, data['operator'])
        if filter_:
            filter_ = {'$and': [filter_]}
            if data['file_type']:
                filter_['$and'] += [{'file_type': data['file_type']}]
        elif data['file_type']:
            filter_ = {'file_type': data['file_type']}
        cursor = db.async_file_collection.select_all(filter_, data['order'], data['sort'])
        index = 0
        while await cursor.fetch_next:
            if data['limit']:
                if index >= data['limit']:
                    break
                index += 1
            documents += [cursor.next_object()]

        documents = schema.FileSchema(many=True).dump(schema.FileSchema(many=True).load(documents))
        self.jsonify({'samples': documents})
        self.finish()


StoreSampleRoute = (r"/store/(?P<sha256_digest>[a-zA-Z0-9]+)?", StoreSampleHandler)  # pylint: disable=invalid-name
StoreRoute = (r"/store", StoreHandler)  # pylint: disable=invalid-name
