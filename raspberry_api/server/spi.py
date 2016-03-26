
import tempfile
import random
import atexit
import os
from collections import OrderedDict

from flask import send_file
from flask_restplus import Resource, Namespace, reqparse, fields, marshal_with, abort
from werkzeug.datastructures import FileStorage

from .flashrom import LinuxSPI, Job

api = Namespace('spi')

_flashrom = LinuxSPI()
_jobs = {}

def _get_job(id):
    if not id in _jobs:
        abort(404, "Invalid ID")
    return _jobs[id]

def _cleanup():
    for id, job in _jobs.items():
        if job.filename:
            os.unlink(job.filename)

atexit.register(_cleanup)

def _new_id():
    return random.getrandbits(20)

spi_job_model = api.model('spi_job', {
    'status': fields.String(enum=Job.valid_status, required=True),
    'cmd': fields.String(enum=list(_flashrom.cmds.keys()), required=True),
})

@api.route('/job/<int:id>')
class SPIJob(Resource):
    @api.marshal_with(spi_job_model)
    def get(self, id):
        """
        Its a job
        """
        return _get_job(id)

    def delete(self, id):
        if not id in _jobs:
            abort(404)
        del _jobs[id]


@api.route('/job/<int:id>/file')
class SPIJob_File(Resource):
    def get(self, id):
        job = _get_job(id)
        filename = job.filename
        if filename:
            return send_file(job.filename, cache_timeout=0)


@api.route('/job/<int:id>/log')
class SPIJob_Log(Resource):
    def get(self, id):
        job = _get_job(id)
        return job.output


def _layout(value):
    layout = OrderedDict()
    for lo in value.split(','):
        name, _, addr = lo.partition(':')
        if '' in (name, addr):
            raise ValueError('Missing name or addr range')
        start, _, end = addr.partition('-')
        if '' in (start, end):
            raise ValueError('Missing addr start or end')
        layout[name] = start, end
    return layout

spi_parser = reqparse.RequestParser()
# location=values lets us put values in query string or post body
spi_parser.add_argument('flash', type=int, choices=[0, 1], default=0, location='values')
spi_parser.add_argument('layout', type=_layout, location='values')
spi_parser.add_argument('image', type=str, location='values')
spi_parser.add_argument('noverify', type=bool, location='values')

# add file parameter
spi_file_parser = spi_parser.copy()
spi_file_parser.add_argument('file', type=FileStorage, location='files', required=True)

spi_post = api.model('spi_post', {
    'job': fields.Integer(),
})


@api.route('/read')
class SPIRead(Resource):

    @api.expect(spi_parser)
    @api.marshal_with(spi_post)
    def post(self):
        args = spi_parser.parse_args()
        id = _new_id()
        prefix = 'read_{}'.format(id)
        temp = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
        temp.close()
        job = _flashrom.read(temp.name, **args)

        _jobs[id] = job
        return {'job': id}


@api.route('/erase')
class SPIErase(Resource):

    @api.expect(spi_parser)
    @api.marshal_with(spi_post)
    def post(self):
        args = spi_parser.parse_args()
        job = _flashrom.erase(**args)
        id = _new_id()
        _jobs[id] = job
        return {'job': id}


@api.route('/write')
class SPIWrite(Resource):

    @api.expect(spi_file_parser)
    @api.marshal_with(spi_post)
    def post(self):
        args = spi_file_parser.parse_args()

        id = _new_id()
        prefix = 'write_{}'.format(id)
        temp = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
        fileobj = args['file']
        fileobj.save(temp)

        job = _flashrom.write(temp.name, **args)
        _jobs[id] = job
        return {'job': id}


@api.route('/verify')
class SPIVerify(Resource):

    @api.expect(spi_file_parser)
    @api.marshal_with(spi_post)
    def post(self):
        args = spi_file_parser.parse_args()

        id = _new_id()
        prefix = 'verify_{}'.format(id)
        temp = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
        fileobj = args['file']
        fileobj.save(temp)

        job = _flashrom.verify(temp.name, **args)
        _jobs[id] = job
        return {'job': id}

