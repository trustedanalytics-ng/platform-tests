0) Go to the sample-nodejs-app
cd ~/repos/platform-tests/project/applications/sample-apps/sample-nodejs-app

1) Login to tap:
./tap address user password

2) Compile and package with maven
npm install

3) Push the application
tap push

4) Verify the application is visible
./tap apps | grep sample-nodejs-app

5) Verify that the apllication has started
./tap logs sample-nodejs-app

6) Go to sample-nodejs-app.tap.address.com
You should see a node.js logo