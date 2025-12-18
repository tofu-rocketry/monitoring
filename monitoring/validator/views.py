from django.shortcuts import render
from django.views.decorators.http import require_http_methods

# Apel record-checking class imports
from apel.db.loader.record_factory import RecordFactory, RecordFactoryException
from apel.db.records.record import InvalidRecordException

# Apel record-type class imports
from apel.db.records.job import JobRecord, JobRecord04
from apel.db.records.summary import SummaryRecord, SummaryRecord04
from apel.db.records.normalised_summary import NormalisedSummaryRecord, NormalisedSummaryRecord04
from apel.db.records.sync import SyncRecord
from apel.db.records.cloud import CloudRecord
from apel.db.records.cloud_summary import CloudSummaryRecord


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Validates inputted records using the Apel record validation methods.
    It either validates a record against a specific type or against all types, depending on what record_type
        option was chosen on the html template. The default is `All`.
    The input record, record type and validation output are then returned to the html template as context on get
        request, so that the html page retains its information/context when refreshing the page or submitting the form.
    """
    template_name = "validator/validator_index.html"
    input_record = ""
    record_type = "All"
    output = ""

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


    def validate(record: str, record_type: str) -> str:
        """
        Validated record(s) and record_type passed in from the html page template.
        If record type is all, make use of the create_records apel method (expects a record header).
        Else, make use of the _create_record_objects apel method (expects there to be no record header).
        If the record is valid, return a "valid record" string.
        If the record is invalid, an InvalidRecordException or RecordFactoryException is raised by the Apel methods.
        Catch these exceptions and return the exception information.
        """
        if not record:
            return "Please enter a record to be validated."

        record = record.strip()

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


    # On form submission, trigger record validation
    if request.method == "POST":
        input_record = request.POST.get("input_record", "")
        record_type = request.POST.get("record_type", "")
        output = validate(input_record, record_type)

    context = {
        "input_record": input_record,
        "record_type": record_type,
        "output": output,
    }

    return render(request, template_name, context)
