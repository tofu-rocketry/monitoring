from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apel.db.loader.record_factory import RecordFactory

# Apel record class imports
from apel.db.records.job import JobRecord, JobRecord04
from apel.db.records.summary import SummaryRecord, SummaryRecord04
from apel.db.records.normalised_summary import NormalisedSummaryRecord, NormalisedSummaryRecord04
from apel.db.records.sync import SyncRecord
from apel.db.records.cloud import CloudRecord
from apel.db.records.cloud_summary import CloudSummaryRecord


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Validates inputted records using Apel RecordFactory,
    when html form is submitted.
    """
    template_name = "validator/validator_index.html"
    input_record = ""
    record_type = "All"
    output = ""

    # Map record_type string to record_type class
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
        Validated record(s) passed in, and returns the result
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
            else:
                return str(result)

        except Exception as e:
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
