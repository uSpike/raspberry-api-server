# raspberry-api-server
A RESTful API to the Raspberry Pi with Flask

[![Build Status](https://travis-ci.org/uSpike/raspberry-api-server.svg?branch=master)](https://travis-ci.org/uSpike/raspberry-api-server)

To start:
```shell
$ python -m raspberry_api.server
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

See full *swagger-ui* documentation at `http://127.0.0.1:5000/api`.

## Supported Interfaces
- SPI
- GPIO
- UART (planned)
- I<sup>2</sup>C (planned)
