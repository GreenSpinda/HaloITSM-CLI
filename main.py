import os
import re
import ast
import sys
import csv
import time
import json
import shutil
import shlex
import datetime
import requests
import subprocess
import configparser
from configparser import ConfigParser
from requests import Response
from datetime import datetime, timedelta


class ShellInstance:
    """ init and command functions """
    # Initalization function
    def __init__(self) -> None:
        subprocess.run('title Halo CLI', shell=True)
        self.boot()

    # Function for boot control
    def boot(self) -> None:
        self.load_data()
        self.load_strings()
        os.chdir(self.INSTALL_LOCATION)
        self.load_config()
        print(f'{self.MESSAGE_WELCOME}')
        if not self.check_access():
            print(self.ERROR_NOTOKEN)

        self.main()

    # NEW - Function to load reference data.
    def load_data(self):
        # Dynamic
        self.is_connected: bool = False
        self.is_configured: bool = False
        self.custom_commands: list = ["raw", "all", "new", "refresh", "keys", "show", "basic"]
        self.config_commands: list = ["list", "open", "change", "update", "help", "dir"]
        self.config_file: str = "config.ini"    # Can be updated through update_config function to target other files. 

        # Static
        self.CONFIG_SECTIONS: list = ['configuration', 'session']
        self.CONFIG_OPTIONS: list = ['host', 'client_id', 'client_secret', 'token', 'expire']

    # Function to load all lengthy strings in one place for easy editing 
    def load_strings(self) -> None:
        self.INSTALL_LOCATION: str = os.path.dirname(__file__)
        self.VERSION: str = "v0.1.3.261110" # previous "v0.1.2.260922"
        self.COMMAND_TAG: str = "not-connected"
        #self.SHELL_TITLE: str = f'HaloCLI {self.VERSION}'
        self.CONFIG_FILENAME = 'config.ini' # Static name for default config replacement.

        self.MESSAGE_WELCOME: str = f"\nVersion: {self.VERSION}\nWelcome to the HaloITSM Command-Line Interface.\n"
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

        self.MESSAGE_CFG_NEWNAME: str = "Name for new configuration: "
        self.MESSAGE_CFG_TARGET: str = "Name of configuration> "
        self.MESSAGE_CFG_WARN: str = "This will update your configuration settings to use "
        self.MESSAGE_CFG_CONFIRM: str = "Type 'YES' to action> "

        self.CONFIG_PATH: str = self.INSTALL_LOCATION + "\\config\\"
        self.CONFIG_DEFAULT_DATA: str = """[configuration]
host = 

[session]
token = 
expire = 
"""

        self.ERROR_INVALIDFN: str = "Please try again with a valid filename." 
        self.ERROR_UNKCFG: str = "Unable to find any files with this name, you can use the 'config list' command to check available files."
        self.ERROR_MULTICFG: str = "More than one configuration with that name."
        self.ERROR_INVALIDCFG: str = "\nerror: Unable to connect to host, please check the configuration file.\n"
        self.ERROR_NOJSON: str = "\nerror: JSON content was not returned, there may be a problem with the endpoint.\n"
        self.ERROR_NOTOKEN: str = "error: No Access Token found in configuration.\n"
        self.ERROR_NOCICS: str = "\nerror: No client ID or client secret found.\n"
        self.ERROR_NOHOST: str = "\nerror: No host specified in configuration.\n"
        self.ERROR_CSVNOTFOUND: str = "\nerror: Unable to location csv file.\n"
        self.ERROR_DELPARAM: str = "\nerror: You cannot pass parameters through a DELETE. Delete example: delete /endpoint/id\n"
        self.ERROR_NORESP: str = "\nerror: POST worked although an error was returned from server. "
        self.ERROR_INVDELEP: str = "\nerror: You must specify a record ID to delete. Usage: delete /endpoint/id\n"
        self.ERROR_NOQUOTES: str = "\nerror: No closing quotation in parameter.\n"
        self.ERROR_NOPOSTDATA: str = "\nerror: You have not specified any data to POST.\n"
        self.ERROR_NOPOSTEP: str = "\nerror: You have not specified any endpoint.\n"
        self.ERROR_INVALIDEP: str = "\nerror: Could not contact the endpoint, head to https://www.usehalo.com/swagger for endpoint list."
        self.ERROR_NOEP: str = "\nerror: You did not specify a /endpoint, head to https://www.usehalo.com/swagger for endpoint list.\n"
        self.ERROR_UNAUTH: str = "error: 401 Unauthorized. Please double check you details in the config file."
        self.ERROR_UNCONNECTED: str = "\nerror: You are not connected to an instance. Please type 'help' for commands.\n"
        self.ERROR_CFGLOAD: str = "Fatal: Corrupted config file, please retype your configuration details."

        self.ERROR_USAGE: str = """\nExample usage: get /endpoint key=value key2=value2
         

The following commands are available:

Commands in this context:
basic:
?              - Displays a list of commands.
clear          - Clear the current command log.
who            - Shows the current host.          
token          - Shows current access token details.
config         - Allows in-app configuration management.
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

        self.ERROR_USAGECONFIG: str = """\nExample usage: config list
         

