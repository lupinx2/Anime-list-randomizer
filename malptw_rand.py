# Returns a random anime from your MAL Plan-to-Watch list
# Using either the API or a local xml file.
#
# TODO
# Update readme with pictures
#
# Test with: Debian / fresh python install / no internet.
#
# PySimpleGUI:
#   Add xml selection.
#   Add randomize button function.
#   Add radial button functionality
#   Improve output formatting, aspect.
#       Add cover art.
#       Add link to MAL page/streaming.
#
# Make it so that APIgetAnimeList is only called if the -username- changes.
#
# Use the API from the GUI.
#   Add save button functionality.
# 
# rename variables to be less confusing.
#
# Remove console output
#   make all the print calls conditional to a DEBUG bool?

from argparse import ArgumentParser
from msilib.schema import CheckBox
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
    no_movies = False
    only_movies = False
    prevUsername = ""

# ------------------------------------------------------------------------------
# API Functions
# ------------------------------------------------------------------------------
    # Pull user's animelist by calling the MAL API, save the response to a dictionary.
    def APIgetAnimeList(user_name):
        global prevUsername
        if user_name == prevUsername:  # prevents unnecessary API calls
            return
        try:
            url = 'https://api.myanimelist.net/v2/users/' + str(user_name) +\
                '/animelist?fields=list_status,media_type&status=plan_to_watch&limit=1000'  # 1000 is the max allowed by MAL.
            headers = {'X-MAL-CLIENT-ID': config.API_key}
            sleep(0.5)  # Sleep to prevent rate limiting.
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception("API call error")
            responseBytes = (response.content)
            responseString = responseBytes.decode("utf-8")
        except:
            print("API Call Error; Status code: " +
                  str(response.status_code) + "\n")
        outputDict = json.loads(responseString)

        # This block poulates the list objects from the API response.
        def gen_dict_extract(var, key):
            if isinstance(var, dict):
                for dictKey, dictValue in var.items():  # for every (key:value) pair in var...
                    if dictKey == key:  # where the key matches the parameter...
                        yield dictValue  # yield the value...
                    # if you run into a list, recursively call this function.
                    if isinstance(dictValue, list):
                        for listItem in dictValue:
                            for result in gen_dict_extract(listItem, key):
                                yield result
        for item in gen_dict_extract(outputDict, 'node'):
            ptw_list.append(item['title'] + " [" + item['media_type'] + "]")
            ptw_list_id.append(item['id'])
            if (no_movies == True and item['media_type'] == "movie"):
                ptw_list.pop()
                ptw_list_id.pop()
            if (only_movies == True and not item['media_type'] == "movie"):
                ptw_list.pop()
                ptw_list_id.pop()
        prevUsername = user_name

    # Returns a tuple of the anime title and a link to the anime's page on MAL.
    def GetRandomAnime():
        rand_index = random.randint(0, len(ptw_list)-1)
        return "{}".format(ptw_list[rand_index]), ('https://myanimelist.net/anime/' +
                                                   str(ptw_list_id[rand_index]))
# ------------------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------------------
    # This is spaghetti code, clean it up later.
    Gooey.theme('LightGray')
    # The main tab.
    tab1_layout = [[Gooey.Text('Allof which makes me anxious:')],
                   [Gooey.Text('MAL username:'),
                    Gooey.InputText(key='-username-')],
                   [Gooey.Radio("Exclude Movies", 666, False, False, key='-no_Movies-'),  # Radio buttons
                    Gooey.Radio("Only Movies", 666, False, False, key='-only_Movies-'),
                    Gooey.Radio("Any anime", 666, True, False, key='-any_Anime-')],  # <-default selection
                   [Gooey.Text("this is the output object", size=(40, 2), key='-OUTPUT-')]]
    # The settings tab.
    tab2_layout = [[Gooey.T('Your API Key:')],
                   [Gooey.In(key='apiKeyInput', password_char='●'), Gooey.Button('Save', key='-SAVE-')],
                   [Gooey.Checkbox('Use local XML file', key='-useXML-')]]
    # The main layout.
    layout = [
        [Gooey.TabGroup([
            [Gooey.Tab('Main', tab1_layout),
             Gooey.Tab('Settings', tab2_layout)]
        ])],
        [Gooey.Button('Randomize!'), Gooey.Button(
            'Exit')]  # The buttons at the bottom
    ]
    window = Gooey.Window('MAL Randomizer', layout)  # Create the window.

    # Loop listening for GUI events.
    while True:
        event, values = window.read()
        if event in (666, '-no_Movies-'):
            no_movies = True
            only_movies = False
        if event in (666, '-only_Movies-'):
            no_movies = False
            only_movies = True
        if event in (666, '-any_Anime-'):
            no_movies = False
            only_movies = False
        if event in (Gooey.WIN_CLOSED, 'Exit'):
            exit()
        if event == 'Randomize!':
            if values['-useXML-'] == True:
                # do nothing
                break
            else:  # use API.
                APIgetAnimeList(values['-username-'])
                Rnd_title, Rnd_link = GetRandomAnime() 
                window['-OUTPUT-'].update(Rnd_title)
    window.close()
# ------------------------------------------------------------------------------
# XML Functions
# ------------------------------------------------------------------------------

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

    # This block populates the list objects from the local xml file.
    # from each <anime> in the xml...
    for anime in tree_root.findall("anime"):
        # where my_status == PTW...
        if anime.find("my_status").text == "Plan to Watch":
            ptw_list.append(anime.find("series_title").text +  # append the series_title to ptw_list...
                            " [" + anime.find("series_type").text + "]")  # also include its series_type...
            # then, append its series_animedb_id to ptw_list_id.
            ptw_list_id.append(anime.find("series_animedb_id").text)
            if (anime.find("series_type").text == "Movie") and (no_movies == "y"):
                ptw_list.pop()
                ptw_list_id.pop()
            if (anime.find("series_type").text != "Movie") and (only_movies == "y"):
                ptw_list.pop()
                ptw_list_id.pop()
