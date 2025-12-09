from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apel.db.loader.record_factory import RecordFactory


@require_http_methods(["GET", "POST"])
def index(request):
    """
    Validates inputted records using Apel RecordFactory,
    when html form is submitted.
    """
    template_name = "validator/validator_index.html"
    input_record = ""
    output = ""


    def validate(record: str) -> str:
        """
        Validated record(s) passed in, and returns the result
        """
        if not record:
            return "Please enter a record to be validated."

        record = record.strip()

        try:
            recordFactory = RecordFactory()

            result = recordFactory.create_records(record)

            return str(result)

        except Exception as e:
            return str(e)


    # On form submission, trigger record validation
    if request.method == "POST":
        input_record = request.POST.get("input_record", "")
        try:
            output = validate(input_record)
        except Exception as e:
            output = f"Error during validation: {e}"

    context = {
        "input_record": input_record,
        "output": output,
    }

    return render(request, template_name, context)
