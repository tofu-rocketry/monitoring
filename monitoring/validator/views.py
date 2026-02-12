from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# Apel loader and record-checking class imports
from apel.db.loader.loader import Loader
from apel.db.loader.record_factory import RecordFactory, RecordFactoryException
from apel.db.records.record import InvalidRecordException

# Apel record-type class imports
from apel.db.records.job import JobRecord, JobRecord04
from apel.db.records.summary import SummaryRecord, SummaryRecord04
from apel.db.records.normalised_summary import NormalisedSummaryRecord, NormalisedSummaryRecord04
from apel.db.records.sync import SyncRecord
from apel.db.records.cloud import CloudRecord
from apel.db.records.cloud_summary import CloudSummaryRecord

# Validator db configuration
from monitoring import validatorSettings

# Python tempfile for temporary apel queues
import tempfile


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Validates inputted records using the Apel record validation methods, or tests they load correctly using an
        instance of the Apel loader.
    For validation:
        It either validates a record against a specific type or against all types, depending on what record_type
        option was chosen on the html template. The default is `All`.
    For loading:
        It both validates the record's syntax against all types, and checks it can load into a database correctly
        using the Apel loader class. The database uses a blackhole engine, so no data is stored.
    The input record, record type, submission type and validation output are then returned to the html template
        as context on get request, so that the html page retains its information/context when refreshing the page
        or submitting the form.
    """

    template_name = "validator/validator_index.html"
    input_record = ""
    record_type = "All"
    submission_type = ""
    output = ""

    # On form submission, check record isnt empty.
    # Then trigger record validation or record loading, based on submission type
    if request.method == "POST":
        input_record = request.POST.get("input_record", "")
        record_type = request.POST.get("record_type", "")
        submission_type = request.POST.get("submission_type", "")

        if input_record:
            input_record = input_record.strip()

            if submission_type == "load":
                output = load(input_record)
            else:
                output = validate(input_record, record_type)
        else:
            output = "Please enter a record to be validated."

    context = {
        "input_record": input_record,
        "record_type": record_type,
        "submission_type": submission_type,
        "output": output,
    }

    return render(request, template_name, context)


def validate(record: str, record_type: str) -> str:
    """
    Record(s) and record_type passed in from the html page template.
    If record type is all, make use of the `create_records` apel method (expects a record header).
    Else, make use of the `_create_record_objects` apel method (expects there to be no record header).
    If the record is valid, return a "valid record" string.
    If the record is invalid, an InvalidRecordException or RecordFactoryException is raised by the Apel methods.
    Catch these exceptions and return the exception information.
    """

    # Map record_type string to record_type class
    # String is always exact as determined through html form selection option
    record_map = {
        "JobRecord": JobRecord,
        "JobRecord04": JobRecord04,
        "SummaryRecord": SummaryRecord,
        "SummaryRecord04": SummaryRecord04,
        "NormalisedSummaryRecord": NormalisedSummaryRecord,
        "NormalisedSummaryRecord04": NormalisedSummaryRecord04,
        "SyncRecord": SyncRecord,
        "CloudRecord": CloudRecord,
        "CloudSummaryRecord": CloudSummaryRecord,
    }

    try:
        recordFactory = RecordFactory()

        if record_type == "All":
            result = recordFactory.create_records(record)
        else:
            record_class = record_map[record_type]
            result = recordFactory._create_record_objects(record, record_class)

        if "Record object at" in str(result):
            return "Record(s) valid!"

        return str(result)

    except (InvalidRecordException, RecordFactoryException) as e:
        return str(e)

def load(record: str) -> str:
    """
    Record passed in from the html page template.
    Create a loader instance, making use of a tempfile directory for the queues and pidfile creation
    Startup loader and then pass record(s) and blank signer into the `load_msg` method
    Make use of a blackhole database, which loads but doesn't store any data.
    If the record loads successfully, return a "valid record" string.
    If the record fails to load, an exception is raised by the Apel methods.
    Catch these exceptions and return the exception information.
    """

    try:
        validatorDB = validatorSettings.VALIDATOR_DB

        # Set the tempfile temporary directory within /tmp
        tempfile.tempdir = "/tmp"

        qpath = tempfile.gettempdir()
        db_backend = validatorDB.get("ENGINE")
        db_host = validatorDB.get("HOST")
        db_port = int(validatorDB.get("PORT"))
        db_name = validatorDB.get("NAME")
        db_username = validatorDB.get("USER")
        db_password = validatorDB.get("PASSWORD")
        pidfile = ""
        signer = ""

        loader = Loader(qpath, record, db_backend, db_host, db_port, db_name, db_username, db_password, pidfile)

        loader.startup()

        loader.load_msg(record, signer)

        loader.shutdown()

        return("Record(s) will load successfully!")

    except Exception as e:
        return str(e)
