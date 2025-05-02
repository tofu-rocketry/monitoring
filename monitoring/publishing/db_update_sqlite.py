# -*- coding: utf-8 -*-
"""
`db_update_sqlite.py` - Syncs data from external database into local SQLite DB.
                      -  It will be run as a standalone operation via cron.
"""
import configparser
import logging
import os
import sys

import pandas as pd
import django
from django.db import DatabaseError


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Find the root and the Django project
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

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

# Set up Django settings to run this `db_update_sqlite.py` as standalone file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring.settings")

# Initialize and setup Django
django.setup()


from monitoring.publishing.models import (
    GridSite,
    CloudSite,
    GridSiteSync,
    VAnonCloudRecord,
    VSuperSummaries,
    VSyncRecords
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


def get_year_month_str(year, month):
    year_string = str(year)
    month_string = str(month)
    if len(month_string) == 1:
        month_string = '0' + month_string
    return year_string + '-' + month_string

def determine_sync_status(f):
    RecordCountPublished = f.get("RecordCountPublished")
    RecordCountInDb = f.get("RecordCountInDb")
    rel_diff1 = abs(RecordCountPublished - RecordCountInDb) / RecordCountInDb
    rel_diff2 = abs(RecordCountPublished - RecordCountInDb) / RecordCountPublished
    if rel_diff1 < 0.01 or rel_diff2 < 0.01:
        return "OK"
    return "ERROR [ Please use the Gap Publisher to synchronise this dataset]"


def refresh_gridsite():
    try:
        sql_query = """
            SELECT
                Site,
                max(LatestEndTime) AS LatestPublish
            FROM VSuperSummaries
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
                WHERE UpdateTime>'2023-01-01'
                GROUP BY SiteName
            )
            AS a
            INNER JOIN VAnonCloudRecords
            AS b
            ON b.SiteName = a.SiteName AND b.UpdateTime = a.latest
            GROUP BY SiteName;
        """
        fetchset =  VAnonCloudRecord.objects.using('cloud').raw(sql_query)

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


if __name__ == "__main__":

    refresh_gridsite()
    refresh_cloudsite()
    refresh_gridsitesync()

    log.info(
        "Data retrieval from the database backend(s) is completed and "
        "successfully synchronized with the local SQLite database."
    )
