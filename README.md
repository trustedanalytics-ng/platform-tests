[![Dependency Status](https://www.versioneye.com/user/projects/57317530a0ca350050840a1a/badge.svg?style=flat)](https://www.versioneye.com/user/projects/57317530a0ca350050840a1a)

## Running api tests

### Requirements
* Recommended OS - Ubuntu 14
* access to the Web (several tests rely on Web resources)
* key `key.dat` to decrypt repository secrets (ask repository owner)


### Setup

**1. Access to cdh launcher**
```
cp <private/key/of/ec2-user> ~/.ssh/auto-deploy-virginia.pem
```
Unfortunately, tests currently use a hardcoded path.

**2. Install required packages**
```
sudo -E add-apt-repository ppa:avacariu/git-crypt
sudo -E apt update
sudo -E apt install python3 python3-dev git git-crypt build=essential g++ libssl-dev
```

**3. Clone repository**
```
git clone git@github.com:intel-data/platform-tests.git
```

**4. Decrypt repository secrets**

Place `key.dat` in /platform-tests directory.
```
cd platform-tests
./deploy/unlock.sh
```
Check that secrets are decrypted correctly:
```
cat platform-tests/project/configuration/secrets/.secret.ini
```
If the file looks normal, secrets have been decrypted.

**5. Set up virtualenv**
```
./deploy/create_virtualenv.sh
```
This will create [pyvenv](https://docs.python.org/3/using/scripts.html) with all Python packages required in `~/virtualenvs/pyvenv_api_tests`.

**6. Add config** -- only if environment has non-default configuration (e.g. no trustedanalytics)

If you plan to run tests on a new environment (i.e. not daily, sprint, demo, etc.), supply non-default config values in `platform-tests/project/configuration/config.py`, in `__CONFIG` string.

**7. Configure test admin user** -- only if it's not already present on an environment

To run tests, we need a user trusted.analytics.tester@gmail.com with appropriate roles and authorizations. To create such user, use script `platform-tests/deploy/add_test_admin.sh`. The script requires cf client and uaac.

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
add_test_admin.sh <domain> <cf admin password> <reference org name> <reference space name> <password>
```
- domain, e.g. gotapaas.eu
- cf admin password -- cf password of user admin
- reference org name (defaults to trustedanalytics)
- reference space name (defaults to platform)
- password (see password for trusted.analytics.tester@gmail.com in DEFAULT section in `platform-tests/project/configuration/secrets/.secret.ini`)


### Run tests
1. Activate virtualenv: `source ~/virtualenvs/pyvenv_api_tests/bin/activate`.
2. `cd platform-tests/project`
3. Run tests using `run_tests.sh` script (see below).

To run smoke tests:
`./run_tests.sh -e <domain, e.g. demotrustedanalytics.com> -s test_smoke > <log_file> 2>&1`

To run api tests:
`./run_tests.sh -e <domain, e.g. demotrustedanalytics.com> -s test_functional > <log_file> 2>&1`


**Parameters**

`-s` - run tests from one directory or file, e.g. `./run_tests.sh -e <domain> -s <path/in/tests/directory>`.

`-t` - run single test: `./run_tests.sh -e <domain> -t <test_name>`, for example: `-t test_create_organization`.

`-p` - priority (higth, medium, low), run only tests with as high priority as specified

`-c` - components, run only tests which apply to the specified components, e.g. `./run_tests.sh -e <domain> -c user_management -c das` - the run will contain tests for user-management and das (full list of available components is available in `./run_tests.sh -help`.

`--only-tagged` - run only tests with a particular tag, e.g. `./run_tests.sh -e <domain> --only-tagged long`

`--not-tagged` - run only tests which are not tagged with a particular tag `./run_tests.sh -e <domain> --not-tagged long`

`-l` - specify logging level. There are 3 logging levels: DEBUG (default), INFO `-l INFO`, WARNING `-l WARNING`.

`--disable-remote-logger` - Run tests without retrieving logs from remote logger.

`--remote-logger-retry-count` - Set number of retries for remote logger

The `run_tests.sh` shell script is used only to run_tests.py in a virtual environment, passing all arguments to the Python script. If you want to see/modify what is happening when tests are run, go there. Argument parsing function is located in project/configuration/config.py

Tests log to both stdout, and stderr, so to save output to a file, use `> <log_file> 2>&1`.


### Run tests on TeamCity agent

Before tests are run on TeamCity:

Required packages (see above) should be installed on the agent.

On TeamCity, a few Command Line custom script steps need to be defined:

Decrypt repository secrets: `git-crypt unlock %decryptor.key.path%`

Create virtualenv `./deploy/create_virtualenv.sh`

Smoke tests `./project/run_tests.sh -s "test_smoke" -e %test_platform%`

API tests: `./project/run_tests.sh -s %test_type% -e %test_platform% --client-type "$client_type"`

### Run smoke tests on bastion

Ssh to your bastion using most likely auto-deploy-virginia.pem key (if you don't know bastion address, but you know the environment is deployed automatically on TeamCity, you'll find bastion address in platform-deployment-tests/deployment-init configuration, step Update domain IP addresses)

+ **Go through steps 2 to 8 from [Setup above](https://github.com/intel-data/api-tests#setup)**

**Note:** to clone the repository, either use http, or copy your private key:
```
scp -i ./auto-deploy-virginia.pem [your_private_key] [user]@[bastion_address]:/[path_to_ssh]/.ssh/[your_private_key]
eval `ssh-agent`
ssh-add .ssh/[your_private_key]
```

**Note:** If the Platform version is other than the newest version, checkout analogous version of api-test, e.g.
```
git checkout TAP-2016-JAN-2-1
```
**Note:** you'll have to pass the same tag to `./run_tests.sh ... -v TAP-2016-JAN-2-1`

+ **Run smoke tests**
```
cd /platform-test/project
./run_tests.sh -s test_smoke -e <platform_address> > <log_file> 2>&1
```

**Useful options:**
* Do not download appstack.yml from GitHub, but use local file instead:
` ./run_tests.sh ... [--local-appstack <path to local appstack if it is used>]`
* Get appstack from version other than master
`./run_tests.sh ... [-v <e.g. TAP-2016-JAN-2-1>]`


