# Returns a random anime from your MAL Plan-to-Watch list
# Using either the API or a local xml file.
#
# TODO
# Update readme with pictures
#
# Test with: Debian / fresh python install / no internet.
# 
# PySimpleGUI:
#   Before anything else, draw a mockup of the final design.
#       Add xml / api selection.
#       Add radial button functionality
#       Improve output formatting, aspect.
#
# Remove console output
#   make all the print calls conditional to a DEBUG bool?

from argparse import ArgumentParser
import xml.etree.ElementTree as ET
import PySimpleGUI as Gooey
from time import sleep
from cmd import PROMPT
import requests
import config
import random
import glob
import json


if __name__ == '__main__':

    ptw_list = list()
    ptw_list_id = list()
    opts = ["y", "n"]

    Gooey.theme('LightGray')
    layout = [  [Gooey.Text('Set parameters:')],
            #[Gooey.Text('Enter username:'), Gooey.InputText()],
            #The group of radio buttons at the top
            [Gooey.Radio("Exclude Movies", 666, False, False),
             Gooey.Radio("Only Movies", 666, False, False),
             Gooey.Radio("Any anime", 666, True, False)],     
            #the two buttons in the middle
            [Gooey.Button('Randomize'), Gooey.Button('Exit')],
            #the output at the end
            [Gooey.Text("",size=(25, 2) ,key='-OUTPUT-')]]            
    window = Gooey.Window('MALptw-rand', layout)

    # Event Loop
    while True:
        event, values = window.read()
        if event in (Gooey.WIN_CLOSED, 'Exit'):
            break
        if event == 'Randomize':
            window['-OUTPUT-'].update("This is the output! Lorem ipsum dolor sit amet, consectetur000025")
    window.close()

    # Prompt user for xml or api.
    while True:
        method = input("Use local .xml file? [Y/N]: ").lower().rstrip()
        if method not in opts:
            print("Invalid input!")
            continue
        else:
            if method == "y":
                method = "xml"
                break
            elif method == "n":
                method = "api"
                break
            continue

    # Function to prompt user to exclude movies or series/OVA.
    def promptForSettings():
        global no_movies
        global only_movies
        while True:
            no_movies = input("Exclude movies? [Y/N]: ").lower().rstrip()
            if no_movies not in opts:
                print("Invalid input!\n")
                continue
            else:
                if no_movies == "n":
                    only_movies = input(
                        "Only movies? [Y/N]: ").lower().rstrip()
                    if only_movies not in opts:
                        print("Invalid input!\n")
                        continue
                    else:
                        break
                else:  # if no_movies = Y
                    only_movies = "n"
                    break

    if method == "xml":

        # Prompt user to pick an .xml file from the working directory.
        ListOfXML = (glob.glob('*.xml'))
        while True:
            print('Select an xml file:')
            i = int(0)
            for each in ListOfXML:
                print(i, ':', ListOfXML[i])
                i = (i+1)
            choice = input()
            try:
                choice = int(choice)
                break
            except ValueError:
                print("Invalid input!\n")
        selectedMALfile = ListOfXML[choice]
        print(selectedMALfile, ' selected.\n')
        list_tree = ET.parse(selectedMALfile)
        tree_root = list_tree.getroot()

        promptForSettings()

        # This block populates the list objects from the local xml file.
        for anime in tree_root.findall("anime"): # from each <anime> in the xml...
            if anime.find("my_status").text == "Plan to Watch":  # where my_status == PTW...
                ptw_list.append(anime.find("series_title").text + # append the series_title to ptw_list...
                                " [" + anime.find("series_type").text + "]")  # also include its series_type...
                ptw_list_id.append(anime.find("series_animedb_id").text) # then, append its series_animedb_id to ptw_list_id.
                if (anime.find("series_type").text == "Movie") and (no_movies == "y"):
                    ptw_list.pop()
                    ptw_list_id.pop()
                if (anime.find("series_type").text != "Movie") and (only_movies == "y"):
                    ptw_list.pop()
                    ptw_list_id.pop()

    elif method == "api":

        # Pull user's animelist by calling the MAL API, save the response to a dictionary.
        while True:
            try:
                print("Please enter MAL username:")
                user_name = input()
                url = 'https://api.myanimelist.net/v2/users/' + str(user_name) +\
                    '/animelist?fields=list_status,media_type&status=plan_to_watch&limit=1000'  # 1000 is the max allowed by MAL.
                headers = {'X-MAL-CLIENT-ID': config.API_key}
                sleep(0.5)  # Sleep to prevent rate limiting.
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    raise Exception("API call error")
                responseBytes = (response.content)
                responseString = responseBytes.decode("utf-8")
                break
            except:
                print("API call error, please verify username or internet connection.")
                print("Status code: " + str(response.status_code) + "\n")
        outputDict = json.loads(responseString)

        promptForSettings()

        # This block poulates the list objects from the API response.
        def gen_dict_extract(var, key):
            if isinstance(var, dict):
                for dictKey, dictValue in var.items():  # for every (key:value) pair in var...
                    if dictKey == key:  # where the key matches the parameter...
                        yield dictValue  # yield the value...
                    if isinstance(dictValue, list): # if you run into a list, recursively call this function.
                        for listItem in dictValue:
                            for result in gen_dict_extract(listItem, key):
                                yield result
        for item in gen_dict_extract(outputDict, 'node'):
            ptw_list.append(item['title'] + " [" + item ['media_type'] + "]")
            ptw_list_id.append(item['id'])
            if (no_movies == "y" and item['media_type'] == "movie"):
                ptw_list.pop()
                ptw_list_id.pop()
            if (only_movies == "y" and not item['media_type'] == "movie"):
                ptw_list.pop()
                ptw_list_id.pop()

    else:
        print("Input error, exiting...")
        exit()

    # Prompt user to pick a random anime from ptw_list.
    while True:
        user_in = input("Get random anime? [Y/N]: ").lower().rstrip()
        if user_in not in opts:
            print("Invalid input!\n")
            continue
        elif user_in == "n":
            print("goodbye!")
            break
        rand_index = random.randint(0, len(ptw_list)-1)
        print("Your random anime is: {}".format(ptw_list[rand_index]))
        print('https://myanimelist.net/anime/' +
              str(ptw_list_id[rand_index]) + "/\n")
