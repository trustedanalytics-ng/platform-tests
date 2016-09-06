0) Go to the sample-java-application
cd ~/repos/platform-tests/project/applications/sample-apps/sample-java-application

1) Login to tap:
./tap address user password

2) Compile and package with maven
mvn compile
mvn package

3) Push the application
tap push

4) Verify the application is visible
./tap apps | grep sample-java-app

5) Verify that the apllication has started
./tap logs sample-java-app

6) Go to sample-java-app.tap.address.com
You should see: "hello world"
