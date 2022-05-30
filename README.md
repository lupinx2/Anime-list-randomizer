# malptw-rand
Randomly selects an anime listing from your MAL plan to watch section.

Original code by renelic

I've made these changes:

* added a bat file for easier launching on Windows.

* prompts the user to pick an xml file from the current directory instead of needing it as an argumennt.

* "Exclude movies" and "Only movies" options


## Requirements
- Python 3.2+

## How to get your exported XML MAL file
Go to your MAL anime list page and locate the sidebar on the right. Then click the `Export` button.

![Export Button](https://i.ibb.co/TB9rnhX/mal1.png)

Select anime list from the dropdown.

![Dropdown Selection](https://i.ibb.co/VNGjrLR/image.png)

Then click the following link to download your list. Make sure to extract it into the same folder that has the `malptw_rand.py` script.

![Download list](https://i.ibb.co/rfB7GJf/image.png)


## Usage
First clone/download this repo and make sure to follow the steps above and put your XML MAL file in same folder as `malptw_rand.py`.

If you're on Windows, you can just double-click the `run-malptw_rand.bat` file.

If you're not on Windows, or would prefer to use a terminal just `cd` into the repo folder. Then type:

`python malptw_rand.py`

or

`python3 malptw_rand.py`

to get a random anime from your PTW list.
