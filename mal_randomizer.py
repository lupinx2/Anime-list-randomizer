# Displays a random anime from your MAL Plan-to-Watch list
# Using either the API or a local xml file.
#
# TODO
#
# update requirements in readme.
# >notes from linux run:
#  # pip isntall pysimplegui + apt install python3-tk
# 
# *split functions into multiple files?[]
# *Force cover art image size to avoid window resizing. []
# *use global variables to reduce number of arguments? []
# *add API call counter.[]
# *remove SaveOutput function, replaced by global tuple. []
#
# *Webscrape mode??? []
#
# Possible Back button bheaviors:
#   Stores each result and simply navigates backwards. <---- list? stack?
#   Always shows the prev result, causing a loop if the button is pressed twice. <---- implement by commeting out the line that disables 'back' button.
#   Goes back once then disables the button until the next result is shown. <---- currently implemented.
#
#
# API method:
#  1 per-username API call to get the list
#  1 per-anime API call to get picture
#  1 per-anime API call to get the anime info
#  total 1 seconds sleep per anime
#
# XML method:
#  0 API calls to get the list
#  2 per-anime API calls to get picture
#  1 per-anime API call to get the anime info
#  total 1.4 seconds sleep per anime

from json import loads as jsonLoads
import xml.etree.ElementTree as ET
import PySimpleGUI as Gooey 
from os import getcwd, path
from random import randint
from time import sleep
from PIL import Image
import webbrowser
import requests
import sys
import io

if __name__ == '__main__':

    list_titles = list()
    list_id = list()
    list_coverImg = list()
    no_movies = False
    only_movies = False
    rnd_Title, rnd_id, rnd_CoverURL = '', '', ''
    prevAPIcall = ""
    prevXMLfile = ""
    prevOutput = ("","","")
    MALURL = "https://myanimelist.net/"
    CurrentDir = getcwd()
    # default image when there is no cover art to display.
    # this method should work with auto-py-to-exe or pyinstaller.
    default_pngPath = path.join((getattr(sys, '_MEIPASS', path.dirname(path.abspath('designismypassion.png')))), 'designismypassion.png')
    pil_im = Image.open(default_pngPath)
    d = io.BytesIO()
    pil_im.save(d, 'png')
    default_png = d.getvalue()
    # if there is no config file, create one
    if not path.exists(CurrentDir + "/config.py"):
        with open("config.py", "w+") as file:
            file.write("API_key = \"******\"")
            file.close()
    # manually reads the Api key from the config file instead of importing it...
    # otherwise the value would be locked in when bundling the app.
    with open("config.py", "r") as file:
        API_key = file.read(-1)
        API_key = API_key[11:-1]
        file.close()

