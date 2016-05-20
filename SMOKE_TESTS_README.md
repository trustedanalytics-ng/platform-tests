## Running smoke tests

Package contains tests:
- without credentials
- without appstack.yml

Before running tests:

- you should install required packages:
```
sudo apt-get install python3 python3-dev git
```
and set up virtualenv:
```
./deploy/create_virtualenv.sh
```
- you should put:
```appstack.yml``` file into a directory: ```platform-tests-{version}/project/```

Run tests:
```
cd project
./run_tests.sh -e <environment> -s test_smoke --admin-username <admin_username> --admin-password <admin_password> --local-appstack appstack.yml > smoketestslog
```

Example:
```
cd project
./run_tests.sh -e gotapaas.eu -s test_smoke --admin-username admin123 --admin-password secretpass --local-appstack appstack.yml > smoketestslog
```

If there is a different ref_org than trustedanalytics, you need to run tests with extra two parameters:
```
--ref_org_name <org_name>
--ref_space_name <space_name>
```

Reading smoke tests:

If you look in smoketestslog, you should be able to see tests with their status.
Complete list of smoke tests:
```
test_all_required_apps_are_present_in_cf (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_all_required_apps_are_present_on_platform (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_all_required_apps_are_running_in_cf (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_all_required_apps_are_running_on_platform (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_all_required_brokers_are_present_in_cf (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_all_required_service_instances_are_present_in_cf (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_all_required_service_instances_are_present_on_platform (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_apps_have_the_same_details_in_cf_and_on_platform (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_spring_services_dont_expose_sensitive_endpoints (test_smoke.test_appstack.TrustedAnalyticsSmokeTest) ... ok
test_0_test_admin_can_login_to_platform (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_add_and_delete_transfer_from_file (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_add_and_delete_transfer_from_link (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_add_new_user_to_and_delete_from_org (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_add_new_user_to_and_delete_from_space (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_create_and_delete_marketplace_service_instances (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_create_and_delete_organization (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_create_and_delete_space (test_smoke.test_functional.FunctionalSmokeTests) ... ok
test_onboarding (test_smoke.test_functional.FunctionalSmokeTests) ... ok
```
