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
from django.utils.timezone import make_aware, is_naive


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
    VSyncRecords,
    GridSiteSyncSubmitH,
)

from monitoring.benchmarks.models import (
    BenchmarksBySubmithost,
    VJobRecords,
    VSummaries,
    VNormalisedSummaries,
)

from monitoring.iris.models import (
    IrisCloudGrid,
    VSuperSummaries,
    VAnonCloudRecords,
)

summaries_dict_standard = {
    "Site": [],
    "Month": [],
    "Year": [],
    "RecordCountPublished": [],
    "RecordStart": [],
    "RecordEnd": [],
    "SubmitHostSumm": [],
}

syncrecords_dict_standard = {
    "Site": [],
    "Month": [],
    "Year": [],
    "RecordCountInDb": [],
    "SubmitHostSync": []
}


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


def fill_summaries_dict(inpDict, row):

    fields_to_update_and_value_to_add = {
        "Site": row.Site,
        "Month": row.Month,
        "Year": row.Year,
        "RecordCountPublished": row.RecordCountPublished,
        "RecordStart": row.RecordStart,
        "RecordEnd": row.RecordEnd,
    }

    for field, value in fields_to_update_and_value_to_add.items():
        inpDict[field] = inpDict.get(field) + [value]

    if hasattr(row, "SubmitHostSumm"):
        inpDict["SubmitHostSumm"] = inpDict.get("SubmitHostSumm") + [row.SubmitHostSumm]

    return inpDict


def fill_syncrecords_dict(inpDict, row):
    inpDict["Site"] = inpDict.get("Site") + [row.Site]
    inpDict["Month"] = inpDict.get("Month") + [row.Month]
    inpDict["Year"] = inpDict.get("Year") + [row.Year]
    inpDict["RecordCountInDb"] = inpDict.get("RecordCountInDb") + [row.RecordCountInDb]
    if hasattr(row, "SubmitHostSync"):
        inpDict["SubmitHostSync"] = inpDict.get("SubmitHostSync") + [row.SubmitHostSync]
    return inpDict


def correct_dict(inpDict):
    keys_to_remove = []
    for key, val in inpDict.items():
        if len(val) == 0:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        inpDict.pop(key)
    return inpDict


# Combine Year and Month into one string (display purposes)
def get_year_month_str(year, month):
    year_string = str(year)
    month_string = str(month)
    if len(month_string) == 1:
        month_string = '0' + month_string
    return year_string + '-' + month_string


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
    views = ['VSummaries', 'VJobRecords', 'VNormalisedSummaries']
    for view in views:
        refresh_BenchmarksBySubmitHost_from_view(view)


