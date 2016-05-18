## API Documentation

This is simple api to communicate with OrientDB.

### Databases

* CREATE

    ```
    curl -i -X POST -H "Content-Type: application/json" -d '{"database_name": "<database_name>"}' http://<host_name>/rest/databases
    ```

* GET

    ```
    curl -i -X GET http://<host_name>/rest/databases/<database_name>
    ```

* DELETE

    ```
    curl -i -X DELETE http://<host_name>/rest/databases/<database_name>
    ```

    
### Classes

* CREATE

    ```
    curl -i -X POST -H "Content-Type: application/json" -d '{"class_name": "<class_name>"}' http://<host_name>/rest/databases/<database_name>/classes
    ```
* DELETE

    ```
    curl -i -X DELETE http://<host_name>/rest/databases/<database_name>/classes/<class_name>
    ```


### Records

* CREATE

    ```
    curl -i -X POST -H "Content-Type: application/json" -d '{"name": "John", "surname": "Doe"}' http://<host_name>/rest/databases/<database_name>/classes/<class_name>/records
    ```

* GET ALL

    ```
    curl -i -X GET http://<host_name>/rest/databases/<database_name>/classes/<class_name>/records
    ```

* GET ONE

    ```
    curl -i -X GET http://<host_name>/rest/databases/<database_name>/classes/<class_name>/records/<record_id>
    ```

* DELETE

    ```
    curl -i -X DELETE http://<host_name>/rest/databases/<database_name>/classes/<class_name>/records/<record_id>
    ```
