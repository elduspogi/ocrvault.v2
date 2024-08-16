from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai
from google.protobuf.json_format import MessageToJson
from google.api_core.exceptions import GoogleAPICallError, NotFound
import logging
import time
import mimetypes

logging.basicConfig(level=logging.INFO)

def process_document_ai(project_id, location, file_path, processor_id):
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    # full resource name of the location
    parent = client.common_location_path(project_id, location)
    processor_name = f"{parent}/processors/{processor_id}"

    processor = client.get_processor(name=processor_name)

    mime_type, _ = mimetypes.guess_type(file_path)

    # Read the file into memory
    with open(file_path, "rb") as document:
        document_content = document.read()

    # Load binary data
    raw_document = documentai.RawDocument(
        content=document_content,
        mime_type=mime_type,
    )

    #  process request config
    request = documentai.ProcessRequest(name=processor.name, raw_document=raw_document)

    result = client.process_document(request=request)

    document = result.document

    # Convert the result to JSON
    result_json = {
        "text":document.text,
    }

    return result_json


