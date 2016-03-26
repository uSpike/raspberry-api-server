
from contextlib import contextmanager
import tempfile

from flask_testing import TestCase

from raspberry_api.server.app import app
# monkey patch
from raspberry_api.server.spi import _flashrom
from raspberry_api.server.gpio import GPIO

class Base(TestCase):

    def create_app(self):
        app.config['TESTING'] = True
        return app

class TestVersion(Base):

    def test_get(self):
        ret = self.client.get('/api/version/')
        self.assert200(ret)

class TestGPIO(Base):

    def get_list(self):
        return self.client.get('/api/gpio/')

    def test_list(self):
        ret = self.get_list()
        self.assert200(ret)
        assert len(ret.json) > 0

    def test_get(self):
        def run(pin):
            ret = self.client.get('/api/gpio/{}'.format(pin['channel']))
            self.assert200(ret)

        for pin in self.get_list().json:
            run(pin)

    def test_set_foo(self):

        def run(pin, direction, value):
            @staticmethod
            def input(*args, **kwargs):
                return value
            GPIO.input = input

            ret = self.client.post('/api/gpio/{}'.format(pin['channel']),
                                   data={'direction': direction, 'value': value})
            self.assert200(ret)

            ret = self.client.get('/api/gpio/{}'.format(pin['channel']))
            self.assert200(ret)

            self.assertEqual(ret.json['direction'], direction)
            self.assertEqual(ret.json['value'], value)

        for pin in self.get_list().json:
            run(pin, 'in', 0)
            run(pin, 'in', 1)
            run(pin, 'out', 0)
            run(pin, 'out', 1)


class TestSPI(Base):


    def setUp(self):
        _flashrom.program = 'echo'

    @contextmanager
    def run_job(self, cmd, **kwargs):
        req = self.client.post('/api/spi/' + cmd, data=kwargs)
        self.assert200(req, cmd)
        job = req.json['job']
        yield job
        req = self.client.delete('/api/spi/job/{}'.format(job))
        self.assert200(req, cmd)

    @contextmanager
    def run_job_file(self, cmd, **kwargs):
        """ run with temporary file input """
        with tempfile.NamedTemporaryFile() as temp:
            with self.run_job(cmd, file=(temp, temp.name), **kwargs) as job:
                yield job

    def wait_job(self, job):
        while True:
            # worst case: continuous check
            req = self.client.get('/api/spi/job/{}'.format(job))
            status = req.json['status']
            if status == 'started':
                continue
            else:
                return req

    def test_post_cmd(self):
        def run(cmd):
            with self.run_job(cmd) as job:
                req = self.wait_job(job)
                self.assertEqual(req.json['status'], 'success')
                self.assert200(req, cmd)

        for cmd in ('read', 'erase'):
            run(cmd)

    def test_fail(self):
        _flashrom.program = 'doesNotExist'
        def run(cmd):
            with self.run_job(cmd) as job:
                req = self.wait_job(job)
                self.assertEqual(req.json['status'], 'error')

                req = self.client.get('/api/spi/job/{}/log'.format(job))
                self.assert200(req, cmd)

        for cmd in ('read', 'erase'):
            run(cmd)

    def test_write_file(self):
        with self.run_job_file('write') as job:
            req = self.wait_job(job)
            self.assertEqual(req.json['status'], 'success')

            req = self.client.get('/api/spi/job/{}/log'.format(job))
            self.assert200(req)

    def test_read_file(self):
        with self.run_job('read') as job:
            req = self.wait_job(job)
            self.assertEqual(req.json['status'], 'success')

            req = self.client.get('/api/spi/job/{}/log'.format(job))
            self.assert200(req)
            req = self.client.get('/api/spi/job/{}/file'.format(job))
            self.assert200(req)

    def test_verify_file(self):
        with self.run_job_file('verify') as job:
            req = self.wait_job(job)
            self.assertEqual(req.json['status'], 'success')

            req = self.client.get('/api/spi/job/{}/log'.format(job))
            self.assert200(req)