# ------------------------------------------------------------------------------
# General Functions
# ------------------------------------------------------------------------------

    # Yields every value in a dict where its key matches the argument.
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

    # Very inefficiently converts seconds to hours and minutes.
    def SecondsToString(secs):
        hrs = 0
        mins = 0
        if secs < 60:
             return (str(secs) + " seconds")
        while secs >= 3600:
            secs -= 3600
            hrs += 1
        while secs >= 60:
            secs -= 60
            mins += 1
        if hrs > 0:
            return (str(hrs) + " hour(s), " + str(mins) + " minute(s)")
        else:
            return (str(mins) + " minute(s)")

    # Call this whenever the user changes the settings, to make sure the lists are updated.
    def SettingsChanged():
        global prevAPIcall, prevXMLfile
        prevAPIcall = ""
        prevXMLfile = ""

    # Clears the output before displaying the next anime.
    def ClearOutput():
        global default_png, MALURL
        window['-OUTPUT_IMG-'].update(image_data=default_png)
        window['-OUTPUT-'].update("")
        window['-OUTPUT_score-'].update("")
        window['-OUTPUT_duration-'].update("")
        window['-OUTPUT_rating-'].update("")
        window['-OUTPUT_genre-'].update("")
        MALURL = 'https://myanimelist.net/'
        
    # Saves the current output for the back button as a tuple. (title, id, coverURL)
    # call with empty strings to return the last saved output as a tuple.
    def SaveOutput(AnimeTitle, AnimeID, AnimeCoverURL):
        global prevOutput
        if AnimeTitle == "" and AnimeID == "" and AnimeCoverURL == "":
            return prevOutput
        else:
            prevOutput = (AnimeTitle, AnimeID, AnimeCoverURL)

    # Updates the GUI with the current output.
    # this function always makes 1 API call to get additional anime info.
    # intended to be used with output from GetRandomAnime()
    def displayOutput(AnimeTitle, AnimeID, AnimeCoverURL):
        try:
            # Get the anime's details from the API using the ID.
            AnimeEnglish, AnimeMean, AnimeEpisodes, AnimeDuration, AnimeRating, AnimeGenres = GetAnimeInfo(AnimeID)
            # Clear the output.
            ClearOutput()
            # update clickable image link.
            MALURL = 'https://myanimelist.net/anime/' + str(rnd_id)
            # Update cover image.
            if AnimeCoverURL != '':
                window['-OUTPUT_IMG-'].update(image_data=GetCoverArt(AnimeCoverURL))
            else:
                window['-OUTPUT_IMG-'].update(image_data=default_png)
            # Update title.
            window['-OUTPUT-'].update(AnimeTitle)
            if (values['-showEng-'] == True) and (AnimeEnglish != ''):
                window['-OUTPUT-'].update(AnimeEnglish)
            # Update mean score.
            if (values['-showScore-'] == True):
                window['-OUTPUT_score-'].update("Score: " + str(AnimeMean))
            # Update duration.
            if (values['-showDuration-'] == True):
                if (AnimeEpisodes > 1 and AnimeDuration != '?'):
                    window['-OUTPUT_duration-'].update(str(AnimeEpisodes) + " episodes, averaging " + SecondsToString(AnimeDuration) + " each.")
                elif (AnimeEpisodes > 1):
                    window['-OUTPUT_duration-'].update(str(AnimeEpisodes) + " episodes, unknown duration.")
                if (AnimeEpisodes == 1 and AnimeDuration != '?'):
                    window['-OUTPUT_duration-'].update(SecondsToString(AnimeDuration) + ".")
                elif (AnimeEpisodes == 1):
                    window['-OUTPUT_duration-'].update("Unknown duration.")
                if (AnimeEpisodes == 0 and AnimeDuration != '?'):
                    window['-OUTPUT_duration-'].update(SecondsToString(AnimeDuration) + " per episode on average.")
                elif (AnimeEpisodes == 0):
                    window['-OUTPUT_duration-'].update("Unknown duration.")
            # Update rating and genres.
            if (values['-showInfo-'] == True):
                AnimeRating = AnimeRating.replace('_', '-')
                AnimeRating = AnimeRating.upper()
                window['-OUTPUT_rating-'].update("Rating: " + "{}".format(AnimeRating))
                window['-OUTPUT_genre-'].update("Genres:" + AnimeGenres[1:])
        except:
            ClearOutput()
            window['-OUTPUT-'].update("Error: Display error.")

    # Returns a tuple with the title, MAL page, and cover art URL from the lists.
    def GetRandomAnime():
        rand_index = randint(0, len(list_titles)-1)
        if values['-useXML-'] == True:
            return "{}".format(list_titles[rand_index]), \
                list_id[rand_index], \
                XMLgetCoverURL(list_id[rand_index])
        else:
            return "{}".format(list_titles[rand_index]), \
                list_id[rand_index], \
                list_coverImg[rand_index]

    # Returns png image of the cover art from the URL.
    # makes 1 API call every time this function is called.
    def GetCoverArt(coverURL):
        try:
            url = coverURL
            #url = "https://cdn.myanimelist.net/images/anime/1682/101883l.jpg" # wide image for testing
            sleep(0.5)  # Sleep to prevent rate limiting.
            response = requests.get(url, stream=True)
            response.raw.decode_content = True # Get jpg format bytes from response...
            jpg_img = Image.open(io.BytesIO(response.content)) # open PIL image from bytes...
            png_img = io.BytesIO()  # create BytesIO object to store png...
            jpg_img.save(png_img, format="PNG") # save data in png format...
            png_data = png_img.getvalue() # save as bytes.
            return png_data
        except:
            return default_png
    
    # Returns a tuple with english title, mean score, #of episodes, duration in seconds, rating, and genres.
    # makes 1 API call every time this function is called.
    def GetAnimeInfo(animeID):
        url = 'https://api.myanimelist.net/v2/anime/' + str(animeID) + '?fields=alternative_titles,mean,num_episodes,average_episode_duration,rating,genres'
        headers = {'X-MAL-CLIENT-ID': API_key}
        sleep(0.5)  # Sleep to prevent rate limiting.
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return '', '?', '?', '0', '?', '?'
        responseBytes = (response.content)
        responseString = responseBytes.decode("utf-8")
        outputDict = jsonLoads(responseString)
        # Make a string and append any genre tags to it.
        genreString = ""
        for item in gen_dict_extract(outputDict, 'name'): 
            genreString = genreString + ("/ " + item + " ")
        #Fill any missing information with default values.
        if 'alternative_titles' not in outputDict:
            outputDict['alternative_titles']['en'] = ''
        if 'mean' not in outputDict:
            outputDict['mean'] = '?'
        if 'num_episodes' not in outputDict:
            outputDict['num_episodes'] = '0'
        if 'average_episode_duration' not in outputDict:
            outputDict['average_episode_duration'] = '?'
        if 'rating' not in outputDict:
            outputDict['rating'] = '?'
        #return the tuple using the values from the dict.
        return outputDict['alternative_titles']['en'], \
            outputDict['mean'], \
            outputDict['num_episodes'], \
            outputDict['average_episode_duration'], \
            outputDict['rating'], \
            genreString

