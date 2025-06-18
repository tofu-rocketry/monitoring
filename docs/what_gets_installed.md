For Django to work with apache, it is common to have a venv within the app, where django and djangorestframework get installed. Other packages needed for the app to work are installed by Aquilon outside the venv.

## Packages installed by Aquilon outside the venv
Following the config file that Aquilon uses, the following are the packages installed:
- `httpd`
- `python3-mod_wsgi` (for apache to work with django)
- `python3-devel`
- `gcc` (needed for dependencies)
- `mariadb`
- `tar`

## Packages installed within the venv
Within venv, the following are installed through pip:
- `djangorestframework` (3.15.1)
- `pymysql` (1.0.2) (needed for mariadb to work)
- `pandas` (1.1.5) (needed by the app)
- `django` (3.2.25)
- `pytz` (2025.2)

Note that when the version of the packages is specified, the app would not work with a different version (due to dependencies conflicts).

Is is also important to note that different types of OS require different packages to be installed.
The above are the packages that allow the app to work on a Rocky8.
