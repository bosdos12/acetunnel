import flask
# Flask, request, jsonify
from flask_cors import CORS
from hashlib import sha256
import uuid



app = flask.Flask(__name__)
CORS(app)


our_users = [
    {"email": "awk", "password": "4a52340305bdd3b0c25b282c12d6e94b2fe8351b5146b756edcaca4a085b521b"}
]

requests_queue = []
responses_pool = []

def validate_userF(email, password):
    hashed_pass = sha256(password.encode("utf-8")).hexdigest()
    for user in our_users:
        print(user)
        if user["email"] == email and user["password"] == hashed_pass:
            print("user exists")
            print(user)
            return True
    return False

# we are so smart we will literally just send the request to the other server :)
def validate_app_exists(app_name):
    print(app_name);

def add_request_to_queueF(full_request, app_name, app_route):
    print(full_request)
    request_id = uuid.uuid4()
    requests_queue.append({
        "full_request": full_request,
        "request_id": request_id,
        "app_name": app_name,
        "app_route": app_route
        
    })
    
    return request_id

def delete_request_from_query(request_id):
    request_index = 0
    for request in requests_queue:
        if str(request["request_id"]) == str(request_id):
            del requests_queue[request_index]
            break

def get_response_from_pool(request_id):
    while True:
        response_index = 0
        for response in responses_pool:
            print(str(request_id) + " " + str(response["response_id"]))
            if str(response["response_id"]) == str(request_id):
                del responses_pool[response_index]
                delete_request_from_query(request_id)
                return response["response"]
            response_index += 1

@app.route("/<path:app_name>/<path:app_route>")
def app_page(app_name, app_route):
    
    # Make sure there is an app with the given name
    validate_app_exists(app_name)
    

    # Add the request to the queue
    # print(flask.request.method + " " + app_route + flask.request.environ.get("SERVER_PROTOCOL"))
    request_id = add_request_to_queueF(flask.request, app_name, app_route)
    
    # Wait until request is on the responses pool and return when here
    return get_response_from_pool(request_id)

@app.get("/test")
def lil_test():
    return "<h1>sdfgfg</h1>";

@app.post("/add_to_responses_pool")
def add_to_responses_pool():
    data = flask.request.get_json()
    if "request_id" not in data or "response" not in data:
        return flask.jsonify({"validity": False, "": "Request ID and Response Body Required"}), 400
    responses_pool.append({
        "response_id": data["request_id"],
        "response": data["response"]
    })
    return {}, 200


@app.post('/login')
def login():
    # Get JSON data from the request body
    data = request.get_json()
    print(data)
    if "email" not in data or "password" not in data:
        return flask.jsonify({"validity": False, "cause": "email and password needed"}), 400
    else:
        if validate_userF(data["email"], data["password"]):
            return flask.jsonify({"validity": True}), 200
        else:
            return flask.jsonify({"validity": False, "cause": "Auth failed."}), 400

@app.get("/metrics")
def metrics():
    print("SYSTEM METRICSSS")
    requestsqueuemetrics = ""
    responsespoolmetrics = ""
    print(requests_queue)
    for request in requests_queue:
        requestsqueuemetrics += f"""
            <div class="metriclistitem">
                <div class="metricitembox"><p>{request["request_id"]}</p></div>
                <div class="metricitembox"><p>{request["app_name"]}</p></div>
                <div class="metricitembox"><p>{request["app_route"]}</p></div>
            <div>
        """
    
    print(responses_pool)
    for response in responses_pool:
        responsespoolmetrics += f"""
            <div class="metriclistitem">
                <div class="metricitembox"><p>{response["response_id"]}</p></div>
                <div class="metricitembox"><p>{response["response"]}</p></div>
            <div>
        """


    return """
<html>
        <style>
            .metriclistitem {
                width: 50%;
                margin-right: auto;
                margin-left: auto;
                height: 50px;
                border: 1px solid black;
                display: flex;
                flex-direction: row;
                flex-align: space-between;
            }

            .metricitembox {
                width: 100%;
                height: 50px;
                text-align: center;
            }
        </style>
        <div style="width: 100%; height: 100%;">
            """ + requestsqueuemetrics + """

            <br/><br/><br/><hr/>

            """ + responsespoolmetrics + """

        </div>
        <script>
            const interval = setInterval(() => window.location.reload(), 5000);
        </script>
    <html>
    """

if __name__ == "__main__":
    app.run(debug=True)
