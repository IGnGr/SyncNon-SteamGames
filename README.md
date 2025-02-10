# SyncNon-SteamGames
A modified version of GameSync from Maikeru86 (https://github.com/Maikeru86/GameSync)

Automatically add Non-Steam Games to Steam with images from SteamGridDB

![GUI](images/GUI.png)


## Features
- Reads games from a specified installation directory.
- Generates unique AppIDs for non-Steam games.
- Fetches grid, hero, and logo images from SteamGridDB.
- Adds new games to Steam shortcuts.
- Removes shortcuts for games that are no longer installed.
- finds largest .exe in game folder and adds that as the game executable.
- logging
- (NEW) Changed the shown name in Steam of the games to be the name from steamgrid instead of the executable name
- (NEW) Added GUI
- (NEW) Inference of the steam_user_data_path so only 3 parameters are needed to be provide by the user
- (NEW) Storage of the variables in a json file at the script location
- (NEW) Changed slightly the messages to be logged, now it informs if a titles is being skipped when it's already present in steam.
- (NEW) Added exceptions to the names of executables to be found, to avoid using the wrong one in Unity games

## Limitations:
- Only 1 folder of games can be used. Altough any number of subfolders is okay. 

    This means that, as long as all games are under a given folder (for example: <b>C:\NonSteamGames\Game1Folder, C:\NonSteamGames\Game2Folder, C:\NonSteamGames\Game3Folder</b> and so on) you are okay. You would select C:\NonSteamGames as your desired folder in this case.

- Only tested in Windows
- The executable is located by size, which is not ideal. At this moment, the user must change the executable in Steam directly if the wrong one has been chosen.


## Requirements
- Windows
- NonSteam Games Folder: Path to the directory where your Non-Steam games are installed.
- SteamGridDB API Key: You have to generate one for yourself here: https://www.steamgriddb.com/profile/preferences/api
- Steam Installation path: Path where Steam is installed in your system.
### Using source

- Install the required libraries
```py
pip install requests vdf Gooey 
```
- Execute the script "SyncNon-SteamGames.py"


## Usage
- Download the packaged version from "Releases"
- Make sure the directories and SteamGridDB API fields are filled in.
- Run it


## Tips
If your library is huge and you are having difficulties locating the games, here is how you can find them easily  until Valve provides a filter in desktop mode (Only big picture has a filter for non-steam games):
- Enable the option to show only installed games
- Create 3 dynamics library: 
    - Single Player
    - Multi Player
    - Co op

    This should narrow the games in your "Uncategorized" section to be basically the ones we're looking for
- Create a new library on "Non-Steam" steam and add them
- Congratulations! your games are categorized and easily accessible

## 3rd Party libraries
- "Gooey" for the GUI (https://github.com/chriskiehl/Gooey)
- "Pyinstaller" for building the executable (https://github.com/pyinstaller/pyinstaller)
- "vdf" to read Valve's config files https://pypi.org/project/vdf/
- "requests" to handle the network side of thing  https://pypi.org/project/requests/