# ------------------------------------------------------------------------------
# API Functions - only called when using API method
# ------------------------------------------------------------------------------

    # Pull user's animelist by calling the MAL API, save the response to a dictionary.
    # makes 1 API call every time this function is called.
    def APIgetAnimeList(user_name):
        global prevAPIcall
        if user_name == prevAPIcall:  # Prevents redundant API calls.
            return
        url = 'https://api.myanimelist.net/v2/users/' + str(user_name) +\
            '/animelist?fields=list_status,media_type&status=plan_to_watch&limit=1000'  # 1000 is the max allowed by MAL.
        headers = {'X-MAL-CLIENT-ID': API_key}
        sleep(0.5)  # Sleep to prevent rate limiting.
        response = requests.get(url, headers=headers)            
        if response.status_code != 200:
            if response.status_code == 404:
                window.Element('-OUTPUT-').Update('Error: No anime list found for ' + user_name)
                raise Exception('API call failed status code: 404')
            else:
                window.Element('-OUTPUT-').Update("Error: API failed Status code: " + str(response.status_code))
                raise Exception('API call failed status code: ' + str(response.status_code))
        responseBytes = (response.content)
        responseString = responseBytes.decode("utf-8")
        outputDict = jsonLoads(responseString)
        # Clear the lists when username or settings change.
        list_titles.clear()
        list_id.clear()
        list_coverImg.clear()
        # Populate the lists from the API response.
        for item in gen_dict_extract(outputDict, 'node'): 
            list_titles.append(item['title'])
            list_id.append(item['id'])
            list_coverImg.append(item['main_picture']['medium'])
            if (item['media_type'] == "movie") and (no_movies == True):
                list_titles.pop()
                list_id.pop()
                list_coverImg.pop()
            if (item['media_type'] != "movie") and (only_movies == True):
                list_titles.pop()
                list_id.pop()
                list_coverImg.pop()
        prevAPIcall = user_name