def refresh_BenchmarksBySubmitHost_from_view(view_name):
    try:
        if view_name == 'VSummaries':
            sql_query = f"""
            SELECT DISTINCT v.Site, v.SubmitHost, v.ServiceLevelType, v.ServiceLevel, v.UpdateTime AS LatestPublish
            FROM {view_name} AS v
            JOIN (
                SELECT Site, SubmitHost, MAX(UpdateTime) AS LatestPublish
                FROM {view_name}
                WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                GROUP BY Site, SubmitHost, ServiceLevelType, ServiceLevel
            ) AS latest
            ON v.Site = latest.Site
               AND v.SubmitHost = latest.SubmitHost
               AND v.UpdateTime = latest.LatestPublish
            WHERE v.UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH);
        """
        elif view_name == 'VJobRecords':
            sql_query = f"""
            SELECT DISTINCT v.Site, v.SubmitHost, v.ServiceLevelType, v.ServiceLevel, v.UpdateTime AS LatestPublish
            FROM {view_name} AS v
            JOIN (
                SELECT Site, SubmitHost, MAX(UpdateTime) AS LatestPublish
                FROM {view_name}
                WHERE EndTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                      AND UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                GROUP BY Site, SubmitHost, ServiceLevelType, ServiceLevel
            ) AS latest
            ON v.Site = latest.Site
               AND v.SubmitHost = latest.SubmitHost
               AND v.UpdateTime = latest.LatestPublish
            WHERE v.EndTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                  AND v.UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH);
        """
        elif view_name == 'VNormalisedSummaries':
            sql_query = f"""
            SELECT DISTINCT v.Site, v.SubmitHost, v.ServiceLevelType, ROUND(v.NormalisedWallDuration / v.WallDuration, 3) AS ServiceLevel, v.UpdateTime AS LatestPublish
            FROM {view_name} AS v
            JOIN (
                SELECT Site, SubmitHost, MAX(UpdateTime) AS LatestPublish, ROUND(NormalisedWallDuration / WallDuration, 3) AS ServiceLevel
                FROM {view_name}
                WHERE UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                    AND WallDuration > 0
                GROUP BY Site, SubmitHost, ServiceLevelType, ServiceLevel
            ) AS latest
            ON v.Site = latest.Site
               AND v.SubmitHost = latest.SubmitHost
               AND v.UpdateTime = latest.LatestPublish
            WHERE v.UpdateTime > DATE_SUB(NOW(), INTERVAL 3 MONTH)
                  AND v.WallDuration > 0;
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
                    'UpdateTime': make_aware(f.LatestPublish) if is_naive(f.LatestPublish) else f.LatestPublish,
                },
                SiteName=f.Site,
                SubmitHost=f.SubmitHost,
                BenchmarkType=f.ServiceLevelType,
                BenchmarkValue=f.ServiceLevel,
                RecordType=model_class._meta.verbose_name
            )

        log.info(f"Refreshed BenchmarksBySubmitHost from {view_name}")

    except Exception:
        log.exception(f'Error while trying to refresh BenchmarksBySubmitHost from {view_name}')


def refresh_gridsitesync_submithost():
    try:
        # Fetch all published summaries
        sql_query_summaries = """
            SELECT
                Site,
                Month,
                Year,
                SUM(NumberOfJobs) AS RecordCountPublished,
                SubmitHost AS SubmitHostSumm,
                MIN(EarliestEndTime) AS RecordStart,
                MAX(LatestEndTime) AS RecordEnd
            FROM VSuperSummaries
            WHERE
                Year >= YEAR(NOW()) - 2
                AND EarliestEndTime > '1900-01-01'
                AND LatestEndTime > '1900-01-01'
            GROUP BY Site, Year, Month, SubmitHost;
        """
        fetchset_summaries = VSuperSummaries.objects.using('grid').raw(sql_query_summaries)

        # Fetch all sync records
        sql_query_syncrec = """
            SELECT
                Site,
                Month,
                Year,
                SUM(NumberOfJobs) AS RecordCountInDb,
                SubmitHost AS SubmitHostSync
            FROM VSyncRecords
            WHERE
                Year >= YEAR(NOW()) - 2
            GROUP BY Site, Year, Month, SubmitHost;
        """
        fetchset_syncrecords = VSyncRecords.objects.using('grid').raw(sql_query_syncrec)

        # Build dicts using helper methods
        summaries_dict = summaries_dict_standard.copy()
        syncrecords_dict = syncrecords_dict_standard.copy()

        for row in fetchset_summaries:
            summaries_dict = fill_summaries_dict(summaries_dict, row)

        for row in fetchset_syncrecords:
            syncrecords_dict = fill_syncrecords_dict(syncrecords_dict, row)

        summaries_dict = correct_dict(summaries_dict)
        syncrecords_dict = correct_dict(syncrecords_dict)

        # Convert to DataFrames
        df_summaries = pd.DataFrame.from_dict(summaries_dict)
        df_syncrecords = pd.DataFrame.from_dict(syncrecords_dict)

        # Merge on all keys
        df_all = df_summaries.merge(
            df_syncrecords,
            left_on=['Site', 'Month', 'Year', 'SubmitHostSumm'],
            right_on=['Site', 'Month', 'Year', 'SubmitHostSync'],
            how='outer'
        )

        # Store in the local DB
        for record in df_all.to_dict('records'):
            site = record.get("Site")
            month = record.get("Month")
            year = record.get("Year")
            submit_host = record.get("SubmitHostSumm") or record.get("SubmitHostSync")
            record_start = record.get("RecordStart")

            # Skip rows where RecordStart is missing or NaN
            if pd.isna(record_start):
                continue

            # Sanitize numeric fields
            record_count_published = record.get("RecordCountPublished")
            if pd.isna(record_count_published):
                record_count_published = 0

            record_count_in_db = record.get("RecordCountInDb")
            if pd.isna(record_count_in_db):
                record_count_in_db = 0

            GridSiteSyncSubmitH.objects.update_or_create(
                SiteName=site,
                YearMonth=get_year_month_str(year, month),
                Month=month,
                Year=year,
                SubmitHost=submit_host,
                defaults={
                    'RecordStart': record_start,
                    'RecordEnd': record.get("RecordEnd"),
                    'RecordCountPublished': record_count_published,
                    'RecordCountInDb': record_count_in_db,
                }
            )

        log.info("Refreshed GridSiteSyncSubmitH")

    except DatabaseError:
        log.exception("Error while trying to refresh GridSiteSyncSubmitH")


def refresh_iris_cloud_grid():
    try:
        sql_query = """
            SELECT
                Site,
                max(LatestEndTime) AS LatestPublish
            FROM VSuperSummaries
            WHERE LatestEndTime > DATE_SUB(NOW(), INTERVAL 1 YEAR)
            GROUP BY 1;
        """
        fetchset = VSuperSummaries.objects.using('iris_grid').raw(sql_query)

        for f in fetchset:
            IrisCloudGrid.objects.update_or_create(
                defaults={'UpdateTime': f.LatestPublish},
                SiteName=f.Site,
                SourceType=VSuperSummaries._meta.verbose_name
            )
        log.info("Refreshed IrisCloudGrid from VSuperSummaries")

        sql_query = """
            SELECT
                b.SiteName,
                b.UpdateTime AS LatestPublish
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
        fetchset = VAnonCloudRecords.objects.using('iris_cloud').raw(sql_query)

        for f in fetchset:
            IrisCloudGrid.objects.update_or_create(
                defaults={'UpdateTime': f.LatestPublish},
                SiteName=f.Site,
                SourceType=VAnonCloudRecords._meta.verbose_name
            )    

        log.info("Refreshed IrisCloudGrid from VAnonCloudRecords")

    except DatabaseError:
        log.exception('Error while trying to refresh IrisCloudGrid')


if __name__ == "__main__":
    log.info('=====================')

    # Sort log entries in ascending order by query duration
    refresh_gridsite()
    refresh_gridsitesync()
    refresh_gridsitesync_submithost()
    refresh_cloudsite()
    # refresh_BenchmarksBySubmitHost()
    refresh_iris_cloud_grid()

    log.info(
        "Data retrieval and processing attempted. "
        "Check the above logs for details on the sync status"
    )
    log.info('=====================')
