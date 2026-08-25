For Django to work with Apache, it is common to have a venv within the app, where Django and the Django REST framework get installed. Other packages needed for the app to work are installed by Aquilon outside the venv.

## Packages installed by Aquilon outside the venv
Following the config file that Aquilon uses, the following are the packages installed:
- `httpd`
- `python3-mod_wsgi` (for apache to work with django)
- `python3-devel`
- `gcc` (needed for dependencies)
- `mariadb`
- `tar`
- `virtualenv` for Python installed using `pip` via the bootstrap script

## Packages installed within the venv
Within the venv, the following packages, and their dependencies, are installed through pip:
- `Django`
- `djangorestframework`
- `numpy` (pandas dependency)
- `pandas` (needed by the app)
- `PyMySQL` (needed for mariadb to work)
- `pytz`

See the `requirements.txt` file for the specific versions installed.

Note that when the version of the packages is specified, the app would not work with a different version (due to dependency conflicts).

Is is also important to note that different types of OS require different packages to be installed.
The above are the packages that allow the app to work on Rocky 9.
