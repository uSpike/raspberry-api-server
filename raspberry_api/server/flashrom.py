
from threading import Thread, Lock
import subprocess
import tempfile
import os

class Job(object):
    """
    This object represents a flashrom job
    """

    valid_status = ('started', 'success', 'error')

    def __init__(self, cmd, **kwargs):
        self.cmd = cmd
        self.filename = kwargs.get('filename')
        self.status = 'started'
        self.output = ''

    def update_status(self, status, output):
        if not status in self.valid_status:
            raise ValueError('Invalid status {}'.format(status))
        self.status = status
        self.output = output.decode('utf-8')

    @property
    def in_progress(self):
        if self.status == 'started':
            return True
        return False

    def wait(self):
        """ Wait for job to finish """
        while self.in_progress:
            pass

class Flashrom(object):

    program = './flashrom'
    programmer = 'linux_spi'
    device = '/dev/spidev0.{flash}'

    cmds = {
        'read':   '-r {}',
        'write':  '-w {}',
        'verify': '-v {}',
        'erase':  '-E'
    }

    # only run one instance at a time
    _lock = Lock()

    def __init__(self, speed='16M', timeout=600):
        self.speed = speed
        self.timeout = timeout

    def _layout_file(self, layout):
        temp = tempfile.NamedTemporaryFile(mode='w+')
        for name, (start, end) in layout.items():
            start = '0x%0.8X' % int(start, 16)
            end   = '0x%0.8X' % int(end, 16)
            buf   = '{}:{} {}\n'.format(start, end, name)
            temp.write(buf)
        return temp

    def _run_cmdline(self, job, cmd, **kwargs):

        filename = kwargs.get('filename', '')
        cmdname = self.cmds.get(cmd)
        args = [self.program, cmdname.format(filename)]

        flash = kwargs.get('flash', 0)
        args += ['--programmer',
            ':'.join([
                self.programmer,
                'dev=' + self.device.format(flash=flash),
                'spispeed=' + self.speed
            ])
        ]

        layout = kwargs.get('layout')
        if layout:
            layout_file = self._layout_file(layout)
            args += ['--layout ' + layout_file.name]
            image = kwargs.get('image')
            if image:
                args += ['--image', image]

        if kwargs.get('noverify'):
            args += ['--noverify']
        if kwargs.get('force'):
            args += ['--force']
        if kwargs.get('verbose'):
            args += ['--verbose']
        chip = kwargs.get('chip')
        if chip:
            args += ['--chip', chip]

        try:
            out = subprocess.check_output(' '.join(args), stderr=subprocess.STDOUT, shell=True)
            job.update_status('success', out)
        except subprocess.CalledProcessError as e:
            job.update_status('error', e.output)
        except subprocess.TimeoutExpired as e:
            job.update_status('error', 'timeout\n{}'.format(e.output))
        except FileNotFoundError as e:
            job.update_status('error', 'Program not found: {}'.format(self.program))
        except Exception as e:
            job.update_status('error', str(e))
        finally:
            if layout:
                layout_file.close()

    def _run(self, cmd, **kwargs):
        job = Job(cmd, **kwargs)
        thread = Thread(target=self._run_cmdline, args=(job, cmd), kwargs=kwargs)
        with self._lock:
            thread.start()
        return job

    def read(self, filename, **kwargs):
        """ Read to a file """
        return self._run('read', filename=filename, **kwargs)

    def write(self, filename, **kwargs):
        """ Write from a file """
        return self._run('write', filename=filename, **kwargs)

    def verify(self, filename, **kwargs):
        """ Verify a file """
        return self._run('verify', filename=filename, **kwargs)

    def erase(self, **kwargs):
        """ Full chip erase """
        return self._run('erase', **kwargs)

class LinuxSPI(Flashrom):
    pass

#class Dediprog(Flashrom):
#    programmer = 'dediprog'

