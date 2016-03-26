

try:
    from RPi import GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except RuntimeError as e:
    import warnings
    warnings.warn('Not running on raspberry pi')

    class GPIO(object):
        """ Fake for running on non-raspberry pi """
        RPI_INFO = {'INFO': 'Fake', 'P1_REVISION': 3}
        IN = OUT = 0
        LOW = HIGH = 0
        PUD_UP = PUD_DOWN = 0

        @staticmethod
        def setup(*args, **kwargs):
            pass

        @staticmethod
        def output(*args, **kwargs):
            pass

        @staticmethod
        def input(*args, **kwargs):
            return 1

from flask_restplus import Resource, Namespace, reqparse, fields, marshal_with, abort

class GPIOPin(object):
    map_directions = {'in': GPIO.IN, 'out': GPIO.OUT}
    map_values = {1: GPIO.HIGH, 0: GPIO.LOW}

    def __init__(self, channel, direction='in', initial=1):
        self.channel = channel
        self._direction = direction
        self.setup(initial=initial)

    def __repr__(self):
        return 'GPIO Pin {} (dir: {} val: {})'.format(self.channel, self.direction, self.value)

    def setup(self, **kwargs):
        GPIO.setup(self.channel, self.map_directions[self._direction], **kwargs)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value
        self.setup()

    @property
    def value(self):
        return GPIO.input(self.channel)

    @value.setter
    def value(self, value):
        GPIO.output(self.channel, self.map_values[value])

PINS = [
    GPIOPin(36),
    GPIOPin(38),
    GPIOPin(37),
    GPIOPin(40),
    GPIOPin(7),
    GPIOPin(32),
    GPIOPin(22),
    GPIOPin(29),
    GPIOPin(31),
    GPIOPin(33),
    GPIOPin(35),
    GPIOPin(11),
    GPIOPin(13),
    GPIOPin(15),
    GPIOPin(12),
]

api = Namespace('gpio')

gpio_model = api.model('gpio_pin', {
    'channel': fields.Integer(required=True),
    'value': fields.Integer(required=True),
    'direction': fields.String(enum=('in', 'out'), required=True),
})

@api.route('/')
class GPIOListResource(Resource):
    @api.marshal_with(gpio_model, as_list=True)
    def get(self):
        """ List of GPIO pins """
        return PINS

parser = reqparse.RequestParser()
parser.add_argument('direction', type=str, choices=['in', 'out'], location='values')
parser.add_argument('value', type=int, choices=[1, 0], location='values')

@api.route('/<int:channel>')
class GPIOResource(Resource):
    @api.marshal_with(gpio_model)
    def get(self, channel):
        """ Get GPIO pin by channel """
        pin = next((p for p in PINS if p.channel == channel), None)
        if not pin:
            abort(404, 'Bad channel')
        return pin

    @api.expect(parser)
    def post(self, channel):
        """ Set GPIO pin by channel """
        args = parser.parse_args()
        pin = next((p for p in PINS if p.channel == channel), None)
        if not pin:
            abort(404, 'Bad name')
        if args['value']:
            pin.value = args['value']
        if args['direction']:
            pin.direction = args['direction']


