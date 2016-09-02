0) Go to the sample-python-directory
cd path/to/sample-python-directory

1) Login to tap:
./tap address user password

2) Set proper proxies (if needed) in run.sh

3) Push the application
./tap push

4) Verify the application is visible
./tap apps | grep sample-python-app

5) Verify that the apllication has started
./tap logs sample-python-app

6) Go to sample-python-app.tap.address.com
You should see: "Test app"
