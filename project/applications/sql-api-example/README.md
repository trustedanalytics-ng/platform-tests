# sql-example-api
An example usage of postgresql and mysql on Trusted Analytics Platform

##Usage

<!---
This should be commented till working implementations of binding mechanism during pushing application
0. Modify ' "bindings": null ' in manifest.json to bind services or left empty (you can bind it later in CLI).

-->
1. Login to TAP CLI

    `./tap login <address> <username> <password> `

2. Ensure you are in sql-api-example directory (it must contain 'manifest.json') and execute push command

    `./tap push`

3. Bind instance of database (if there was no specified bindings in manifest.json)

    `./tap bind-instance  <db_instance_name> <app_name> `


##Changing database

1. Unbind old instance

2. Bind new instance.



##Running app locally

You need to export environmental variables, follow this schema:

` <INSTANCE_NAME>_MYSQL_<VARIABLE>`  *(if using mysql db)*

or ` <INSTANCE_NAME>_POSTGRES_<VARIABLE>` *(if using postgres db)*

Variables to set: `DBNAME, USERNAME, PASSWORD, HOSTNAME`

i. e.

```
    MYSQL_DB_MYSQL_DBNAME = <dbname>
    MYSQL_DB_MYSQL_USERNAME = <username>
    MYSQL_DB_MYSQL_PASSWORD = <password>
    MYSQL_DB_MYSQL_HOSTNAME = <hostname>
```
Exporting `APP_PORT` and `LOG_LEVEL` is optional.
By default ` APP_PORT = 80 ` and ` LOG_LEVEL=DEBUG `.

##Using and testing app with curl

1. Create a table:

`curl -X POST -H "Authorization: bearer $TOKEN"  -H "Content-type: application/json" -d '{"table_name": "tab_name", "columns":[{"name": "col_name", "type": "VARCHAR", "max_len":10}]}' http://<app_address>/tables`

2. Display table content:

`curl -X GET -H "Authorization: bearer $TOKEN" http://<app_address>/tables`

3. Display table columns:

`curl -X  GET -H "Authorization: bearer $TOKEN" http://<app_address>/tables/<tab_name>/columns`

4. Display all table rows:

`curl -X  GET -H "Authorization: bearer $TOKEN" http://<app_address>/tables/<tab_name>/rows`

5. Create row:

`curl -X POST -H "Authorization: bearer $TOKEN"  -H "Content-type: application/json" -d '[{"column_name":"col_name", "value":"some_value"}, {"column_name":"col_name2", "value":1}, {"column_name":"col_name3", "value":true}]' http://<app_address>/tables/<tab_name>/rows`

6. Remove table:

`curl -X  DELETE -H "Authorization: bearer $TOKEN" http://<app_address>/tables/<tab_name>`

7. Remove specific row:

`curl -X  DELETE -H "Authorization: bearer $TOKEN" http://<app_address>/tables/<tab_name>/rows/<row_id>`

8. Display row content:

`curl -X  GET -H "Authorization: bearer $TOKEN" http://<app_address>/tables/<tab_name>/rows/<row_id>`

9. Update value for specific column in specific row:

`curl -X  PUT -H "Authorization: bearer $TOKEN" -H "Content-type: application/json" -d '[{"column_name":"col_name", "value":"some_value"}]' http://<app_address>/tables/<tab_name>/rows/<row_name>`