# ------------------------------------------------------------------------------
# XML Functions - only called when using the XML method
# ------------------------------------------------------------------------------

    # Pull anime list from MAL xml file, save directly to lists.
    def XMLgetAnimeList(XMLfile):
        global prevXMLfile
        if XMLfile == prevXMLfile: # Prevents redundant XML parsing.
            return
        # Clear the lists when username or settings change
        list_titles.clear()
        list_id.clear()
        list_coverImg.clear()
        # Populate the lists from the XML file.
        list_tree = ET.parse(XMLfile)
        tree_root = list_tree.getroot()
        for anime in tree_root.findall("anime"): # From each <anime> in the xml...
            if anime.find("my_status").text == "Plan to Watch":# where my_status == PTW...
                list_titles.append(anime.find("series_title").text ) # append the series_title to ptw_list...
                list_id.append(anime.find("series_animedb_id").text) # then, append its series_animedb_id to ptw_list_id.
                if (anime.find("series_type").text == "Movie") and (no_movies == True):
                    list_titles.pop()
                    list_id.pop()
                if (anime.find("series_type").text != "Movie") and (only_movies == True):
                    list_titles.pop()
                    list_id.pop()
        prevXMLfile = XMLfile

    # Get URL for cover art of a single anime, using the API. (Only way I could find to get the cover art.)
    # makes 1 API call every time this function is called.
    def XMLgetCoverURL(animeID):
        try:
            url = 'https://api.myanimelist.net/v2/anime/' + str(animeID) + '?fields=main_picture'
            headers = {'X-MAL-CLIENT-ID': API_key}
            sleep(0.5)  # Sleep to prevent rate limiting.
            response = requests.get(url, headers=headers)            
            if response.status_code != 200:
                return ''
            responseBytes = (response.content)
            responseString = responseBytes.decode("utf-8")
            outputDict = jsonLoads(responseString)
            return outputDict['main_picture']['medium']
        except:
            return ''
        
