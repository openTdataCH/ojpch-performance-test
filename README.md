# ojpch-performance-test

Performance tests (response time measurements) for the Swiss Open Journey Planner (OJP) service, plus TRIAS 2020 and J-S for comparison purposes.

## Introduction
This repository provides a Python 3 test script `ojp_performance_tests.py`
for running series of tests of OJP and TRIAS2020 service endpoints,
plus SBB Journey Service (J-S) for comparison.

The script is tailored for the services and endpoints
(environments) of the Swiss service OJP (Open Journey Planner)
for intermodal trip planning, which is in production since 2021 and
documented here:
- [Open Journey Planner (OJP) - Cookbook](https://opentransportdata.swiss/en/cookbook/open-journey-planner-ojp)
- [TripRequest (TRIAS 2020)](https://opentransportdata.swiss/en/cookbook/triprequest)

## Main features:
- Run series of tests (API calls) for given environments (prod, test, etc.)
and request types.
- Supported request types:
  - OJP: Trip Request TR, Location Information Request LIR,
  Trip Information Request TIR, Stop Event Request SER.
  - TRIAS 2020: TR.
- Fully configurable with a parameter file `parameters.txt`,
- Measures response times of each call.
- Does some basic checks (http status code, payload, etc.)
- Counts and displays statistics.
- Saves overview information of each test call in CSV files.
- Saves all requests and responses into files.

## License
[MIT license](https://github.com/openTdataCH/ojpch-performance-test/blob/main/LICENSE)

## Setup
The script may be installed and run in Python development environment
(Pycharm, Visual Studio Code or similar),
or run on the command line (shell).

### Script Files (`*.py`)
- `ojp_performance_tests.py`: the main, runnable script; contains most of the code.
- `configuration.py`: contains some of the configuration; see below. Is imported upon startup.
- `local_configuration.py`: optional, extra configuration; see below.

### Sub-Directories
The following sub-directories are needed (created if missing):
- `data`: mainly for the DIDOK file (is downloaded if not present)
- `input`: contains the parameter file(s), see below) 
- `output`: for every test run, a new sub-directory `test...` is created here.
- `templates`: Contains 10 templates for the OJP requests (`LIR.xml`, etc.)

### Python 3 Interpreter and Libraries
The script requires a recent Python 3 interpreter (we have used 3.10).
It requires the `requests` library, which may be
installed with pip, pipenv or similar.
(in addition, libraries `certifi`, `charset-normalizer`, `idna`, `urllib3`
will be installed for transient dependencies.)

## Configuration
The test runs are configured by these three files:

### Base Configuration (URLs, etc.)
- `configuration.py`: Contains some basic configuration parameters which will normally remain constant,
such as servic URLs, tokens, etc.
- `local_configuration.py`: may be used in addition, to supersede parameters in `configuration.py`.
This file is not provided on github (excluded in .gitignore).
It should be used for secrets (tokens) that will not be pushed to github.

### Test Configuration File (number of calls, request types, etc.)
All test configuration files must be in the directory `input`.

#### Default File
The file `./input/parameters.txt` defines all parameters to actually configure a test, such as environment,
request types, number of calls, etc..

This file `./input/parameters.txt`
is the default configuration file.
It is used if the script is started
with no command-line arguments.

The file contains simple key-value pairs,
plus lots of comments.

#### Other Files
Other parameter files may be used instead of the default, e.g. `./input/parameters123.txt`.
The name `parameters123.txt` must be provided as command-line argument when starting the script.

#### Fail Fast Principle
The parameter file must always provide the full
configuration ("fail fast" principle).
Missing or mistyped keys will lead to runtime-errors.
Default values are not used, in order to keep parametrization simple and unambiguous.


## Test runs
### Starting a Test
The script is directly runnable, simply press "run" in your development environment.

### Logging
The progress of the tests is logged in much detail to the console (shell).

### Saving Results to File
In directory `output`, new test directry is created where all results will be stored.
The directory name contain the parameter file used, and a date/timestamp.

Depending on the parameters, the following data is saved:
- the parameters file used
- a statistics file
- for each environment/request-type, a CSV file with all measurements
- if parameter `save_details = True`, all requests and responses are saved into files.
 

## Statistics
Statistics mainly comprise:
- counts (numbers) of total, successful (200 ok) and failed runs.
- calculation times (response times): min, max, average (based only on successful tests).


## Miscellaneous
### Didok for Stations/Stops
The DIDOK file is a data source containing all stops/stations of public transport in Switzerland.
See: https://opentransportdata.swiss/en/dataset/didok, file `verkehrspunktelemente_actualdate.csv`.

The script loads this file from `data` directory.
With parameter `download_didok_data=True`, the file is first downloaded from opentransportdata.swiss.

### Random Choice of Start/Stop
OJP services all contain one or two (or more) loctions: either a place (usually station/stop),
or a geo-position (WGS 84 coordinates, longitude, latitude) of a place.

Tests are randomly choosing stations/stops from the DIDOK file.

The random number generator may be set with a "seed" (set `use_random_seed=True`),
so that, when a test is repeated, the same "random" places will be generated.

### Connections File 'from', 'to' and 'via' Locations
If parameter `use_connections_file=True`,
the 'from', 'to' and 'via' locations
will be taken from a file.

The file must be in `input` directory,
the name is taken from the `connections_file` parameter.

The file is a simple UTF-8 encoded CSV-file
with a leading check info (usually empty),
then a 'from', 'to' and 'via' locations,
separated by a delimiter defined in the `connections_delimiter` parameter
(recommended: semi-colon ';').

A comma ',' is used as delimiter within names of bus stops,
(e.g. 'Bern, Wankdorf'), as is commonly used in Swiss PT.

The file `connections-example.csv` contains 50, pseudo-randomly
selected connections for illustration purposes.


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
Various environments, such as "Prod", "Int", "Test", etc. can be configured in
`configuration.py` and `local_configuration.py`.
There, `apiEndpoint` (URL) and `authBearerKey` (secret token) are configured.

In the parameters files then, these environments are referred to by their names,
e.g. "Prod" or "Int".

### OJP <Params\>
All OJP requests contain a `<ojp:Params>` element for adding some controlling
what to include in the response.
See https://opentransportdata.swiss/en/cookbook/open-journey-planner-ojp/ for more details.

In our script, these settings may be configured by corresponding parameters in the
parameters file, e.g.
`tr_include_track_sections`, `tr_include_leg_projection` and many more.

To turn all these "extras" off, set the parameter `use_params = False`,
like a "main switch". Only if `use_params = True`, the other boolean
parameters will have an effect.
