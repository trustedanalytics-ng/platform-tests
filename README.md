[![Dependency Status](https://www.versioneye.com/user/projects/57317530a0ca350050840a1a/badge.svg?style=flat)](https://www.versioneye.com/user/projects/57317530a0ca350050840a1a)

## Running platform tests

### Requirements
* Recommended OS - Ubuntu 14
* access to the Web (several tests rely on Web resources) - not necessarily needed for smoke tests (see below)
* key `key.dat` to decrypt repository secrets (ask repository owner) - not needed for smoke tests


### Setup

**1. Access to jumpbox**
(not needed for smoke tests)
You'll need to export the path to jumpbox key as `PT_JUMPBOX_KEY_PATH`


**2. Install required packages**
```
sudo -E add-apt-repository ppa:avacariu/git-crypt
sudo -E apt update
sudo -E apt install python3.4 python3.4-dev git git-crypt build=essential g++ libssl-dev
```

**3. Download and install git crypt**
(not needed for smoke tests)
```
wget https://github.com/AGWA/git-crypt/archive/0.5.0.zip
unzip 0.5.0.zip
cd git-crypt-0.5.0
make git-crypt
sudo make install git-crypt
```


**3. Clone this repository**


**5. Decrypt repository secrets**
(not needed for smoke test)

Place `key.dat` in /platform-tests directory.
```
cd platform-tests
./deploy/unlock.sh
```
Check that secrets are decrypted correctly:
```
cat platform-tests/project/secrets/gmail-code.json
```
If the file looks normal, secrets have been decrypted.


**6. Set up virtualenv**
```
./deploy/create_virtualenv.sh
```
This will create [pyvenv](https://docs.python.org/3/using/scripts.html) with all Python packages required in `~/virtualenvs/pyvenv_api_tests`.


**7. Configure test admin user** -- only if it's not already present on an environment
You can use default `admin` user, but then certain failures may occur, because the username is not a valid e-mail.

To run tests, we need a user trusted.analytics.tester@gmail.com with appropriate roles and authorizations. To create such user, use script `platform-tests/deploy/add-test-admin.sh`. The script requires cf client and uaac.


install cf client
```
wget https://cli.run.pivotal.io/stable?release=debian64 -O cf-client.deb
sudo dpkg -i cf-client.deb
```

install uaac
```
sudo apt-get install rubygems-integration
sudo gem install cf-uaac
```

run the script
```
./add-test-admin.sh <domain> <cf admin password> <core org name> <core space name> <password>
```
- domain, e.g. daily-nokrb.gotapaas.eu
- cf admin password -- cf password of user admin
- core org name (defaults to trustedanalytics)
- core space name (defaults to platform)



### Run tests from command line

The best way to run the tests from command line is to use the `run_tests.sh` script located in the `project` directory.
The script activates virtualenv and runs the tests.

Configuration (e.g. TAP domain, core org name, etc.) is defined using environment variables. They are parsed in `platform-tests/project/config.py`.
This is also where you can find names of the variables.

There are three options to define configuration:

1. export all variables before running tests

2. create a file `platform-tests/project/user_config.py` with environment variable defined like this:
```
import os
os.environ["PT_TAP_DOMAIN"] = "daily-nokrb.gotapaas.eu"
os.environ["PT_ADMIN_PASSWORD"] = "password"
...
```

3. export the variables in `run_tests.sh`


The script `run_tests.sh` accepts [standard py.test parameters](https://pytest.org/latest/usage.html).

To run smoke tests:
`./run_tests.sh tests/test_smoke > <log_file> 2>&1`

To run functional tests:
`./run_tests.sh tests/test_functional > <log_file> 2>&1`

To run functional tests of user-management, excluding long tests:
`./run_tests.sh tests/test_functional -m "user_management and not long"`

Tests log to both stdout, and stderr, so to save output to a file, use `> <log_file> 2>&1`.

#### Rerunning failed tests

To run only tests that failed on TC:

1. Go to the given test run and artifact tab.

2. Download `lastfailed/lastfailed` file and put it on `/path/to/platform-tests/project/.cache/v/cache/` directory.

3. Run tests from command line with `--lf` (`--last-failed`) flag.

Due to issues with mongo reporter it might be necessary to specify a tests path. In this case just use a directory that contains all failed tests (e.g. `platform-tests/project/tests`). Full command should looks like ```./run_tests.sh tests --lf```.

### Run smoke tests on bastion

Ssh to your bastion using, most likely, auto-deploy-virginia.pem key (if you don't know bastion address, but you know the environment is deployed automatically on TeamCity, you'll find bastion address in platform-deployment-tests/deployment-init configuration, step Update domain IP addresses)

+ **Go through steps 2 to 6 from [Setup above](https://github.com/intel-data/platform-tests#setup)**

**Note:** to clone the repository, either use http, or copy your private key:
```
scp -i ./auto-deploy-virginia.pem [your_private_key] [user]@[bastion_address]:/[path_to_ssh]/.ssh/[your_private_key]
eval `ssh-agent`
ssh-add .ssh/[your_private_key]
```

**Note:** If the Platform version is other than the newest version, checkout analogous version of platform-tests, e.g.
```
git checkout tests/v0.7
```
**Note:** you'll have to also specify appstack version (branch/tag name) in configuration, i.e. export PT_APPSTACK_VERSION=v0.7

+ **Run smoke tests**
```
cd /platform-test/project
./run_tests.sh test_smoke > <log_file> 2>&1
```

**Useful options:**
* If you export `PT_LOCAL_APPSTACK_PATH`, this will be the appstack.yml used, and tests won't download it from GitHub. This will allow for running smoke tests without access to GitHub.
* If you export `PT_TAP_REPOS_DIRECTORY`, all repositories will be retrieved from there, and tests won't download them from github.
