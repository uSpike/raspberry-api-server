
from flask_restplus import Resource, Namespace, reqparse, fields, marshal_with

from .gpio import GPIO

api = Namespace('version')

version_model = api.model('version', {
    'product': fields.String,
    'rev': fields.String
})

version_list = api.model('version_list', {
    'host': fields.Nested(version_model),
})

@api.route('/')
class Version(Resource):
    @api.marshal_with(version_list)
    def get(self):
        return {
            'host': {'product': 'raspberry_pi', 'rev': GPIO.RPI_INFO['P1_REVISION']},
        }