# ------------------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------------------
   
    Gooey.theme('LightGrey1')
    # Output Columns.
    col_left = [[Gooey.Button(image_data=default_png, key="-OUTPUT_IMG-",image_size=(200,278), \
                                size=(200,278), tooltip="Click to open in browser.")]]
    col_rite = [[Gooey.Text("", font='Verdana 12 bold', size=(33, 2), key='-OUTPUT-')],
                [Gooey.Text("", font='Verdana 11', size=(15, 1), key='-OUTPUT_score-')],
                [Gooey.Text("", font='Verdana 11', size=(45, 1), key='-OUTPUT_duration-')],
                [Gooey.Text("", font='Verdana 11', size=(15, 1), key='-OUTPUT_rating-')],
                [Gooey.Text("", font='Verdana 11', size=(25, 4), key='-OUTPUT_genre-')]]
    # The main tab.
    tab1_layout = [[Gooey.Text('MAL username:'),
                     Gooey.InputText(key='-username-', right_click_menu=[[''], ['Paste Username']])],
                   [Gooey.Radio("Exclude Movies", 666, default=False, disabled=False, enable_events=True, key='-no_Movies-'),
                     Gooey.Radio("Only Movies/OVA", 666, default=False, disabled=False, enable_events=True, key='-only_Movies-'),
                     Gooey.Radio("Any anime", 666, default=True, disabled=False, enable_events=True, key='-any_Anime-')],
                   [Gooey.Column(col_left), Gooey.Column(col_rite)]] #<-- Output Columns.
    # The settings tab.
    tab2_layout = [[Gooey.Push(), Gooey.T('API Key:'),
                     Gooey.In(key='-apiKeyInput-', default_text=API_key , password_char='●', right_click_menu=[[''], ['Paste API key']]),
                     Gooey.Button('Save', key='-SAVE-')],
                   [Gooey.Checkbox('Use local XML file', key='-useXML-', enable_events=True),
                     Gooey.Push(), Gooey.T('XML file:'),
                     Gooey.Input(key='-XMLfileInput-'), Gooey.FileBrowse()],
                   [Gooey.Checkbox('Show english title', default=False, key='-showEng-')],
                   [Gooey.Checkbox('Show mean score', default=True, key='-showScore-')],
                   [Gooey.Checkbox('Show duration', default=True, key='-showDuration-')],
                   [Gooey.Checkbox('Show additional info', default=False,  key='-showInfo-')]]
    # The main layout.
    layout = [
        [Gooey.TabGroup([[Gooey.Tab('Main', tab1_layout), 
                          Gooey.Tab('Settings', tab2_layout)]])],
        [Gooey.Push(),Gooey.Button('Back', disabled=True), Gooey.Button('Randomize!', bind_return_key=True), Gooey.Button('Exit')]]
    window = Gooey.Window('MAL Randomizer', layout)  # Create the window.

    # Loop listening for GUI events.
    while True:
        event, values = window.read()
        if event == 'Paste Username':
            window['-username-'].update(Gooey.clipboard_get(), paste=True)
        if event == 'Paste API key':
            window['-apiKeyInput-'].update(Gooey.clipboard_get(), paste=True)
        if event in (666, '-no_Movies-'):
            no_movies = True
            only_movies = False
            SettingsChanged()
        if event in (666, '-only_Movies-'):
            no_movies = False
            only_movies = True
            SettingsChanged()
        if event in (666, '-any_Anime-'):
            no_movies = False
            only_movies = False
            SettingsChanged()
        if event == '-useXML-':
            SettingsChanged()
        if event == '-showInfo-':
            SettingsChanged()
        if event in ('-SAVE-'):
            API_key = values['-apiKeyInput-']
            with open('config.py', 'w+') as file:
                file.write("API_key = \"" + API_key + "\"")
        if event in ('-OUTPUT_IMG-'):
            # user clicks on the cover image.
            webbrowser.open_new_tab(MALURL)
        if event == 'Randomize!':
            if values['-useXML-'] == True:
                try: # Use local XML file.
                    XMLgetAnimeList(values['-XMLfileInput-'])
                except:
                    ClearOutput()
                    window['-OUTPUT-'].update("Error: Failed to parse XML file.")
                    continue
                if not list_titles and not list_id: # If the lists are empty after parsing the xml.
                    ClearOutput()
                    window['-OUTPUT-'].update("Error: No anime found in XML file.")
                    continue
            else: # Use only API calls.
                try:
                    APIgetAnimeList(values['-username-'])
                except:
                    ClearOutput()
                    window['-OUTPUT-'].update("Error: Failed to get anime list.")
                    continue
                if not list_titles and not list_id and not list_coverImg:# If the list is empty after API call.
                    ClearOutput()
                    window['-OUTPUT-'].update("Error: No anime found in PTW list.")
                    continue
            # save current output, enable the back button.
            SaveOutput(rnd_Title, rnd_id, rnd_CoverURL)
            window['Back'].update(disabled=False)
            # Get the random anime from the list.
            rnd_Title, rnd_id, rnd_CoverURL = GetRandomAnime()
            # Display the anime in the GUI.           
            displayOutput(rnd_Title, rnd_id, rnd_CoverURL)            
        if event == 'Back':
            window['Back'].update(disabled=True)#<---- Prevent multiple  uses of the back button. 
            try:
                if prevOutput[1] != '':
                    displayOutput(prevOutput[0], prevOutput[1], prevOutput[2])
                    _buffer = (rnd_Title, rnd_id, rnd_CoverURL)
                    rnd_Title, rnd_id, rnd_CoverURL = prevOutput
                    prevOutput = _buffer
                else:
                    ClearOutput()
            except:
                ClearOutput()
                window['-OUTPUT-'].update("Error: Back button error.")
        if event in (Gooey.WIN_CLOSED, 'Exit'):
            sys.exit(0)