The following commands are available:

Commands in this context:
config list    - Lists all configuration files in the config folder.
config open    - Open the config file currently in use. 
config update  - Updates the target config file to be used.
config new     - Creates a new config file in the config directory.
config dir     - Open the directory holding the config files.\n"""

    # NEW - Function to create a configuration file within the config directory.
    def create_config_file(self, config_file_name, notify_error=False) -> None:
                path = (self.CONFIG_PATH + config_file_name)
                if notify_error:
                    print(self.ERROR_CFGLOAD)

                os.makedirs('config', exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.CONFIG_DEFAULT_DATA)
                    f.close
    
                subprocess.run(f'notepad {path}')

    # Function to create and/or Loads configuration file
    def load_config(self) -> None:
        # Creates a config file 
        self.config: ConfigParser = configparser.ConfigParser()
        
        try: 
            with open(self.config_file_path(), 'r', encoding='utf-8'):
                pass
        except FileNotFoundError:
            self.create_config_file(self.CONFIG_FILENAME, notify_error=True)
            
        self.config.read(self.config_file_path())

        try:
            self.host: str = self.config.get(self.CONFIG_SECTIONS[0], self.CONFIG_OPTIONS[0])
            self.session_token: str = self.config.get(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[3])
            self.session_expiry: datetime = datetime.strptime(self.config.get(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[4]), "%Y-%m-%d %H:%M:%S.%f")

        except ValueError:
            pass

        except configparser.NoSectionError:
            if self.is_configured: 
                self.config_file = self.CONFIG_FILENAME
                return print("Invalid configuration, fallback executed.")
            else:
             return self.create_config_file(self.CONFIG_FILENAME, notify_error=True)

        except configparser.NoOptionError:
            if self.is_configured: 
                self.config_file = self.CONFIG_FILENAME
                return print("Invalid configuration, fallback executed.")
            else:
             return self.create_config_file(self.CONFIG_FILENAME, notify_error=True)

        ## Additional check to type change session_token
        if len(self.session_token) < 1:
            self.session_token = None # type: ignore

        ## Additional catch to make clid and slsc optional
        try: 
            self.client_id: str | None = self.config.get(self.CONFIG_SECTIONS[0], self.CONFIG_OPTIONS[1])
            self.client_secret: str | None = self.config.get(self.CONFIG_SECTIONS[0], self.CONFIG_OPTIONS[2])

        except configparser.NoOptionError:
            self.client_id: str | None = None
            self.client_secret: str | None = None

        self.is_configured = True
        #

    # NEW - Parent function to route configuration commands through main.
    def manage_config(self, commands) -> None:
        try:
            command: str = commands[0]
        except IndexError:
            print(self.ERROR_USAGECONFIG)
            return
        
        match command:
            case 'help':
                print(self.ERROR_INVALIDCFG)

            case 'open':
                subprocess.run(f'notepad {self.config_file_path()}')
                self.load_config()

            case 'list':
                self.print_v2(self.find_config())

            case 'update' | 'change':
                self.update_config()

            case 'new':
                self.new_config()

            case 'dir':
                print("\n", "Opening configuration path.","\n")
                os.startfile(self.CONFIG_PATH)
                

        #self.load_config()

        # NEW - Function to change config file read. [REQUIRES CLEAN AND BUILD OUT]
    
    # NEW - Function to update the targeted configuration to use. 
    def update_config(self) -> None:
        def filter_list(file_filter):
            target_config_file = []

            for f in self.find_config():
                if file_filter in f.lower():
                    target_config_file.append(f)

            return target_config_file
        
        user_input = input("\n" + self.MESSAGE_CFG_TARGET)

        config_file = filter_list(user_input)

        if user_input in ['exit', 'quit', 'q', 'back']:
            return 
        
        elif len(config_file) > 1: 
            print(self.ERROR_MULTICFG)
            self.print_v2(config_file, "Available configurations")
            return self.update_config()
        
        elif len(config_file) < 1: 
            print(self.ERROR_UNKCFG)
            return

        print(self.MESSAGE_CFG_WARN, config_file[0], ". Confirm?")
        user_confirmation = input(self.MESSAGE_CFG_CONFIRM)
        if user_confirmation in ['yes', 'y']:
            self.disconnect()
            self.config_file = config_file[0]
            self.load_config()
            print()
            
        else: 
            print()
            return

        # Function create a new config file from create_config_file
    
    # NEW - Function to create a new configuration file in the config directory.
    def new_config(self) -> None:
        name_prompt: str = input("\n" + self.MESSAGE_CFG_NEWNAME)
        if len(name_prompt) < 1:
            return print(self.ERROR_INVALIDFN, "\n")
        print()
        self.create_config_file(f"config_{name_prompt}.ini")

    # NEW - Function to return a list of 'config' files in CONFIG_PATH
    def find_config(self) -> list:
        config_list = []

        file_list = os.listdir(self.CONFIG_PATH)

        for f in file_list:
            if 'config' in f:
                    config_list.append(f)

        return config_list

        # NEW - Simple function to return configuration target full file path. 
    
    # NEW - Function to return path of target config file.
    def config_file_path(self) -> str:
        return self.CONFIG_PATH + self.config_file
    
    # NEW - Function to print py lists of data 
    def print_v2(self, data_list: list, title: str = "List",
               headers: list[str] | None = None,
               row_ids: list[str] | None = None,
               id_header: str = "#",
               max_col_width: int = 40) -> None:

        def clip(text: str, width: int) -> str:
            return text if len(text) <= width else text[:width - 1] + "…"
    
        def fmt_row(cells: list[str]) -> str:
            return "│ " + " │ ".join(clip(c, w).ljust(w) for c, w in zip(cells, widths)) + " │"
    
        def line(left: str, mid: str, right: str) -> str:
            return left + mid.join("─" * (w + 2) for w in widths) + right
        
        if not data_list:
            print(f"\n{title}\n(no data)\n")
            return

        # Normalise every row into a list of strings
        first = data_list[0]
        if isinstance(first, dict):
            headers = headers or list(first.keys())
            rows = [[str(item.get(h, "")) for h in headers] for item in data_list]
        elif isinstance(first, (list, tuple)):
            rows = [[str(c) for c in item] for item in data_list]
        else:
            rows = [[str(item)] for item in data_list]

        # Make every row the same length
        num_cols = max(len(r) for r in rows)
        rows = [r + [""] * (num_cols - len(r)) for r in rows]

        # Headers must match the column count exactly: trim extras, pad missing
        headers = [str(h) for h in (headers or [])][:num_cols]
        if not headers and num_cols == 1:
            headers = ["File"]
        headers += [f"Col {i + 1}" for i in range(len(headers), num_cols)]

        # Only add the id column if row_ids were supplied
        if row_ids is not None:
            ids = [str(i) for i in row_ids]
            if len(ids) != len(rows):
                raise ValueError(f"row_ids has {len(ids)} items but data has {len(rows)} rows")
            headers = [id_header] + headers
            rows = [[i] + r for i, r in zip(ids, rows)]

        # Column widths: widest cell, capped by max_col_width
        widths = [
            min(max(len(headers[c]), max(len(r[c]) for r in rows)), max_col_width)
            for c in range(len(headers))
        ]

        # Shrink the widest column if the table exceeds the terminal width
        term_width = shutil.get_terminal_size((100, 20)).columns
        overhead = 3 * len(widths) + 1
        while sum(widths) + overhead > term_width and max(widths) > 8:
            widths[widths.index(max(widths))] -= 1

        total = sum(widths) + overhead
        print(f"\n{title.center(total)}")
        print(line("┌", "┬", "┐"))
        print(fmt_row(headers))
        print(line("├", "┼", "┤"))
        for r in rows:
            print(fmt_row(r))
        print(line("└", "┴", "┘"))
        print(f"{len(rows)} item(s)\n")

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
    def who_token(self, commands: list) -> None:
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

        try:
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
        except requests.exceptions.ConnectionError: 
            print(self.ERROR_INVALIDCFG)

        # New error catch v.261006
        try:
            data: dict = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            print(self.ERROR_NOJSON)
            return
        #

        if request.status_code in [x for x in range(200, 300)]:
            self.session_token: str = data['access_token']
            self.refresh_token: str = data['refresh_token']
            self.session_expiry: datetime = datetime.now()

            self.config.set(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[3], f'{self.session_token}')
            self.config.set(self.CONFIG_SECTIONS[1], self.CONFIG_OPTIONS[4], f'{self.session_expiry}')
            with open(self.config_file_path(), 'w') as f:
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
    def build_loading_bar(self, total: int):
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

    # Function to parse raw POST data to ensure compatability 
    def parse_raw_post(self, data: str):
        strip_data: str = data.strip()
        try:
            return json.loads(strip_data)
        except json.JSONDecodeError:
            pass

        try:
            return ast.literal_eval(strip_data)
        except (ValueError, SyntaxError):
            pass

        normalized = strip_data
        normalized = re.sub(r'\btrue\b', 'True', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bfalse\b', 'False', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\bnull\b', 'None', normalized, flags=re.IGNORECASE)

        try:
            return ast.literal_eval(normalized)
        except (ValueError, SyntaxError) as e:
            raise ValueError(f"Could not parse as JSON or Python literal:\n{data}") from e

    # Function to run against strings with nested json elements
    def parse_nested_json(self, value: str | dict | list):
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
        split_command: list = shlex.split(command)  # For direct json posting need to review here <-
        conditions: list = split_command[1:]
        
        
        for condition in conditions:
            if '/' in condition[0]:
                endpoint: str = condition
            elif '=' in condition:
                print(condition)
                data_pack[condition.split('=', 1)[0]] = condition.split('=', 1)[1]
                
            elif condition in self.custom_commands or condition in self.config_commands:
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

    # NEW - Function to disconnect ability to run requets. 
    def disconnect(self) -> None:
        if self.is_connected:
            print(f"Disconnected from {self.host}.")
            self.COMMAND_TAG: str = "not-connected"
            self.is_connected: bool = False
        else:
            return #print("You are not connected.")

    # Function to GET data from specified HaloAPI endpoint 
    def get_endpoint(self, endpoint: str) -> list | None:
        def GET_Request(params: dict = {}):
            # Inclusion filter parameters - 27/10/2026
            params['includedisabled'] = True
            #
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
                data: dict = json.loads(request_text)[endpoint_as_str]
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
    def post_endpoint(self, endpoint: str, user_conditions: dict, commands: list) -> None:
        def POST_Request(payload: list = []) -> Response:
            # some posts were erroring from no list for json array, added catch here 19/10/2026
            if not isinstance(payload, list):
                payload = [payload]

            request: Response = requests.post(
                                    url = f'https://{self.host}/api{endpoint}',
                                    headers = {
                                        "Authorization": f"Bearer {self.session_token}",
                                        "Content-Type": "application/json"
                                        },
                                    json = payload
                                    )
            return request

        if len(endpoint) < 1:
            print(self.ERROR_NOPOSTEP)
            return

        # Attempt raw post mode 09-11-2026
        if 'raw' in commands:
            raw_post_data = input("Enter raw JSON to post:\n")
            try:
                raw_post = self.parse_raw_post(raw_post_data)
                #raw_post: list = ast.literal_eval(raw_post_data)
                r: Response = POST_Request(raw_post)
                new_id: int = json.loads(r.text)['id']
                print("\n", endpoint.capitalize(), self.MESSAGE_SUCCESSPOST, new_id, "\n")

            except Exception as e:
                print("You have submitted invalid JSON.")
                print(e)

            print()
            return

        if len(user_conditions) < 1:
            print(self.ERROR_NOPOSTDATA)
            return
        
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

        


        
        if isinstance(user_conditions, dict):
            user_conditions_list: list = [user_conditions]

        
        #print("data_pack: ", user_conditions)
        user_conditions_list = self.parse_nested_json(user_conditions) # type: ignore
        
        request = POST_Request(user_conditions_list)

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
                           }
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
            "asset": "assets",
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
    def print_req_data(self, data, endpoint, user_conditions, commands) -> None:
        def print_basic(keys, values):
            print(f'\n --- {endpoint} Endpoint --- ')
            for key, value in zip(keys, values):
                print(f"{key}: {value}")
            print()

        def print_all():
            key_list = []
            value_list = []
           
            if isinstance(data, dict):
                for key, value in data.items():
                    key_list.append(key)
                    value_list.append(value)

                if 'basic' not in commands:
                    self.print_v2(value_list, f"{endpoint} Endpoint", ["Value"], key_list, "Key")
                else:
                    print_basic(key_list, value_list)
                    
            elif isinstance(data, list):
                data_dict = data[0]

                for key, value in data_dict.items():
                    key_list.append(key)
                    value_list.append(value)

                if 'basic' not in commands:
                    self.print_v2(value_list, f"{endpoint} Endpoint", ["Value"], key_list, "Key")
                else: 
                    print_basic(key_list, value_list)

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
            key_list = []
            for key in data[0]:
                key_list.append(key)
            self.print_v2(key_list, f"{endpoint} endpoint keys", ["Key"])

            return

        if "all" in commands or "list" in commands:
            print()
            
            id_list = []
            name_list = []
            for data_pack in data:
                try:
                    data_set = (f"{str(data_pack['id'])}", f"{data_pack['summary']}")
                except KeyError:
                    try:
                       data_set = (f"{str(data_pack['id'])}", f"{data_pack['name']}")
                    except KeyError:
                        data_set = (f"{str(data_pack['id'])}", f"{endpoint.split('/')[1]}")

                id_list.append(data_set[0])
                name_list.append(data_set[1])

            self.print_v2(name_list, f"{endpoint} endpoint", ["Records"], id_list, "ID")

            if 'print' in user_conditions:
                print("print true")

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
                    return self.parse_nested_json(data_dict) # type: ignore
                else:
                    return []
                
        except FileNotFoundError:
            print(self.ERROR_CSVNOTFOUND)
            return []
        
        else:
            return

    """ main function / loop """
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

                elif user_command.lower() in ['disconnect']:
                    user_command = str()
                    self.disconnect()

                elif user_command.lower() in ['get']:
                    user_command = str()
                    if self.is_connected is True:
                        data = self.get_endpoint(endpoint)
                        data = self.filter_data(data, user_conditions, commands) 
                        self.print_req_data(data, endpoint, user_conditions, commands)
                    else:
                        print(self.ERROR_UNCONNECTED)
                        continue

                elif user_command.lower() in ['post']:
                    user_command = str()
                    if self.is_connected is True:
                        self.post_endpoint(endpoint, user_conditions, commands)
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

                elif user_command.lower() in ['config']:
                    user_command = str()
                    self.manage_config(commands)

                elif user_command.lower() in ['test']:
                    print(endpoint)
                    print(user_conditions)
                    print(commands)

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