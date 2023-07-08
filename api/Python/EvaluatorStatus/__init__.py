import azure.functions as func
import azure.durable_functions as df
import json


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    client = df.DurableOrchestrationClient(starter)

    instance_id = req.route_params["id"]

    response = await client.get_status(instance_id)

    if response.instance_id is None:
        return func.HttpResponse("Job not found", status_code=404)

    return func.HttpResponse(json.dumps({
        "id": response.instance_id,
        "status": response.runtime_status.value,
        "result": response.output
    }))