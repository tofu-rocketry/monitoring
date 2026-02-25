## Steps to set up a blackhole database for local testing of the loading validator

As part of the validator app, records are sent to a local instance of the apel
loader class, to test if they load into an apel server database correctly.
This is important as some errors in a record won't be detected by the syntax
validator, but will still cause a record to fail to load.

These records are loaded into a database with blackhole engined tables - these
tables allow insert commands, but don't store any rows or data, as data is
discarded on write. This allows complete checking that a record can be
successfully loaded to a database, without having to deal with data being stored.

The local instance of the apel loader class is within `monitoring/views.py`, and
uses `monitoring/validatorSettings.py` to pull configuration settings from
`monitoring/settings.ini` about the blackhole validator database.

Steps to set up a blackhole-engined version of the apel server database:

1. Ensure maraidb is started and enabled:
    - `sudo su`
    - `sudo systemctl start mariadb`
    - `sudo systemctl enable mariadb`

2. Login to mariadb with root:
    - `mysql -u root -p`

3. Install the blackhole plugin, and then verify it is installed:
    - `INSTALL SONAME 'ha_blackhole';`
    - `SHOW ENGINES;` (should be a row with BLACKHOLE and support as YES).

4. Exit mariadb:
    - `exit;`

5. Set the global default storage engine to blackhole, so that when the database
    schema gets applied, tables are created with the blackhole engine:
    - find where your mariadb settings are stored (for me it was `/etc/my.cnf.d/`).
    - either edit `server.cnf` or create a new `blackhole.cnf` file (what I did).
    - in that file:
    ```
    [mysqld]
    default-storage-engine=BLACKHOLE
    ```
    - This config setting means that any create table statements without an engine
    defined will be set to a blackhole engine by default.

6. Restart mariadb:
    - `sudo systemctl restart mariadb`
    - Running `SHOW ENGINES;` within mariadb at this point should show the Blackhole
    row with support as DEFAULT;

7. Create the database:
    - `mysql -u root -p`
    - `CREATE DATABASE validator_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
    - `CREATE USER 'your_name'@'localhost' IDENTIFIED BY 'your_password';`
    - `GRANT ALL PRIVILEGES ON validator_db.* TO 'your_name'@'localhost';`
    - `FLUSH PRIVILEGES;`
    - `exit;`

8. Apply the apel server schema to the database:
    - the schema is at https://github.com/apel/apel/blob/dev/schemas/server.sql.
    - to do this step, I used my locally cloned version of apel as the
    schema file path.
    - `mysql -u root validator_db < path_to_apel/schemas/server.sql`

9. Verify the schema applied correctly, and that the correct tables use a
    blackhole engine:
    - `mysql -u your_name -p`
    - `SHOW DATABASES;`
    - `USE validator_db;`
    - `SHOW TABLES;` (check all tables are there)
    - `SHOW TABLE STATUS;` (check that all tables either have a BLACKHOLE or
    NULL engine)

10. Populate settings.ini with the following, adding in the correct values:
    - ```
      [db_validator]
      backend=mysql
      hostname=localhost
      name=validator_db
      password=
      port=3306
      username=
      ```
    - these config options are picked up by the `validatorSettings.py` file.
