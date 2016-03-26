
from flask import Flask
from flask_restplus import Api

from .version import api as version_ns
from .gpio import api as gpio_ns
from .spi import api as spi_ns

# Can't use distribution name in python 3.4.0
# https://github.com/mitsuhiko/flask/issues/1011
app = Flask(__name__)
api = Api(app, endpoint='api', prefix='/api', doc='/api',
          version='0.1',
          title='raspberry-api-server',
          description='RESTful interface to Raspberry Pi')

api.add_namespace(version_ns)
api.add_namespace(gpio_ns)
api.add_namespace(spi_ns)

def run(*args, **kwargs):
    import os
    if os.environ.get('DEBUG'):
        app.config['DEBUG'] = True
    app.run(*args, **kwargs)

