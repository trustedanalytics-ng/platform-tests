0) Go to the sample-go-app
cd ~/repos/platform-tests/project/applications/sample-apps/sample-go-app

1) Login to tap:
./tap address user password

2) Build go executable
./build.sh

3) Push the application
tap push

4) Verify the application is visible
./tap apps | grep sample-go-app

5) Verify that the apllication has started
./tap logs sample-go-app

6) Go to sample-java-app.tap.address.com
You should see: "OK"
