## Stress Testing with Locust

### About Locust

* Homepage: http://locust.io/
* Documentation: http://docs.locust.io/en/latest/
* Source code: https://github.com/locustio/locust
* Homepage on pypi: https://pypi.python.org/pypi/locustio
* License: MIT

### Python version

Official latest Locust version (0.7.5) supports only Python 2. Support
for Python 3 has been added to master. We need to watch out for the next
release to switch to the official version.

To use Locust with Python 3, install using git:
pip install git+https://github.com/locustio/locust.git@master
(in requirements, it’s safer to specify a particular commit, and not rely on master HEAD).

### How to run stress tests

Before starting tests it is required to set several env variables:

- `PT_LOCUST_FILE` path to locust file with task (task sets are placed in `tests/test_stress`)
- `PT_NUM_CLIENTS` number of clients spawned by locust, default: 2
- `PT_HATCH_RATE` rate per second in which clients are spawned, default: 1
- `PT_DURATION` test duration, default: 10 [minutes]
- `PT_LOCUST_PORT` port for locust web service, default: 8089

After setting required env variables test can be run by `python run_stress_tests.py`.

#### How to run parametrized tests separately

For measuring test execution separately with each parameter it is possible to run pytest with `--only-with-param` argument. For more details see README.md in platform-tests root directory.

### Locust documentation 

Documentation is rather minimal, but the source code is clean and
readable.

Good to know:

**Using locust from command line**
Using `--no-web` option disable interacting with locust using HTTP.

All locust options can be found in its source code: `locust.main`.

It is possible to perform given number of calls `locust -n <number>` or `locust -num-request=<number>`. 

**Interacting with locust using HTTP**

Locust provides a web interface, by default served on *:8089.

Tests can be triggered using either UI or a http call.
Provide number of users and user hatch rate (number of users per second).

To start:
```curl -X POST  -F 'locust_count=2' -F 'hatch_rate=2' http://localhost:8089/swarm```

To stop:
```curl http://localhost:8089/stop```

Retrieve statistics:
```curl http://localhost:8089/stats/requests```

Web API is implemented in Flask. Routes can be viewed in `locust.web` module.
The interface can be extended. More info: http://docs.locust.io/en/latest/extending-locust.html#adding-web-routes


### Locust with platform-tests

Locust’s main use case is stress testing HTTP applications. The
available client (`locust.clients module`) enables sending HTTP requests
and is implemented using the requests library. However, the client is
generic, missing many functionalities which are already implemented in
platform-tests framework.

Locust allows for implementing custom clients.
Example RPC client: http://docs.locust.io/en/latest/testing-other-systems.html

The main requirement is to be able to run existing test scenarios
as stress tests. This means that we need to implement an adapter between
locust and platform-tests.

Points to consider:

* Each locust task is a separate test session (i.e. http session) - user logs in each time.
* Fixtures executed again for each task.
* Probably we’ll need to implement additional e2e test scenarios.
* Integration problems between locust and py.test.
* Statistics collected per task, not per an http request.
