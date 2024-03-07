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


sessions_list  = [] # session_name, session_owner (email)
requests_queue = [] # full_request, request_id, session_name, app_route
responses_pool = [] # response_id, response

def validate_userF(email, password, check_if):

    # if its a check_if_user_exists request, the data is already hashed on clients device;
    # if its a normal login request, normal password is entered, so hash
    if check_if:
        hashed_pass = password
    else:
        hashed_pass = sha256(password.encode("utf-8")).hexdigest()
    
    for user in our_users:
        print(user)
        if user["email"] == email and user["password"] == hashed_pass:
            print("user exists")
            print(user)
            return True
    return False

# we are so smart we will literally just send the request to the other server :)
def validate_session_exists(session_name):
    for session in sessions_list:
        if session_name == str(session["session_name"]):
            return True
    return False

def add_request_to_queueF(full_request, session_name, app_route):
    request_id = uuid.uuid4()
    requests_queue.append({
        "full_request": full_request,
        "request_id": request_id,
        "session_name": session_name,
        "app_route": app_route
    })
    
    return request_id

def delete_request_from_queue(request_id):
    request_index = 0
    for request in requests_queue:
        if str(request["request_id"]) == str(request_id):
            del requests_queue[request_index]
            break

# will fetch the response from the pool with id,
# return it, and delete it from pool
def get_response_from_pool(request_id):
    while True:
        response_index = 0
        for response in responses_pool:
            print(str(request_id) + " " + str(response["response_id"]))
            if str(response["response_id"]) == str(request_id):
                del responses_pool[response_index]
                delete_request_from_queue(request_id)
                return response["response"]
            response_index += 1

# Endpoint that will act as the tunnel,
# first parameter is the session id, second path is the request path.
# It will create request queue, and once response is in pool, the response will be served.
# Empty app_route handler.
@app.route("/<session_name>/")
def session_no_route(session_name):
    print("session no route")
    return app_page(session_name, "")
# Wildcard route
@app.route("/<session_name>/<path:app_route>")
def app_page(session_name, app_route):
    print(session_name)
    print(app_route)
    print(sessions_list)
    # Make sure there is an app with the given name
    print(111)
    if validate_session_exists(session_name):
        print(222)
        # Add the request to the queue
        # print(flask.request.method + " " + app_route + flask.request.environ.get("SERVER_PROTOCOL"))
        request_id = add_request_to_queueF(flask.request, session_name, app_route)
        
        print(333)
        # Wait until request is on the responses pool and return when here
        return get_response_from_pool(request_id)
    else:
        return f"<p>There are no sessions with the name of [{session_name}]</p>", 400

@app.post("/create_session")
def create_session():
    data = flask.request.get_json()
    if "email" not in data or "password" not in data:
        return flask.jsonify({"validity": False, "cause": "email and password needed"}), 400
    else:
        if validate_userF(data["email"], data["password"], True):
            session_name = uuid.uuid4()
            sessions_list.append({
                "session_name": session_name,
                "session_owner": data["email"]
            })
            return flask.jsonify({"validity": True, "session_name": session_name}), 200
        else:
            return flask.jsonify({"validity": False, "cause": "Auth Failed."}), 400

# Sends the first request from the queue that matches the session_id
# Which lets the client application to create an internal request,
# and then post it on the add_to_responses_pool api
@app.post("/get_session_request_from_queue")
def get_session_request_from_queue():
    data = flask.request.get_json()

    if "session_name" not in data or "email" not in data or "password" not in data:
        return {"validity": False, "cause": "session_name, email and password are required"}, 400
    else:
        print(data)
        if validate_session_exists(data["session_name"]):
            print("session existss daaa!")
            print(requests_queue)
            for queued_request in requests_queue:
                if str(queued_request["session_name"]) == data["session_name"]:
                    # Cant return the entire request sadly as
                    # "TypeError: Object of type LocalProxy is not JSON serializable"
                    # so just get the headers, body, requesttype from request
                    # and give those as individual properties that will be used together.
                    # to create the request object on the client app
                    return {
                            "method": queued_request["full_request"].method,
                            "headers": {key: value for key, value in queued_request["full_request"].headers if key != 'Host'},
                            "data": queued_request["full_request"].get_data(as_text=True),
                            "request_id": queued_request["request_id"],
                            "app_route": queued_request["app_route"],
                            "validity": True
                    }, 200

        else:
            return {"validity": False, "cause": "The session doesn't exist"}, 400

    return {"validity": False, "cause": "No pending requests in the queue of this session"}, 404
@app.post("/add_to_responses_pool")
def add_to_responses_pool():
    data = flask.request.get_json()
    if "request_id" not in data or "response" not in data:
        return flask.jsonify({"validity": False, "cause": "Request ID and Response Body Required"}), 400
    else:
        if "email" not in data or "password" not in data:
            return {"validity": False, "cause": "email and password needed ;)"}, 400
        else:
            # if validate user, davai, if not, niet davai cyka pidarac
            if validate_userF(data["email"], data["password"], True):
                responses_pool.append({
                    "response_id": data["request_id"],
                    "response": data["response"]
                })
                return {}, 200
            else:
                return {"validity": False, "cause": "Auth Failed."}, 400


@app.post('/login')
def login():
    # Get JSON data from the request body
    data = flask.request.get_json()
    print(data)

    if "check_if" not in data:
        data["check_if"] = False
    
    print(data)    

    if "email" not in data or "password" not in data:
        return flask.jsonify({"validity": False, "cause": "email and password needed"}), 400
    else:
        if validate_userF(data["email"], data["password"], data["check_if"]):
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
                <div class="metricitembox"><p>{request["session_name"]}</p></div>
                <div class="metricitembox"><p>{request["app_route"]}</p></div>
            </div>
        """
    
    print(responses_pool)
    for response in responses_pool:
        responsespoolmetrics += f"""
            <div class="metriclistitem">
                <div class="metricitembox"><p>{response["response_id"]}</p></div>
                <div class="metricitembox"><p>{response["response"]}</p></div>
            </div>
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
