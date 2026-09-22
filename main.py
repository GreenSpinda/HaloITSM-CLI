## TESTING UPTO ATTACHMENT IN SWAGGER

import os
import sys
import csv
import time
import json
import shlex
import datetime
import requests
import subprocess
import configparser
from configparser import ConfigParser
from requests import Response
from datetime import datetime, timedelta

## DEV NOTES
# * Filter data not working. query /tickettype returning 140 for expected 412. 

class ShellInstance:
    """ init and command functions """
    # Initalization function
    def __init__(self) -> None:
        subprocess.run('title Halo CLI', shell=True)
        self.is_connected: bool = False
        self.custom_commands: list = ["raw", "all", "new", "refresh", "keys", "show"]
        self.boot()

    # Function for boot control
    def boot(self) -> None:
        self.load_strings()
        self.load_config()
        print(f'{self.MESSAGE_WELCOME}')
        if not self.check_access():
            print(self.ERROR_NOTOKEN)

        self.main()

    # Function to load all lengthy strings in one place for easy editing 
    def load_strings(self) -> None:
        self.INSTALL_LOCATION: str = os.path.dirname(__file__)
        self.VERSION: str = "v0.1.2.260922" # previous "v0.1.260911"
        self.COMMAND_TAG: str = "not-connected"
        self.SHELL_TITLE: str = f'HaloAPI Shell {self.VERSION}'

        self.MESSAGE_WELCOME: str = f"\nVersion: {self.VERSION}\nWelcome to the HaloITSM CLI.\n"
        self.MESSAGE_WHOHOST: str = f"\nThe current target host is:   "
        self.MESSAGE_WHOTOKEN: str = f"\nTime left on stored token:   "
        self.MESSAGE_GOTTOKEN: str = f"\nA new access token was successfully retrieved.\n"
        self.MESSAGE_EXPIREDTOKEN: str = "\nToken expired. Please refresh or request a new token.\n"
        self.MESSAGE_VALIDTOKEN: str = f"\nValid token was loaded, time left: "
        self.MESSAGE_SUCCESSPOST: str = f"record successfully created with ID:"
        self.MESSAGE_CONFIRMDEL: str = "This will PERMANENTLY delete the record(s) from the endpoint and database. Are you sure? (y/n): "
        self.MESSAGE_CANCELDEL: str = "Delete operation cancelled."
        self.MESSAGE_SUCCESSDEL: str = "\nThe following record(s) IDs have been deleted from the endpoint: "
        self.MESSAGE_NODATA: str = f"records found in the endpoint with the specified conditions.\n" # This is a error 27/08/2026
        self.MESSAGE_X: str = f""
        
        self.CONFIG_FILE: str = self.INSTALL_LOCATION + "\\" + "config.ini"
        self.CONFIG_DEFAULT_DATA: str = """[configuration]
host = 

[session]
token = 
expire = 
"""
        self.CONFIG_SECTIONS: list = ['configuration', 'session']
        self.CONFIG_OPTIONS: list = ['host', 'client_id', 'client_secret', 'token', 'expire']


        self.ERROR_NOTOKEN: str = "error: No Access Token found in configuration.\n"
        self.ERROR_NOCICS: str = "\nerror: No client ID or client secret found.\n"
        self.ERROR_NOHOST: str = "\nerror: No host specified in configuration.\n"
        self.ERROR_CSVNOTFOUND: str = "\nerror: Unable to location csv file.\n"
        self.ERROR_DELPARAM: str = "\nerror: You cannot pass parameters through a DELETE. Delete example: delete /endpoint/id\n"
        self.ERROR_NORESP: str = "\nerror: POST worked although an error was returned from server. "
        self.ERROR_INVDELEP: str = "\nerror: You must specify a record ID to delete. Usage: delete /endpoint/id\n"
        self.ERROR_NOQUOTES: str = "\nerror: No closing quotation in parameter.\n"
        self.ERROR_NOPOSTDATA: str = "\nerror: You have not specified any data to POST.\n"
        self.ERROR_INVALIDEP: str = "\nerror: Could not contact the endpoint, head to https://www.usehalo.com/swagger for endpoint list."
        self.ERROR_NOEP: str = "\nerror: You did not specify a /endpoint, head to https://www.usehalo.com/swagger for endpoint list.\n"
        self.ERROR_UNAUTH: str = "error: 401 Unauthorized. Please double check you details in the config file."
        self.ERROR_UNCONNECTED: str = "\nerror: You are not connected to an instance. Please type 'help' for commands.\n"
        self.ERROR_CONFIG: str = "Fatal: Corrupted config file, please enter details and rerun program."
        self.ERROR_USAGE:str = """\nExample usage: get /endpoint key=value key2=value2
         

The following commands are available:

Commands in this context:
basic:
?              - Displays a list of commands.
clear          - Clear the current command log.
who            - Shows the current host.          
token          - Shows current access token details.
exit           - Exit the program. 

interaction:
connect        - Connect to the HaloAPI for interaction (requires token or client id).
get            - Send a GET request to a specified /endpoint.
post           - Send a POST request to a specified /endpoint.
delete         - Send a DELETE request to a specified /endpoint.\n"""
        self.ERROR_USAGE_EXT: str = """sub-commands:
get /ep all    - Used with 'get' command to display all records in the table.
get /ep keys   - Used with 'get' command to display table keys.
get /ep raw    - Used to display the raw json content returned from server.
token refresh  - Used to force request a new token from the HaloAPI.

sub-processes: 
post csv="C:\\target_file.csv"      
               - Used to post and bulk upload to the HaloAPI\n"""

    # Function to create and/or Loads configuration file
    def load_config(self) -> None:
        # Creates a config file 
        def create_config_file():
            print(self.ERROR_CONFIG)
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(self.CONFIG_DEFAULT_DATA)
                f.close

            subprocess.run(f'notepad {self.CONFIG_FILE}')

        self.config: ConfigParser = configparser.ConfigParser()
        
        try: 
            with open(self.CONFIG_FILE, 'r', encoding='utf-8'):
                pass
        except FileNotFoundError:
            create_config_file()
            
        self.config.read(self.CONFIG_FILE)

        try:
            self.host: str = self.config.get(self.CONFIG_SECTIONS[0], self.CONFIG_OPTIONS[0])
            self.session_token: str = self.config.get(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[3])
            self.session_expiry: datetime = datetime.strptime(self.config.get(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[4]), "%Y-%m-%d %H:%M:%S.%f")

        except ValueError:
            pass

        except configparser.NoSectionError:
            create_config_file()
            exit()

        except configparser.NoOptionError:
            create_config_file()
            exit()

        ## Additional check to type change session_token
        if len(self.session_token) < 1:
            self.session_token = None # type: ignore

        ## Additional catch to make clid and slsc optional
        try: 
            self.client_id:str | None = self.config.get(self.CONFIG_SECTIONS[0], self.CONFIG_OPTIONS[1])
            self.client_secret: str | None = self.config.get(self.CONFIG_SECTIONS[0], self.CONFIG_OPTIONS[2])

        except configparser.NoOptionError:
            self.client_id: str | None = None
            self.client_secret: str | None = None

        ##

    # Function to clear terminal within program
    def clear_function(self) -> None:
        subprocess.run('cls', shell=True)

    # Function for runner to update the command tag
    def update_cmd_tag(self) -> None:
        self.COMMAND_TAG: str = self.host
    
    # Function for runner to print current targeted host to terminal
    def who_host(self) -> None:
        print(self.MESSAGE_WHOHOST + self.host + '\n')

    def check_access(self) -> bool:
        if self.session_token or self.client_id:
            return True
        else:
            return False 

    # Function for runner to print current targeted host to terminal
    def who_token(self, commands) -> None:
        if ("new" in commands or "refresh" in commands) and (self.client_id):
            self.get_token()

        ONE_HOUR: timedelta =  timedelta(hours=1)
        time_passed: timedelta = datetime.now() - self.session_expiry
        remaining_time: timedelta = ONE_HOUR - time_passed
        remaining_days: int = remaining_time.days
        if remaining_days >= 0:
            if "show" in commands: 
                print("\nAccess Token = ", self.session_token, "\n")
            else:
                print(self.MESSAGE_WHOTOKEN + (str(remaining_time).split('.')[0]) + '\n')
        else: 
            print(self.MESSAGE_EXPIREDTOKEN)

    # Function to get usable token from HaloAPI
    def get_token(self) -> None:

        if not self.host:
            print(self.ERROR_NOHOST)
            return None

        
        request: Response = requests.post(
            url = f'https://{self.host}/auth/Token',
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
                },
            data = {
                "grant_type": "client_credentials", # potietially handle other options
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "all"
                }
            )
        
        if request.status_code in [x for x in range(200, 300)]:
            self.session_token: str = json.loads(request.text)['access_token']
            self.refresh_token: str = json.loads(request.text)['refresh_token']
            self.session_expiry: datetime = datetime.now()

            self.config.set(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[3], f'{self.session_token}')
            self.config.set(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[4], f'{self.session_expiry}')
            with open(self.CONFIG_FILE, 'w') as f:
                self.config.write(f)

            self.COMMAND_TAG: str = self.host
            print(self.MESSAGE_GOTTOKEN)
            self.update_cmd_tag()
            self.is_connected = True
        
        elif request.status_code == 401:
            print(self.ERROR_UNAUTH)
        else:
            print(request.status_code)

    # Function to check the HaloAPI token expiry
    def is_token_expired(self) -> bool:
        try: 
            if self.session_token:
                self.session_expiry
            else: 
                return True
        except AttributeError:
            return True
        
        ONE_HOUR: timedelta =  timedelta(hours=1)
        time_passed: timedelta = datetime.now() - self.session_expiry
        hours_passed: float = ((time_passed.seconds / 60) / 60) + (time_passed.days * 24)
        if hours_passed >= 1:
            return True
        else:
            remaining_time: str = str(ONE_HOUR - time_passed).split('.')[0]
            print(self.MESSAGE_VALIDTOKEN + (remaining_time) + '\n') 
            return False

    # Function to create cmd like loading bar for csv command bulk uploads
    def build_loading_bar(self, total):
        current = 0
        start_time = time.monotonic()

        def update():
            nonlocal current
            current += 1

            percentage = (current / total) * 100
            filled = int(percentage // 10)

            bar = "█" * filled + "░" * (10 - filled)

            # Calculate estimated remaining time
            elapsed = time.monotonic() - start_time

            if current > 0:
                average_time_per_item = elapsed / current
                remaining_items = total - current
                remaining_seconds = average_time_per_item * remaining_items
            else:
                remaining_seconds = 0

            # Convert seconds into HH:MM:SS
            remaining_seconds = int(remaining_seconds)
            hours, remainder = divmod(remaining_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            eta = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            sys.stdout.write(
                f"\r[{bar}] {percentage:6.2f}% | ETA: {eta}"
            )
            sys.stdout.flush()

            if current >= total:
                print()

        return update

    # Function to run against strings with nested json elements
    def parse_nested_json(self, value: str | dict | list) -> str | int | float | list | dict:
                if isinstance(value, str):
                    try:
                        return self.parse_nested_json(json.loads(value))
                    except (json.JSONDecodeError, TypeError):
                        lower = value.lower()
                        if lower == "true":
                            return True
                        if lower == "false":
                            return False
    
                        try:
                            if "." in value:
                                return float(value)
                            return int(value)
                        except ValueError:
                            return value
    
                elif isinstance(value, dict):
                    return {
                        key: self.parse_nested_json(val)
                        for key, val in value.items()
                    }
    
                elif isinstance(value, list):
                    return [
                        self.parse_nested_json(item)
                        for item in value
                    ]
    
                return value

        # Function to handle user commands
    
    # Function to parse user data
    def parse_user_input(self, command: str) -> tuple[str, dict, list]:
        endpoint: str = str()
        data_pack: dict = {}
        commands: list = []
        split_command: list = shlex.split(command)
        conditions: list = split_command[1:]
        for condition in conditions:
            if '/' in condition[0]:
                endpoint: str = condition
            elif '=' in condition:
                data_pack[condition.split('=')[0]] = condition.split('=')[1]
            elif condition in self.custom_commands:
                commands.append(condition)
            
        return (endpoint, data_pack, commands)

    """ request functions """
    # Function for runner to call and manage token
    def connect(self) -> None:
        if self.is_token_expired():
            self.get_token()
        else:
            self.update_cmd_tag()
            self.is_connected = True

        return

    # Function to GET data from specified HaloAPI endpoint 
    def get_endpoint(self, endpoint: str) -> list | None:
        def GET_Request(params: dict = {}):
            request: Response = requests.get(
                        url = f'https://{self.host}/api{endpoint}',
                        headers = {
                            "Authorization": f"Bearer {self.session_token}"
                            },
                        params = params
                        )
            return request

        def unpack_data(request_text: str, endpoint_as_str: str) -> dict:
            try:             
                data = json.loads(request_text)[endpoint_as_str]
            except KeyError:
                try:
                    data= json.loads(request_text)[self.find_endpoint_key_mapping(endpoint_as_str.lower())]
            ##
                except KeyError:
                        data= json.loads(request_text)["results"]
                except IndexError:
                        data= json.loads(request_text)["tree"]

            return data
        
        data_set: list = []

        if len(endpoint) < 1: 
            print(self.ERROR_NOEP)
            return None
        
        endpoint_as_str: str = endpoint.lower().split('/')[1]

        request: Response = GET_Request()
        #print(request.text)
        #print(request.status_code)

        if request.status_code in [x for x in range(200, 300)]:
            try:
                if 'record_count' in json.loads(request.text):
                    record_count: int = json.loads(request.text)['record_count']
                    pages = 1
                    if record_count >= 50:
                        r: Response = GET_Request(
                            params={
                                "pageinate": True,
                                "page_no": 1,
                                "page_size": pages
                                }
                                )
                        record_count = json.loads(r.text)['record_count']
                        pages: int = int((record_count + 99) // 100)

                    if pages > 1:
                        for page_no in range(1, pages + 1):
                            request: Response = GET_Request(
                                params={
                                    "pageinate": True,
                                    "page_no": page_no,
                                    "page_size": 100
                                    }
                                    )

                            data: dict = unpack_data(request.text, endpoint_as_str)

                            for data_dict in data:
                                data_set.append(data_dict)

                    else:
                        data: dict = unpack_data(request.text, endpoint_as_str)
                            
                        for data_dict in data: 
                            data_set.append(data_dict)

                elif 'record_count' not in json.loads(request.text):
                    data: dict = json.loads(request.text)
                    data_set.append(data)
            
            except KeyError:
                data: dict = json.loads(request.text)

            return data_set
        
        elif request.status_code in [404]: 
            print(self.ERROR_INVALIDEP + "\n")
            return None
        
        elif request.status_code in [400, 401]:
            print("\nerror: ", f"{request.status_code}: {request.text}", "\n")
            return None

        elif request.status_code in [500]:
            print("\nerror: ", request.status_code, "\n")
            return None
        
    # Function to POST data from specified HaloAPI endpoint
    def post_endpoint(self, endpoint: str, user_conditions: dict) -> None:
        def POST_Request(payload: list = []) -> Response:
            request: Response = requests.post(
                                    url = f'https://{self.host}/api{endpoint}',
                                    headers = {
                                        "Authorization": f"Bearer {self.session_token}",
                                        "Content-Type": "application/json"
                                        },
                                    json = payload
                                    )
            return request

        
        # CSV Bulk upload post function
        if 'csv' in user_conditions.keys():
            bulk_upload_pack = self.prepare_csv(user_conditions)
            if not bulk_upload_pack:
                print("Operation cancelled.")
                return
            loading_bar = self.build_loading_bar(len(bulk_upload_pack))
            error_list = []
            for pack in bulk_upload_pack:
                pack = self.parse_nested_json(pack)
                request = POST_Request([pack])
                if request.status_code not in [x for x in range(200, 300)]:
                    error_list.append(request.text)
                loading_bar()
            print("Bulk Upload Process Had been completed.")
            print(f"Skipped records: {error_list}")
            return
        #
        
        if len(user_conditions) < 1:
            print(self.ERROR_NOPOSTDATA)
            return

        
        if isinstance(user_conditions, dict):
            user_conditions = [user_conditions]

        
        #print("data_pack: ", user_conditions)
        user_conditions = self.parse_nested_json(user_conditions)
        
        request = POST_Request(user_conditions)

        if request.status_code in [x for x in range(200, 300)]:
            try:
                new_id: int = json.loads(request.text)['id']
            except KeyError:
                print("Could not retrieve new record ID from server response. Skipping.")
                print(request.text)
            print("\n", endpoint.capitalize(), self.MESSAGE_SUCCESSPOST, new_id, "\n")

        else:
            print(self.ERROR_NORESP, f"{request.status_code}: {request.text}.\n")

    # Function to DELETE data from specified HaloAPI endpoint
    def delete_endpoint(self, endpoint: str, user_conditions: dict) -> None:

        if len(user_conditions) > 0:
            print(self.ERROR_DELPARAM)
            return
        
        # You need to add an error catch, check swagger i dont think you can pass conditions through a delete. 
        try:
            target_id: str = endpoint.split('/')[1]
            
        except IndexError:
            print(self.ERROR_INVDELEP)
            return
        
        confirmation: str = input(self.MESSAGE_CONFIRMDEL)

        if confirmation.lower() not in ['y', 'yes']:
            print(self.MESSAGE_CANCELDEL)
            return
        
        request: Response = requests.delete(
                       url = f'https://{self.host}/api{endpoint}',
                       headers = {
                           "Authorization": f"Bearer {self.session_token}"
                           },
                       #json = [user_conditions]
                       )
                

        if request.status_code in [x for x in range(200, 300)]:
            print(self.MESSAGE_SUCCESSDEL, target_id, "\n")
        else:
            print("error: ", request.status_code)
            print(request.text)

    # Function to filter data returned from HaloAPI endpoint based on parameters
    def filter_data(self, data: list | None, user_conditions: dict, commands: list) -> list | None:

        if data is None:
            return None
        
        if len(data) < 1: 
            return []
        
        if len(data) == 1 and isinstance(data[0], list): 
                data = data[0]

        #if len(user_conditions) < 1: - replaced as per review on 28/08/2026
        if not user_conditions: 
            return data

        data_key_list: list = []   
        for record in data:  
            for key in record: 
                if key not in data_key_list:    
                    data_key_list.append(key)
        


        match_cond_list: list = []
        for condition_key, condition_value in user_conditions.items():
            if condition_key in data_key_list and condition_key not in match_cond_list:
                match_cond_list.append((condition_key, condition_value))
        

        filtered_data: list = []
        for record in data:
           for key, value in (condition for condition in match_cond_list):
                if str(record[key]) == value:
                    
                    filtered_data.append(record) 
       

        return filtered_data
    
    # MAPPING HERE FOR INCORRECT TABLE NAMES
    def find_endpoint_key_mapping(self, endpoint_str) -> str:
        ENDPOINT_KEY_MAP: dict = {
            "actions": "actions",
            "site": "sites",
            "report": "reports",
            "client": "clients",
            "crmnote": "actions",
            "attachment": "attachments",
            "automation": "automations",
            "service": "services"
            }
        return ENDPOINT_KEY_MAP[endpoint_str]

    # Function to print filter data to shell
    def print_data(self, data, endpoint, user_conditions, commands) -> None:
        def print_all():
            if isinstance(data, dict):
                print(f'\n --- {endpoint} Endpoint --- ')
                for key, value in data.items():
                    print(f"{key}: {value}")
                print()

            elif isinstance(data, list):
                for data_pack in data:
                    print(f'\n --- {endpoint} Endpoint --- ')
                    for key, value in data_pack.items():
                        print(f"{key}: {value}")
                    print()

        if data is None:
            return
        
        if "raw" in commands:
            print(data)
            print(len(data))
            return 

        if len(data) < 1:
            print('\n', len(data), self.MESSAGE_NODATA)
            return

        if "keys" in commands:
            print(f'\n --- {endpoint} Endpoint Keys --- ')
            for key in data[0]:
                print(key)
            print()

            return

        if "all" in commands:
            print()
            for data_pack in data:
                try:
                    print(f"ID: {str(data_pack['id'])} -> {data_pack['summary']}")
                except KeyError:
                    try:
                        print(f"ID: {data_pack['id']} -> {data_pack['name']}")
                    except KeyError:
                        print(f"ID: {data_pack['id']} -> {endpoint.split('/')[1]}")
                print()
            return
        
        if len(user_conditions) < 1 and len(data) > 1 and len(endpoint.split('/')) < 3:          
            print(f"\nThere are {len(data)} total records in the {endpoint} endpoint.\n")
            return
        
        print_all()

    """ file functions """
    # Function to read csv files 
    def prepare_csv(self, file_string: dict) -> list:
        
        try:
            target_location = file_string['csv']
            with open(target_location, 'r', newline='', encoding='utf-8-sig') as csv_data:
                data_dict: list = list(csv.DictReader(csv_data))
                print(f"This process will attempt to upload {len(data_dict)} records to the Halo Instance.")
                user_input = input("TYPE 'COMMIT'> ")
                if user_input.lower() in ['commit']:
                    return self.parse_nested_json(data_dict)
                else:
                    return []

        except FileNotFoundError:
            print(self.ERROR_CSVNOTFOUND)
            return []
        
        else:
            return

    """ main function """
    def main(self): 
        while True: 
            user_input = input(f'{self.COMMAND_TAG}> ')
            try:
                user_command = shlex.split(user_input)[0]
                endpoint, user_conditions, commands = self.parse_user_input(user_input)
            except IndexError:
                pass

            except ValueError as e:
                print(self.ERROR_NOQUOTES)
                continue

            try:
                if user_command.lower() in ['exit', 'quit']:
                    break

                elif user_command.lower() in ['cls', 'clear']:
                    user_command = str() 
                    self.clear_function()

                elif user_command.lower() in ['who', 'host']:
                    user_command = str()
                    self.who_host()

                elif user_command.lower() in ['token']:
                    user_command = str()
                    self.who_token(commands)

                elif user_command.lower() in ['connect']:
                    user_command = str()
                    self.connect()

                elif user_command.lower() in ['get']:
                    user_command = str()
                    if self.is_connected is True:
                        data = self.get_endpoint(endpoint)
                        data = self.filter_data(data, user_conditions, commands) 
                        self.print_data(data, endpoint, user_conditions, commands)
                    else:
                        print(self.ERROR_UNCONNECTED)
                        continue

                elif user_command.lower() in ['post']:
                    user_command = str()
                    if self.is_connected is True:
                        self.post_endpoint(endpoint, user_conditions)
                    else:
                        print(self.ERROR_UNCONNECTED)
                        continue

                elif user_command.lower() in ['delete']:
                    user_command = str()
                    if self.is_connected is True:
                        self.delete_endpoint(endpoint, user_conditions)
                    else:
                        print(self.ERROR_UNCONNECTED)
                        continue

                elif user_command.lower() in ['help']:
                    user_command = str()
                    if 'all' in commands:
                        print(self.ERROR_USAGE)
                        print(self.ERROR_USAGE_EXT)
                    else:
                        print(self.ERROR_USAGE)

                elif user_command.lower() in ['test']:
                    print(self.session_token)
                    print(type(self.session_token))
                    print(self.client_id)
                    print(type(self.client_id))

                elif user_command == str():
                    pass

                else:
                    user_command = str()
                    print(self.ERROR_USAGE)
                    pass


            except UnboundLocalError:
                continue
                
if __name__ in "__main__":
    shell = ShellInstance()
