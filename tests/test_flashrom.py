
import unittest

from raspberry_api.server.flashrom import Flashrom

class Test(unittest.TestCase):
    def setUp(self):
        self.flashrom = Flashrom()
        # just echo back arguments
        self.flashrom.program = 'echo'

    def test_cmds(self):
        other_args = ' --programmer linux_spi:dev=/dev/spidev0.0:spispeed=16M'

        job = self.flashrom.read('foofile')
        job.wait()
        self.assertEqual(job.cmd, 'read')

        output = job.output.strip()
        self.assertEqual(output, '-r foofile' + other_args)

        job = self.flashrom.write('foofile')
        job.wait()
        self.assertEqual(job.cmd, 'write')

        output = job.output.strip()
        self.assertEqual(output, '-w foofile' + other_args)

        job = self.flashrom.verify('foofile')
        job.wait()
        self.assertEqual(job.cmd, 'verify')

        output = job.output.strip()
        self.assertEqual(output, '-v foofile' + other_args)

        job = self.flashrom.erase()
        job.wait()
        self.assertEqual(job.cmd, 'erase')

        output = job.output.strip()
        self.assertEqual(output, '-E' + other_args)

    def test_flash(self):
        job = self.flashrom.read('foofile', flash=1)
        job.wait()
        self.assertIn('spidev0.1', job.output)

    def test_fail(self):
        self.flashrom.program = 'false'
        job = self.flashrom.read('foofile')
        job.wait()
        self.assertEqual('error', job.status)

    def test_timeout(self):
        self.flashrom.program = 'sleep 2;'
        self.flashrom.timeout = 1
        job = self.flashrom.read('foofile')
        job.wait()
        self.assertEqual('error', job.status)

    def test_bad_program(self):
        self.flashrom.program = 'doesNotExist'
        job = self.flashrom.read('foofile')
        job.wait()
        self.assertEqual('error', job.status)


if __name__ == '__main__':
    unittest.main()
