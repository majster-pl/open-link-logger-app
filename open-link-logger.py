#!/usr/bin/env python3
from ast import While
from optparse import OptionParser
from asyncio.log import logger
import subprocess
import json
import logging
import configparser
import os
import requests
import sys
import time
import os.path
from shutil import copyfile
from pathlib import Path

# parser = argparse.ArgumentParser(
parser = OptionParser(
    description='Open Link Logger, this script will test your internet connection and save data locally for it to be nicely presented in browser.')

parser.add_option("-s", "--stop", action="store_true", dest="stop_server", default=False,
                  help="Stops services running in the background")

parser.add_option("-f", "--fresh", action="store_true", dest="fresh", default=False,
                  help="Start setup wizard")

(options, args) = parser.parse_args()

# Kill web server and API server when -s or --stop option used.
if (options.stop_server):
    print("Sotpping services...")
    os.system("kill -9 $(cat server-api.pid)")
    os.system("kill -9 $(cat server-web.pid)")
    sys.exit()


# Application confing
config = configparser.ConfigParser()
files = ['open-link.conf']
dataset = config.read(files)
# check if config file exist
if len(dataset) != len(files):
    logging.info(f"Config file don't exist, creating one...")
    config["Default"] = {
        'first-run': 'true',
        'data-path': '',
        'test-reiteration': 3,
        'port': 3900
    }
    # save config file
    with open("open-link.conf", "w") as file_object:
        config.write(file_object)
        logging.info("Config file 'open-link.conf' created")

# open and read config file
config.read('open-link.conf')
data_json_path = config['Default']['data-path']
first_run = config['Default']['first-run']
test_reiteration = config['Default']['test-reiteration']
port = config['Default']['port']
port_api = 4981
test_count = 0

# define termianl colors


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Application logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info('Starting Open-Link-Logger...')

# function to check if scrip running for first time, if so run setup guide


