[![Dependency Status](https://www.versioneye.com/user/projects/57317530a0ca350050840a1a/badge.svg?style=flat)](https://www.versioneye.com/user/projects/57317530a0ca350050840a1a)

## Running platform tests

### Requirements
* Recommended OS - Ubuntu 14, Centos 7
* access to the Web (several tests rely on Web resources)
* key `key.dat` to decrypt repository secrets (ask repository owner) - not needed for smoke tests


### Setup

**1. Access to jumpbox**
You'll need to export the path to jumpbox key as `PT_NG_JUMP_KEY_PATH`


**2. Install required packages**
Ubuntu:
```
sudo -E add-apt-repository ppa:avacariu/git-crypt
sudo -E apt update
sudo -E apt install python3.4 python3.4-dev git git-crypt build-essential g++ libssl-dev
```

Centos:
```
sudo yum install epel-release
sudo yum install gcc libffi-devel python-devel python34 python34-devel python34-setuptools openssl-devel maven make
sudo easy_install pip
```


**3. Clone this repository**
```
git clone git@github.com:intel-data/platform-tests.git
```

**4. Decrypt repository secrets**
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


**5. Set up virtualenv**
```
./deploy/create_virtualenv.sh
```
This will create [pyvenv](https://docs.python.org/3/using/scripts.html) with all Python packages required in `~/virtualenvs/pyvenv_api_tests`.


**6. Configure test admin user** -- only if it's not already present on an environment

To run tests, we need a test admin user for tests with appropriate roles and authorizations. To create such user, use script `platform-tests/deploy/add-test-admin.sh`. The script requires uaac.


install uaac
Ubuntu:
```
sudo apt-get install rubygems-integration
sudo gem install cf-uaac
```

Centos:
```
sudo yum install rubygems ruby-devel gcc-c++
sudo gem install cf-uaac
```

run the script - (if there is already a user **username** you get the error "username already in use: **username**")
```
cd platform-tests
./deploy/add-test-admin.sh <domain> <uaa client pass> <username> <password>
```
- **domain**: e.g. daily-nokrb-aws.gotapaas.eu
- **uaa client pass**: uaa password for user admin
- **username**: e.g. taptester
- **password**: password for your taptester user



### Run tests from command line

The best way to run the tests from command line is to use the `run_tests.sh` script located in the `project` directory.
The script activates virtualenv and runs the tests.

Configuration (e.g. TAP domain) is defined using environment variables. They are parsed in `platform-tests/project/config.py`.
This is also where you can find names of the variables.

There are three options to define configuration:

1. export all variables before running tests

2. create a file `platform-tests/project/user_config.py` with environment variable defined like this:
  ```
  import os
  os.environ["PT_TAP_DOMAIN"] = "daily-nokrb.gotapaas.eu"
  os.environ["PT_ADMIN_USERNAME"] = "taptester"
  os.environ["PT_ADMIN_PASSWORD"] = "<password>"
  os.environ["PT_NG_JUMP_IP"] = "<jumpbox_ip>"
  os.environ["PT_NG_JUMP_KEY_PATH"] = "<jumpbox_key_path>"
  os.environ["PT_K8S_SERVICE_AUTH_PASSWORD"] = "<kubernetes-password>"
  os.environ["PT_DISABLE_ENVIRONMENT_CHECK"] = "True"
  ...
  ```

3. export the variables in `run_tests.sh`


The script `run_tests.sh` accepts [standard py.test parameters](https://pytest.org/latest/usage.html).

To run smoke tests:
`./run_tests.sh tests/test_smoke > <log_file> 2>&1`

To run components tests:
`./run_tests.sh tests/test_components > <log_file> 2>&1`

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

#### Running parametrized tests with single parameter only

In order to run test with only single parameter it is possible to run pytest with `--only-with-param` argument.

For example to run `test_create_and_delete_marketplace_service_instances` only for gateway with Single plan run:
```./run_tests.sh tests/test_smoke/test_functional.py::test_create_and_delete_marketplace_service_instances --only-with-param [gateway-single]```

### Run smoke tests on bastion

Ssh to your bastion using <jumpbox_key> (if you don't know bastion address, but you know the environment is deployed automatically on TeamCity, you'll find bastion address in platform-deployment-tests/deployment-init configuration, step Update domain IP addresses)

+ **Go through steps 2 to 6 from [Setup above](https://github.com/intel-data/platform-tests#setup)**

**Note:** to clone the repository, either use http, or copy your private key:
```
scp -i ./<jumpbox_key> [your_private_key] [user]@[bastion_address]:/[path_to_ssh]/.ssh/[your_private_key]
eval `ssh-agent`
ssh-add .ssh/[your_private_key]
```

**Note:** If the Platform version is other than the newest version, checkout analogous version of platform-tests, e.g.
```
git checkout tests/v0.7
```

+ **Run smoke tests**
```
cd /platform-test/project
./run_tests.sh tests/test_smoke > <log_file> 2>&1
```

**Useful options:**
* If you export `PT_TAP_REPOS_DIRECTORY`, all repositories will be retrieved from there, and tests won't download them from github.

### Creating offline package
```
cd /platform-tests
./deploy/create_package.sh
```

The package will be present in `/TAP-tests-<tests_version>.zip`.
The version is taken from `.bumversion.cfg`.

### Creating virtual environment from offline package
```
mkdir platform-tests
cd platform-tests
unzip ../TAP-tests-<tests_version>.zip
./deploy/create_virtualenv.sh --vendor vendor
```

By default virtual environment will be created in `~/virtualenvs/pyvenv_api_tests`.
It can be changed with parameter `--pyvenv path`.
