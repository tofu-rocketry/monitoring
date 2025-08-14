# -*- coding: utf-8 -*-
"""
`db_update_sqlite.py` - Syncs data from external database into local SQLite DB.
                      -  It will be run as a standalone operation via cron.
"""
import configparser
import logging
import os
import sys

import django
from django.db import DatabaseError
import pandas as pd


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Find the root and the Django project
sys.path.append(BASE_DIR)

# Set up Django settings to run this `db_update_sqlite.py` as standalone file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring.settings")

# Initialize and setup Django
django.setup()


# Cron jobs run in a minimal environment and lack access to Django settings.
# To ensure proper model imports and database interactions, we MUST initialize and setup Django first.
from monitoring.publishing.models import (
    GridSite,
    CloudSite,
    GridSiteSync,
    VAnonCloudRecord,
    VSuperSummaries,
    VSyncRecords
)

from monitoring.publishing.views import (
    summaries_dict_standard,
    syncrecords_dict_standard,
    correct_dict,
    fill_summaries_dict,
    fill_syncrecords_dict,
    get_year_month_str
)

from monitoring.benchmarks.models import (
    BenchmarksBySubmithost,
    VJobRecords,
    VSummaries,
    VNormalisedSummaries,
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
    filename=cp.get('common', 'logfile'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# set up the logger
log = logging.getLogger(__name__)


def determine_sync_status(f):
    """
    Helper to determine sync status between published and the database record counts.
    """
    RecordCountPublished = f.get("RecordCountPublished")
    RecordCountInDb = f.get("RecordCountInDb")
    rel_diff1 = abs(RecordCountPublished - RecordCountInDb)/RecordCountInDb
    rel_diff2 = abs(RecordCountPublished - RecordCountInDb)/RecordCountPublished
    if rel_diff1 < 0.01 or rel_diff2 < 0.01:
        syncstatus = "OK"
    else:
        syncstatus = "ERROR [ Please use the Gap Publisher to synchronise this dataset]"
    return syncstatus


def refresh_gridsite():
    try:
        sql_query = """
            SELECT
                Site,
                max(LatestEndTime) AS LatestPublish
            FROM VSuperSummaries
            WHERE LatestEndTime > DATE_SUB(NOW(), INTERVAL 1 YEAR)
            GROUP BY 1;
        """
        fetchset = VSuperSummaries.objects.using('grid').raw(sql_query)

        for f in fetchset:
            GridSite.objects.update_or_create(
                defaults={'updated': f.LatestPublish},
                SiteName=f.Site
            )

        log.info("Refreshed GridSite")

    except DatabaseError:
        log.exception('Error while trying to refresh GridSite')


def refresh_cloudsite():
    try:
        sql_query = """
            SELECT
                b.SiteName,
                COUNT(DISTINCT VMUUID) as VMs,
                CloudType,
                b.UpdateTime
            FROM(
                SELECT
                    SiteName,
                    MAX(UpdateTime) AS latest
                FROM VAnonCloudRecords
                WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 1 YEAR)
                GROUP BY SiteName
            )
            AS a
            INNER JOIN VAnonCloudRecords
            AS b
            ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest
            GROUP BY SiteName;
        """
        fetchset = VAnonCloudRecord.objects.using('cloud').raw(sql_query)

        for f in fetchset:
            CloudSite.objects.update_or_create(
                defaults={
                    'Vms': f.VMs,
                    'Script': f.CloudType,
                    'updated': f.UpdateTime
                },
                SiteName=f.SiteName
            )

        log.info("Refreshed CloudSite")

    except DatabaseError:
        log.exception('Error while trying to refresh CloudSite')


def refresh_gridsitesync():
    try:
        # The condition on EarliestEndTime and LatestEndTime is necessary to avoid error by pytz because of dates like '00-00-00'
        sql_query_summaries = """
            SELECT
                Site,
                Month,
                Year,
                SUM(NumberOfJobs) AS RecordCountPublished,
                MIN(EarliestEndTime) AS RecordStart,
                MAX(LatestEndTime) AS RecordEnd
            FROM VSuperSummaries
            WHERE
                Year >= YEAR(NOW()) - 2 AND
                EarliestEndTime>'1900-01-01' AND
                LatestEndTime>'1900-01-01'
            GROUP BY
                Site, Year, Month;
        """
        fetchset_Summaries = VSuperSummaries.objects.using('grid').raw(sql_query_summaries)

        sql_query_syncrec = """
            SELECT
                Site,
                Month,
                Year,
                SUM(NumberOfJobs) AS RecordCountInDb
            FROM VSyncRecords
            WHERE
                Year >= YEAR(NOW()) - 2
            GROUP BY
                Site, Year, Month;
        """
        fetchset_SyncRecords = VSyncRecords.objects.using('grid').raw(sql_query_syncrec)

        # Create empty dicts that will become dfs to be combined
        summaries_dict = summaries_dict_standard.copy()
        syncrecords_dict = syncrecords_dict_standard.copy()

        # Fill the dicts with the fetched data
        for row in fetchset_Summaries:
            summaries_dict = fill_summaries_dict(summaries_dict, row)
            summaries_dict = correct_dict(summaries_dict)
        for row in fetchset_SyncRecords:
            syncrecords_dict = fill_syncrecords_dict(syncrecords_dict, row)
            syncrecords_dict = correct_dict(syncrecords_dict)

        # Merge data from VSuperSummaries and VSyncRecords into one df
        df_Summaries = pd.DataFrame.from_dict(summaries_dict)
        df_SyncRecords = pd.DataFrame.from_dict(syncrecords_dict)
        df_all = df_Summaries.merge(
            df_SyncRecords,
            left_on=['Site', 'Month', 'Year'],
            right_on=['Site', 'Month', 'Year'],
            how='inner'
        )
        fetchset = df_all.to_dict('index')

        # Determine SyncStatus based on the difference between records published and in db
        for f in fetchset.values():
            f['SyncStatus'] = determine_sync_status(f)

            # Combined primary keys outside the default dict
            GridSiteSync.objects.update_or_create(
                defaults={
                    'RecordStart': f.get("RecordStart"),
                    'RecordEnd': f.get("RecordEnd"),
                    'RecordCountPublished': f.get("RecordCountPublished"),
                    'RecordCountInDb': f.get("RecordCountInDb"),
                    'SyncStatus': f.get("SyncStatus"),
                },
                YearMonth=get_year_month_str(f.get("Year"), f.get("Month")),
                SiteName=f.get("Site"),
                Month=f.get("Month"),
                Year=f.get("Year"),
            )
        log.info("Refreshed GridSiteSync")

    except DatabaseError:
        log.exception('Error while trying to refresh GridSiteSync')

def refresh_BenchmarksBySubmitHost():
    try:
        # sql_query = """
        #     SELECT
        #         Site,
        #         SubmitHost,
        #         ServiceLevelType,
        #         ServiceLevel,
        #         max(UpdateTime) AS LatestPublish
        #     FROM VJobRecords
        #     WHERE EndTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
        #         AND UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
        #     GROUP BY Site, SubmitHost;
        # """
        # fetchset = VJobRecords.objects.raw(sql_query)
        sql_query = """
            SELECT
                Site,
                SubmitHost,
                ServiceLevelType,
                ServiceLevel,
                max(UpdateTime) AS LatestPublish
            FROM VSummaries
            WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
            GROUP BY Site, SubmitHost;
        """
        fetchset = VSummaries.objects.using('grid').raw(sql_query)

        for f in fetchset:
            BenchmarksBySubmithost.objects.update_or_create(
                defaults={
                    'UpdateTime': f.LatestPublish,
                    'SourceView': 'VSummaries'
                    },
                SiteName=f.Site,
                SubmitHost=f.SubmitHost,
                ServiceLevelType=f.ServiceLevelType,
                ServiceLevel=f.ServiceLevel,
            )

        log.info("Refreshed BenchmarksBySubmitHost")

    except DatabaseError:
        log.exception('Error while trying to refresh BenchmarksBySubmitHost')        


def refresh_BenchmarksBySubmitHost():
    # views = ['VSummaries', 'VJobRecords', 'VNormalisedSummaries']
    views = ['VSummaries', 'VNormalisedSummaries']
    for view in views:
        refresh_BenchmarksBySubmitHost_from_view(view)


def refresh_BenchmarksBySubmitHost_from_view(view_name):
    try:        
        if view_name == 'VSummaries':
            sql_query = f"""
            SELECT
                Site,
                SubmitHost,
                ServiceLevelType,
                ServiceLevel,
                max(UpdateTime) AS LatestPublish
            FROM {view_name}
            WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
            GROUP BY Site, SubmitHost;
        """
        elif view_name == 'VJobRecords':
            sql_query = f"""
            SELECT
                Site,
                SubmitHost,
                ServiceLevelType,
                ServiceLevel,
                max(UpdateTime) AS LatestPublish
            FROM {view_name}
            WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
            GROUP BY Site, SubmitHost;
        """
        elif view_name == 'VNormalisedSummaries':
            sql_query = f"""
            SELECT
                Site,
                SubmitHost,
                ServiceLevelType,
                (NormalisedWallDuration / WallDuration) AS ServiceLevel,
                max(UpdateTime) AS LatestPublish
            FROM {view_name}
            WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                  AND WallDuration > 0
            GROUP BY Site, SubmitHost;
        """
        else:
            log.warning(f"Unknown view name: {view_name}")
            return

        # Dynamically get the model class from globals
        model_class = globals()[view_name]
        fetchset = model_class.objects.using('grid').raw(sql_query)

        for f in fetchset:
            BenchmarksBySubmithost.objects.update_or_create(
                defaults={
                    'UpdateTime': f.LatestPublish,
                    'SourceView': view_name
                },
                SiteName=f.Site,
                SubmitHost=f.SubmitHost,
                ServiceLevelType=f.ServiceLevelType,
                ServiceLevel=f.ServiceLevel,
            )

        log.info(f"Refreshed BenchmarksBySubmitHost from {view_name}")

    except Exception:
        log.exception(f'Error while trying to refresh BenchmarksBySubmitHost from {view_name}')      


if __name__ == "__main__":
    log.info('=====================')

    refresh_gridsite()
    refresh_cloudsite()
    refresh_gridsitesync()
    refresh_BenchmarksBySubmitHost()

    log.info(
        "Data retrieval and processing attempted. "
        "Check the above logs for details on the sync status"
    )
    log.info('=====================')