def check_if_first_run():
    if first_run == "true" or options.fresh == True:
        print(f'{bcolors.OKGREEN}\
####################################################################################### \n\
#                                                                                    ##\n\
#    ▌ ▌   ▜               ▐       ▞▀▖            ▌  ▗    ▌     ▌                    ##\n\
#    ▌▖▌▞▀▖▐ ▞▀▖▞▀▖▛▚▀▖▞▀▖ ▜▀ ▞▀▖  ▌ ▌▛▀▖▞▀▖▛▀▖▄▄▖▌  ▄ ▛▀▖▌▗▘▄▄▖▌  ▞▀▖▞▀▌▞▀▌▞▀▖▙▀▖   ##\n\
#    ▙▚▌▛▀ ▐ ▌ ▖▌ ▌▌▐ ▌▛▀  ▐ ▖▌ ▌  ▌ ▌▙▄▘▛▀ ▌ ▌   ▌  ▐ ▌ ▌▛▚    ▌  ▌ ▌▚▄▌▚▄▌▛▀ ▌     ##\n\
#    ▘ ▘▝▀▘ ▘▝▀ ▝▀ ▘▝ ▘▝▀▘  ▀ ▝▀   ▝▀ ▌  ▝▀▘▘ ▘   ▀▀▘▀▘▘ ▘▘ ▘   ▀▀▘▝▀ ▗▄▘▗▄▘▝▀▘▘     ##\n\
#                                                                                    ##\n\
#######################################################################################{bcolors.ENDC}\n\n\
{bcolors.OKBLUE}Using this script you can check you internet connection speed as often as you want\n\
and every test will be sotored localy. Results can then be viewed in your browser.{bcolors.ENDC}\n\n\
{bcolors.WARNING}This is Open Source software released under MIT licence and is provided "AS IS" without\n\
any warranty on any kind!\n\n\
{bcolors.OKCYAN}Author{bcolors.ENDC}:       Szymon Waliczek\n\
{bcolors.OKCYAN}Contact{bcolors.ENDC}:      waliczek.szymon@gmail.com\n\
{bcolors.OKCYAN}Instructions{bcolors.ENDC}: https://github.com/majster-pl/open-link-logger/blob/main/README.md\n\
{bcolors.OKCYAN}Source Code{bcolors.ENDC}:  https://github.com/majster-pl/open-link-logger\n\
')
        q_procceed = input("Do you want to continue ? (y/N)")
        if q_procceed not in ['y', 'Y', 'Yes', 'yes']:
            print("See you again soon! :)")
            sys.exit()

        print(f'In next few steps you will set up few important parameters\n')

        # setting up web server port
        while True:
            try:
                q_port = int(input(
                    f"[1/4] What port do you want a web server to run on?\n{bcolors.HEADER}[3900]: {bcolors.ENDC}") or 3900)
                break
            except ValueError:
                print(
                    f"{bcolors.FAIL}Please enter valid port number...{bcolors.ENDC}")

        if q_port:
            print(f'Port set to: {bcolors.OKGREEN}{q_port}{bcolors.ENDC}')
        else:
            q_port = 3900
            print(f'Port set to: {bcolors.OKGREEN}{q_port}{bcolors.ENDC}')
        config['Default']['port'] = str(q_port)

        # path to db.json file
        Default_path = os.getcwd() + "/data/db.json"
        q_data_path = input(
            f"\n[2/4] Specify the path where you want data to be collected:\n\
{bcolors.HEADER}[{Default_path}]{bcolors.ENDC}: ")
        if q_data_path:
            print(
                f'Path set to: {bcolors.OKGREEN}{q_data_path}{bcolors.ENDC}')
        else:
            q_data_path = Default_path
            print(
                f'Path set to: {bcolors.OKGREEN}{q_data_path}{bcolors.ENDC}')
        config['Default']['data-path'] = str(q_data_path)

        # Number of test reiterations
        default_reiteration = 3
        while True:
            try:
                q_reiteration = int(input(
                    f"\n[3/4] How many times you want test to retry connect to server before exiting the app (if added to crontab, sometimes too many tests running at the same time from differet locations and blocking servers from respodning)\n{bcolors.HEADER}[{default_reiteration}] {bcolors.ENDC}: ") or 3)
                break
            except ValueError:
                print(f"{bcolors.FAIL}Please enter integer only...{bcolors.ENDC}")
        if not q_reiteration:
            q_reiteration = default_reiteration
        print(
            f'Sppedtest retry set to: {bcolors.OKGREEN} {q_reiteration} {bcolors.ENDC}')
        config['Default']['test-reiteration'] = str(q_reiteration)

        # Add job to crontab
        entires = {
            1: ' * 12 * * * ',
            2: ' * 00 * * * ',
            3: ' * 12,00 * * * ',
            4: ' 00 * * * * ',
            5: ' 30 * * * * ',
            6: ' */30 * * * * ',
        }
        entires_text = {
            1: 'Once a day @ 12:00',
            2: 'Once a day @ 00:00',
            3: 'Twice a day @ 12:00 and 00:00',
            4: 'Every hour @ 00 hours',
            5: 'Every hour @ 30 minutes past',
            6: 'Every 30 minutes',
            7: 'Do not add to crontab (I\'ll run this script manually whenever I want)'
        }

        while True:
            try:
                q_crontab = int(input(
                    f"\n[4/4] Now you can add speedtest to crontab to be lunched automaticaly.\n\
Choose one options from below and it will be added to crontab for you.\n\
    1 => {entires_text[1]}\n\
    2 => {entires_text[2]}\n\
    3 => {entires_text[3]}\n\
    4 => {entires_text[4]}\n\
    5 => {entires_text[5]}\n\
    6 => {entires_text[6]}\n{bcolors.HEADER}\
    7 => {entires_text[7]}{bcolors.ENDC}\n\
{bcolors.HEADER}[7]{bcolors.ENDC}: ") or 7)
                if q_crontab in range(1, 8):
                    break
                else:
                    print(f"{bcolors.FAIL}Invalid selection!{bcolors.ENDC}")
            except ValueError:
                print(f"{bcolors.FAIL}Please enter integer only...{bcolors.ENDC}")

        # check if other then default selected
        if q_crontab == 7:
            print(f'{bcolors.OKBLUE}Nothing added to crontab.{bcolors.ENDC}')
        else:
            if not q_crontab == 7:
                command = f'crontab -l | {{ cat; echo "{entires[q_crontab]} cd {os.getcwd()} && /usr/bin/python3 open-link-logger.py >> crontab_jobs.log 2>&1"; }} | crontab -'
                print(
                    f'Test will run automatically: {bcolors.OKGREEN} {entires_text[q_crontab]} {bcolors.ENDC}')

        # Ask user if happy to save data.
        while True:
            q_save = input(
                f"\nDo you want to save all settings?\n{bcolors.HEADER}[Y/n]{bcolors.ENDC}: ") or "Y"
            if q_save not in ['y', 'Y', 'Yes', 'yes']:
                print("Restarting...")
                check_if_first_run()
                break
            else:
                if not q_crontab == 7:
                    os.system(command)
                    print(
                        f'\n{bcolors.WARNING}New entry added to crontab, to edit run "crontab -e" in terminal{bcolors.ENDC}')

                config['Default']['first-run'] = 'false'
                with open('open-link.conf', 'w') as configfile:
                    config.write(configfile)
                print(
                    f'{bcolors.OKGREEN}\nYou are all set and ready to go!\n\
To get your first test run ./open-link-logger.py again ;) - Enjoy!{bcolors.ENDC}')
                sys.exit()

