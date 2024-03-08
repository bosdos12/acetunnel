import sys
import json
from hashlib import sha256
import requests
import time


server_url = "http://127.0.0.1:5000/"

def please_login_syntax():
    print("Please login with \n login [email] [password]")

def login(email, password, check_if=False):
    response = requests.post(f"{server_url}login", json={
                                                        "email": email, 
                                                        "password": password,
                                                        "check_if": check_if
                                                        })
    
    response_json = response.json()
    print(response_json)
    
    if response_json["validity"]:
        return True
    else:
        print("Login failed")
        print("cause: " + response_json["cause"])
        return False
   
def check_if_logged_in():
    try:
        print("aaa")
        with open("user_data.json", "r") as _raw_userdata:
            print("bbb")
            user_data = json.load(_raw_userdata)
            return login(user_data["email"], user_data["password"], True)
    except:
        print("ccc")
        please_login_syntax()
        return False

def get_user_data():
    try:
        with open("user_data.json", "r") as _raw_userdata:
            user_data = json.load(_raw_userdata)
            return [user_data["email"], user_data["password"]]
    except:
        return False



def add_response_to_pool(email, password, request_id, response):
    print("\n\n\nadd to respones pool")
    print(email)        
    print(password)
    print(request_id)
    print(response)


    add_to_response_res = requests.post(f"{server_url}add_to_responses_pool", json={
                                        "request_id": request_id,
                                        "response_headers": dict(response.headers),
                                        "response_status_code": response.status_code,
                                        "response_text": response.text,
                                        "email": email,
                                        "password": password
                                                                })
    
    add_to_response_res_json = add_to_response_res.json()

    print(add_to_response_res_json)

    
    
def start_http_tunnel(server_port):
    
    user_data = get_user_data()
    


    # Create the public endpoint session
    session_creation_response = requests.post(f"{server_url}create_session", json={
                                                                                "email": user_data[0],
                                                                                "password": user_data[1]
                                                                                })
    session_creation_response_json = session_creation_response.json()
    print(f"Local Server  | http://localhost:{server_port}/\nPublic Tunnel | {server_url}{session_creation_response_json['session_name']}")
    if session_creation_response_json["validity"]:
        # Start the event listener loop which will track all the new requests and request them locally.
        while True:
            queued_request = requests.post(f"{server_url}get_session_request_from_queue", json={
                                                                                                "session_name": session_creation_response_json["session_name"],
                                                                                                "email": user_data[0],
                                                                                                "password": user_data[1]
                                                                                            }) 
            queued_request_json = queued_request.json()
            if queued_request_json["validity"]:
                
                # NOTE - Deal with this shit right here when you wake up
                # project almost done u got this
                print(queued_request_json)  
                
                app_route = "/" if queued_request_json["app_route"] == "" else queued_request_json["app_route"]                

                # note implemet full proxy features in the future.
                # for now just test if the GET request functionality works
                # NOTE - headers & data implemented later
                local_request_response = requests.get(f"http://127.0.0.1:{server_port}/{app_route}")
                print(local_request_response)

                add_response_to_pool(
                                    user_data[0],
                                    user_data[1],
                                    str(queued_request_json["request_id"]),
                                    local_request_response)              


                # print(f"{queued_request_json['method']} /{queued_request_json['app_route']}")
            time.sleep(0.1)
    else:
        print(session_creation_response_json["cause"])

def print_available_commands():
    print("Available commands:\n login [email] [password]\n acetunnel http [port] [options] -auth? [pass]?\n acetunnel server [port] -auth? [pass]?")

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) <= 1:
        print_available_commands()
    elif sys.argv[1] == "login":
        if len(sys.argv) == 4:
            email    = sys.argv[2]
            password = sys.argv[3]

            if login(email, password):
                with open("user_data.json", "w") as _write_userdata:
                    _write_userdata.write(json.dumps({
                                                    "email": email,
                                                    "password": sha256(password.encode("utf-8")).hexdigest() 
                                                    }))
                print("Logged in successfully.")
        else:
            print("Invalid commands or syntax")
            please_login_syntax()
    elif sys.argv[1] == "acetunnel" and len(sys.argv) <= 2:
        if check_if_logged_in():
            print("Available options:\nhttp   | usage: http [port] [options] -auth? [pass]? \nserver | usage: server [port] -auth? [pass]?")
    elif sys.argv[1] == "acetunnel" and len(sys.argv) > 3:
        if check_if_logged_in():
            server_port = sys.argv[3]

            if sys.argv[2] == "http":
                start_http_tunnel(server_port)
            
            elif sys.argv[2] == "server":
                # do it later. not critical for mvp
                print("server")
    else:
        print("Invalid commands or syntax")
        print_available_commands()

