import sys
import json
from hashlib import sha256
import requests

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



def start_http_tunnel(server_port):
    
    user_data = get_user_data()
    


    # Create the public endpoint session
    session_creation_response = requests.post(f"{server_url}create_session", json={})
    session_creation_response_json = session_creation_response.json()

    # Start the event listener loop which will track all the new requests and request them locally.
    while True:
        
        print("HTTP TUNNELLLLL")

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