# Function to check if local server running if not start it


def start_local_webserver():
    # try to connect to local server if running don't start another server
    try:
        get = requests.get(f'http://localhost:{port}')
        if get.status_code == 200:
            logging.info(f"Server already running on: http://localhost:{port}")
            return
        else:
            logging.warning(
                f"Posible problem with server on: http://localhost:{port}")
            logging.warning(f"Error code: {get.status_code}")
            return
    except:
        logging.info(f"Starting local server on port: {port}")
        # print(f"Starting local server...")
        process = subprocess.Popen(
            ["node", "./server/server.js", "-p", port, "-d", data_json_path], stdout=None, stderr=None)
        # Write PID file
        pidfilename = os.path.join(os.getcwd(), 'server-web.pid')
        pidfile = open(pidfilename, 'w')
        pidfile.write(str(process.pid))
        pidfile.close()
        return

# Function to check if API server is running, if not start it


def start_local_api_server():
    # try to connect to local server if running don't start another server
    try:
        get = requests.get(f'http://localhost:{port_api}')
        if get.status_code == 200:
            logging.info(
                f"API Server already running on: http://localhost:{port_api}")
            return
        else:
            logging.warning(
                f"Posible problem with API server on: http://localhost:{port_api}")
            logging.warning(f"Error code: {get.status_code}")
            return
    except:
        logging.info(f"Starting local API server on port: {port_api}")
        # check if db.json file exist if not copy from template
        if not os.path.exists(data_json_path):
            data = {"speedtest": []}
            Path(os.path.join(os.getcwd(), 'data')
                 ).mkdir(parents=True, exist_ok=True)
            with open('./data/db.json', 'w') as f:
                json.dump(data, f)
            logging.info('New db.json created.')
        _path = os.path.join(os.getcwd(), "node_modules",
                             ".bin", "json-server")
        api_process = subprocess.Popen(
            ["node", _path, "-H", "0.0.0.0", "--watch", "./data/db.json", f"-p={str(port_api)}", "-q"], stdout=None, stderr=None)
        # Write PID file
        pidfilename = os.path.join(os.getcwd(), 'server-api.pid')
        pidfile = open(pidfilename, 'w')
        pidfile.write(str(api_process.pid))
        pidfile.close()
        return

# function to append results in db.json file


def save_results(new_data, filename=data_json_path):
    # check if db.json file exist if not copy from template
    if not os.path.exists(data_json_path):
        data = {"speedtest": []}
        Path(os.path.join(os.getcwd(), 'data')
             ).mkdir(parents=True, exist_ok=True)
        with open('./data/db.json', 'w') as f:
            json.dump(data, f)
        logging.info('New db.json created.')

    with open(filename, 'r+') as file:
        file_data = json.load(file)
        try:
            file_data['speedtest'][-1]["id"]
            new_data['id'] = int(file_data['speedtest'][-1]["id"]) + 1
        except:
            new_data['id'] = 1
        file_data["speedtest"].append(new_data)
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent=4)
        logging.info(f"Results added to {filename}")

# run speedtest with parameters from config file


def run_speedtest_cli():
    global test_count
    test_count += 1
    logging.info(f'Speedtest attempt no: {test_count}/{test_reiteration}')
    proc = subprocess.Popen(
        ['speedtest', '-f', 'json-pretty'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    pros_status = proc.wait()

    if pros_status == 0:
        logging.info('Test completed successfully')
        return json.loads(stdout)
        # return False
    else:
        logging.critical('Speedtest failed, check error message below')
        logging.info(stderr[2:])
        return False


check_if_first_run()
start_local_webserver()
start_local_api_server()
result = run_speedtest_cli()

# if unable to run test, retry number of times from config.
while not result:
    if test_count < int(test_reiteration):
        logging.error('Test failed')
        logging.info('Attempting to run test again in 5 seconds...')
        time.sleep(5)
        result = run_speedtest_cli()
    else:
        logging.error('Test failed')
        logging.info('Exiting aplication.')
        break

if result:
    save_results(result)

print(f"########## END ##########")
