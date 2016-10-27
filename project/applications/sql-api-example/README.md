# sql-example-api
An example usage of postgresql and mysql on Trusted Analytics Platform

How to use:

1. Clone sql-api-example repository.

2. Modify `services:[]` line in `manifest.yml` to bind services or left empty (you can bind it later in console). Remember you can bind only one db service at once.

3. Login to Cloud Foundry to your organization and space (`cf login ...`).

4. Go to `manifest.yml` containing directory and push app with `cf push`.

5. If not bound any service in `manifest.yml` then in TAP console go to Applications tab, bind one and restart app.

To change db service:

1. Stop app.

2. Unbind old service.

3. Bind new service.

4. Start app.