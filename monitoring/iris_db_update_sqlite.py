# -*- coding: utf-8 -*-
"""
- Syncs data from external database into local SQLite DB.
- It will be run as a standalone operation via cron.
"""
import configparser
import logging
import os
import sys

import django
from django.db import DatabaseError
from django.utils.timezone import make_aware, is_naive


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Find the root and the Django project
sys.path.append(BASE_DIR)

# Set up Django settings to run this `iris_db_update_sqlite.py` as standalone file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring.settings")

# Initialize and setup Django
django.setup()


# Cron jobs run in a minimal environment and lack access to Django settings.
# To ensure proper model imports and database interactions, we MUST initialize and setup Django first.
from monitoring.iris.models import (
    IrisCloudAndGrid,
    VSuperSummaries,
    VAnonCloudRecords,
)

try:
    # Read configuration from the file
    cp = configparser.ConfigParser(interpolation=None)
    file_path = os.path.join(BASE_DIR, 'monitoring', 'settings.ini')
    cp.read(file_path)

except (configparser.NoSectionError) as err:
    print("Error in configuration file. Check that file exists first: %s" % err)
    sys.exit(1)

# Set up basic logging config
logging.basicConfig(
    filename=cp.get('common', 'iris_update_logfile'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# set up the logger
log = logging.getLogger(__name__)


def refresh_iris_cloud_and_grid():
    """
    Refreshes the IrisCloudAndGrid table by performing necessary queries and updates.
    Intended to be called from the main execution block or scheduled tasks.
    """
    try:
        sql_query = """
            SELECT
                Site,
                max(LatestEndTime) AS LatestPublish
            FROM VSuperSummaries
            WHERE LatestEndTime >= NOW() - INTERVAL 6 MONTH
            AND (Site LIKE 'UK%%' OR Site LIKE 'RAL-LCG2')
            GROUP BY 1;
        """
        fetchset = VSuperSummaries.objects.using('iris_grid').raw(sql_query)

        for f in fetchset:
            IrisCloudAndGrid.objects.update_or_create(
                defaults={'UpdateTime': make_aware(f.LatestPublish) if is_naive(f.LatestPublish) else f.LatestPublish},
                SiteName=f.Site,
                SourceType=VSuperSummaries._meta.verbose_name
            )
        log.info("Refreshed IrisCloudAndGrid from VSuperSummaries")

        sql_query = """
            SELECT
                SiteName,
                MAX(UpdateTime) AS LatestPublish
            FROM VAnonCloudRecords
            WHERE UpdateTime >= NOW() - INTERVAL 6 MONTH
            GROUP BY SiteName;
        """
        fetchset = VAnonCloudRecords.objects.using('iris_cloud').raw(sql_query)

        for f in fetchset:
            IrisCloudAndGrid.objects.update_or_create(
                defaults={'UpdateTime': make_aware(f.LatestPublish) if is_naive(f.LatestPublish) else f.LatestPublish},
                SiteName=f.SiteName,
                SourceType=VAnonCloudRecords._meta.verbose_name
            )

        log.info("Refreshed IrisCloudAndGrid from VAnonCloudRecords")

    except DatabaseError:
        log.exception('Error while trying to refresh IrisCloudAndGrid')


def main():
    """
    Entry point for running the iris cloud and grid data refresh process.
    """
    log.info('=====================')

    refresh_iris_cloud_and_grid()

    log.info(
        "Data retrieval and processing attempted."
        "Check the above logs for details on the sync status."
    )
    log.info('=====================')


if __name__ == "__main__":
    main()
