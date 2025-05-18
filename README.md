# rcgamestats

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

rcgamestats is a web application that enables running a large number of RoboCup Soccer 2D simulation matches in a distributed manner while aggregating match results over the Internet. It is designed to support the distributed execution of matches across dozens or more host machines.

## Requirements
- Server
  - [Flask](https://flask.palletsprojects.com/)
  - See [requirements.txt](requirements.txt) for other dependent libraries.

- Client
  - Linux Environment (Ubuntu 22.04 is recommended)
  - Python3
  - [rcssserver](https://github.com/rcsoccersim/rcssserver)
  - (optional) [librcsc](https://github.com/helios-base/librcsc)
  - (optional) [rcg2data](https://github.com/hidehisaakiyama/rcg2data)
  - (optional) cpufrequtils

## Documentation

See [docs](docs/README.md)
