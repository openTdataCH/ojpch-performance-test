# ojpch-performance-test

Performance tests (response time measurements) for the Swiss Open Journey Planner (OJP) service,
supporting OJP versions 1.0 and 2.0, plus TRIAS 2020 and J-S for comparison purposes.

## Introduction
This repository provides a Python 3 test script for running series of tests on the services mentioned above.

The script is tailored for the services and endpoints
(environments) of the Swiss service OJP (Open Journey Planner)
for intermodal trip planning, which is in production since 2021 and
documented here:
- [Open Journey Planner (OJP) - Cookbook](https://opentransportdata.swiss/en/cookbook/open-journey-planner-ojp)
- [TripRequest (TRIAS 2020)](https://opentransportdata.swiss/en/cookbook/triprequest)

## Main features:
- Runs series of a given number of tests (API calls) for given environments (services) and request types.
- supported environements: OJP 1.0 and 2.0 services, TRIAS 2020 and SBB J-S (Journey Service).
- Supported request types are:
  - OJP 1.0 and 2.0: Trip Request TR, Location Information Request LIR,
  Trip Information Request TIR, Stop Event Request SER (named TR10, TR20, LR10, LR20 etc.)
  - TRIAS 2020: TR (named TRIAS2020TR).
  - J-S: /trips/by-origin-destination
- Fully configurable with a parameter file in folder  `test_parameters`, default name `parameters.txt`,
- Measures the response times in milliseconds of each call.
- Does some basic checks (http status code, payload, etc.) and counts.
- Displays statistics.
- Saves results (options):
  - overview information of each test call in CSV files.
  - all requests and responses into files.
  - uploads statistics in a JSON file to an OpenSearch index.

## License
[MIT license](https://github.com/openTdataCH/ojpch-performance-test/blob/main/LICENSE)

## Setup
The script may be installed and run in a Python 3 development environment
(e.g. Pycharm, Visual Studio Code or similar),
or run on the command line (shell).

### Script Files (`*.py`)
- `ojp_performance_tests.py`: the main, executable module; contains the top level functions.
- `configuration.py`: contains some of the configuration; see below. Is imported upon startup.
- `local_configuration.py`: optional, extra configuration, including secrets; see below.
- `utilities/....py`: various modules which support the main module.

### Sub-Directories
The following folders are needed (defined in `configuration.py`)
- `output` (created if missing): for every test run, a new sub-directory `test...` is created here.
- `stop_points` (created if missing): location where the stop-point file will be stored. 
- `templates`: Contains 20+ templates for building the service request bodies.
- `test_parameters`: contains the parameter file(s), see below. 
- `utilities`: Python code (script files).
 
### Python 3 Interpreter and Libraries
The script requires a recent Python 3 interpreter (we have used 3.9 or newer).
It requires the `requests` library, which may be installed with pip, pipenv or similar.
(in addition, libraries `certifi`, `charset-normalizer`, `idna`, `urllib3`
will be installed for transient dependencies.)

## Configuration
The test runs are configured by the three files `configuration.py`, `local_configuration.py`
and a parameters file in the directory `test_parameters` (default: `parameters.txt`).

### 1. Base Configuration (URLs, etc.) in `configuration.py`
This file contains some basic configuration parameters which will normally remain constant,
such as the available environments (service URLs, tokens, etc.).

### 2. Additional Configuration in `local_configuration.py`
This file may be used in addition, to supersede parameters in `configuration.py`.
The file is loaded, if available,
at the end of `configuration.py` (i.e. when this module is loaded).

The file is not provided on github (excluded in .gitignore).
It should be used for secrets (tokens) that will not be pushed to github.

### 3. Test Parameters (number of calls, request types, etc.) in directory `test_parameters`
All test parametrization files must be in the directory `test_parameters`.

The **default file** `parameters.txt` (from github) shows all available options.
The file contains simple key-value pairs plus explanatory comments.

If the test is started with 1+ **command-line arguments**, 
the first CL argument is taken as the name of the parameters file to be used.

Thus, to set up you own tests, the easiest way is to make a copy of `parameters.txt`
and alter the settings as needed. Then, add the name of your file as first
command-line argument.

*Note: We adopt "fail fast principle". The parameter file must always provide the full
configuration. Missing keys or key with typos will cause runtime-errors.*


## Test runs
### Starting a Test
The script `main.py` is directly executable. Simply press the "run" button in your development environment.

If you have a file with test parameters, add its name as the (first) command-line argument.

### Logging
The progress of the tests is logged in much detail to the console (shell) and/or a log file.

Logging is defined in the Python module `utilities/logging_wrapper.py` which wraps
standard Python `logging`.

### Folder with Test Results
In directory `output`, a new test directory is created, where everything is stored in files:
the parameters file, statistics, response time measurements, etc.

If parameter `save_details = True`, all requests and responses are saved into files.

### Statistics
Statistics mainly comprise:
- counts (numbers) of total, successful (200 ok) and failed runs,
- response times: min, max, average (based only on successful tests).

## Miscellaneous
### Stops Points (Stations, Bus Stops, etc)
As of early 2024, stop points are delivered as open data in a CSV file under the following URL: 
https://opentransportdata.swiss/en/dataset/service-points-actual-date

This replaces the predecessor, known as "DIDOK file".

Our script uses a subfolder `stop_points`. If it does not find the stop-points file there,
it loads the stop points from the given URL.

### Random Choice of Start/Stop
OJP services all contain one or two (or more) loctions: either a place (usually station/stop),
or a geo-position (WGS 84 coordinates, longitude, latitude) of a place.

Tests are randomly choosing stations/stops from the stop-points file.

The random number generator may be set with a "seed" (set `use_random_seed=True`),
so that, when a test is repeated, the same "random" places will be generated.

### Connections File 'from', 'to' and 'via' Locations
If parameter `use_connections_file=True`,
the 'from', 'to' and 'via' locations will be taken from a file.

The file must be in `input` directory,
the name is taken from the `connections_file` parameter.

The file is a simple UTF-8 encoded CSV-file with a leading 'check info' (may be empty),
then a 'from', 'to' and 'via' locations, 
separated by a delimiter defined in the `connections_delimiter` parameter
(recommended: semi-colon ';').

A comma ',' is used as delimiter within names of bus stops, (e.g. 'Bern, Wankdorf'), as is commonly used in Swiss PT.

The file `connections.csv` contains 50, pseudo-randomly selected connections in Switzerland for illustration purposes.


### Random definition of DepArrTime
Arrival/Departure time must be set to a useful date in the near future.
In our script, this is also generated randomly; the range of dates and times
can be defined with the parameters `days_ahead_min`, `days_ahead_max`, `hours_min`, `hours_max`,
`minutes_min`, and `minutes_max`.

### Request Types (TR, LIR, SER, TIR)
Currently, these request types are supported:
- **Trip Request (TR)**: the basic trip-planning service for a trip from A to B.
- **Location Information Request (LIR)**: look-up of locations (stops, places) matching a given name.
- **Stop Event Request (SER)**: Data respetive to a stop event.
- **Trip Info Request (TIR)**: Additional information about a trip.
For this request, a prior call of a TR is needed, in which a trip A to B
is computed and for each timed leg, a `journey_ref` and `op_day_ref` are returned.
In our script, the first `journey_ref` and `op_day_ref` found in the response are used.

For more details, see: https://opentransportdata.swiss/en/cookbook/open-journey-planner-ojp/

### Environments ("Prod", "Int", etc.)
Various environments, such as "OjpProd", "Int", "Test", etc. can be configured in
`configuration.py` and `local_configuration.py`.
There, `apiEndpoint` (URL) and `authBearerKey` (secret token) are configured,
as well as the request that are supported.

In the test parameters file then, these environments are referred to by their names,
e.g. "OjpProd".

### OJP <Params\>
All OJP requests contain a `<ojp:Params>` element for adding some controlling
what to include in the response.
See https://opentransportdata.swiss/en/cookbook/open-journey-planner-ojp/ for more details.

In our script, these settings may be configured by corresponding parameters in the
parameters file, e.g.
`tr_include_track_sections`, `tr_include_leg_projection` and many more.

These configs are only effective, however, if also the "main switch" is "on". 
The main switch ("on" or "off")
is controlled by a "suffix" after the request type.
Thus, in the parameters file, at parameter `request_types`, you may add suffices as follows:
- "+" = 1 test run *with* parameters active.
- "-" = 1 test run *without* parameters (default)
- "*" = 2 test runs, first *without* parameters, then *with* parameters.
