import os
import vdf
import requests
import logging
import zlib   
import json
from pathlib import Path
from gooey import Gooey, GooeyParser

def saveJsonFile(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def readJsonFile(filename):
    if(os.path.isfile(filename)):
        with open(filename, 'r') as f:
            return json.loads(f.read())
        
def determineUserdataFolder():
    #Assuming only 1 steam usser, on \\userdata we only have the '0' folder and the one with the ID, so we can infer it
    steam_user_data_ID = [x for x in os.listdir(os.path.join(steamdir_path,"userdata"))][1]
    return os.path.join(steamdir_path, "userdata", steam_user_data_ID, "config")
    

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

storedParametersJSONFilename = "parameters.json"

storedParametersJSON = {}
storedParametersJSON = readJsonFile(storedParametersJSONFilename)

game_installation_path = ""
steamgriddb_api_key = ""
steamdir_path = ""

##Taking them from the JSON if it exists
if storedParametersJSON:
    game_installation_path = storedParametersJSON["game_installation_path"]
    steamgriddb_api_key = storedParametersJSON["steamgriddb_api_key"] 
    steamdir_path = storedParametersJSON["steamdir_path"]


totalGames = 0
currentGame = 0


def read_current_games():
    """Read the current games from the game installation directory."""
    try:
        current_games = {folder.lower() for folder in os.listdir(game_installation_path) if os.path.isdir(os.path.join(game_installation_path, folder))}
        global totalGames
        totalGames = len(current_games)
        logger.info(f"Total number of games: {totalGames}")

    except Exception as e:
        logger.error(f"Error reading game installation directory {game_installation_path}: {e}")
        return set()
    return current_games

def generate_appid(game_name, exe_path):
    """Generate a unique appid for the game based on its exe path and name."""
    unique_name = (exe_path + game_name).encode('utf-8')
    legacy_id = zlib.crc32(unique_name) | 0x80000000
    return str(legacy_id)

def getGridImageURLBySize(json,image_type):
    imageSize = {'grid' : (600,900), 'home' : (920,430)}

    ##Locating the image type by size, and taking the first result 
    url = [x for x in json['data'] if x and x['width'] == imageSize[image_type][0] and x['height'] == imageSize[image_type][1]]
    if(url):
        return url[0]['url']
    else:
        return None

def fetch_steamgriddb_image(game_id, image_type):
    """Fetch a single image (first available) of specified type from SteamGridDB."""
    headers = {
        'Authorization': f'Bearer {steamgriddb_api_key}'
    }
    if image_type == 'hero':
        base_url = f'https://www.steamgriddb.com/api/v2/heroes/game/{game_id}'
    elif image_type == "home":
        base_url = f'https://www.steamgriddb.com/api/v2/grids/game/{game_id}'
    else: base_url = f'https://www.steamgriddb.com/api/v2/{image_type}s/game/{game_id}'
    response = requests.get(base_url, headers=headers)
    logger.info(f"Fetching {image_type} for game ID: {game_id}, URL: {base_url}, Status Code: {response.status_code}")


    if response.status_code == 200:
        data = response.json()
        if data['success'] and data['data']:
            if image_type == "home" or image_type == 'grid':
                return getGridImageURLBySize(data, image_type)
            return data['data'][0]['url']  # Return the URL of the first image found
        
    logger.error(f"Failed to fetch {image_type} for game ID: {game_id}")
    return None

def download_image(url, local_path):
    """Download an image from URL and save it locally."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded image from {url} to {local_path}")
            return True
    except Exception as e:
        logger.error(f"Failed to download image from {url}: {e}")
    return False

def save_images(appid, game_id):
    """Save grid, hero, and logo images for the game."""
    image_types = ['grid', 'hero', 'logo', 'home']
    for image_type in image_types:
        url = fetch_steamgriddb_image(game_id, image_type)
        if url:
            extension = os.path.splitext(url)[1]

            if image_type == 'grid':
                image_path = os.path.join(grid_folder, f'{appid}p{extension}')
            elif image_type == 'hero':
                image_path = os.path.join(grid_folder, f'{appid}_hero{extension}')
            elif image_type == 'logo':
                image_path = os.path.join(grid_folder, f'{appid}_logo{extension}')
            elif image_type == 'home':
                image_path = os.path.join(grid_folder, f'{appid}{extension}')

            logger.info(f"Saving {image_type} image for appid {appid} from {url} to {image_path}")
            if not os.path.exists(image_path):
                if download_image(url, image_path):
                    logger.info(f"Downloaded {image_type} image for appid {appid} from {url}")

def find_largest_exe(game_dir):
    largest_file = None
    largest_size = 0
    #To avoid the uninstaller or some other exe to be used, mostly in Unity games
    exceptions = ["unins","unity"]

    for root, dirs, files in os.walk(game_dir):
        for file in files:
            if file.endswith(".exe") and not any([x in file.lower() for x in exceptions]):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                if file_size > largest_size:
                    largest_size = file_size
                    largest_file = file_path
    
    return largest_file



def update_shortcuts(current_games):
    """Update the Steam shortcuts with new and removed games, and fetch/update images."""

    steam_user_data_path = determineUserdataFolder()

    global grid_folder
    grid_folder = os.path.join(steam_user_data_path, 'grid')  # Folder to store grid images
    # Ensure the grid folder exists
    Path(grid_folder).mkdir(parents=True, exist_ok=True)

    shortcuts_file = os.path.join(steam_user_data_path, 'shortcuts.vdf')

    try:
        # Load existing shortcuts or create new if the file doesn't exist
        if os.path.exists(shortcuts_file):
            with open(shortcuts_file, 'rb') as f:
                shortcuts = vdf.binary_load(f)
        else:
            shortcuts = {'shortcuts': {}}

        # Collect the current shortcuts
        existing_games = {os.path.basename(shortcut.get('StartDir', '').lower().strip('"')): shortcut for shortcut in shortcuts['shortcuts'].values()}

        # Remove shortcuts for games no longer in the installation directory
        for game_name, shortcut in existing_games.items():
            if game_name not in current_games:
                appid = shortcut.get('appid', '')
                # Remove images associated with the game
                for image_type in ['p', '_hero', '_logo','home']:
                    for ext in ['.jpg', '.png']:
                        if(image_type == 'home'):
                            image_path = os.path.join(grid_folder, f'{appid}{ext}')
                        else:
                            image_path = os.path.join(grid_folder, f'{appid}{image_type}{ext}')
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            logger.info(f"Removed {image_type} image for game: {game_name}")

                # Remove the shortcut from shortcuts file
                for idx, s in list(shortcuts['shortcuts'].items()):
                    if s.get('appname', '').strip().lower() == game_name:
                        del shortcuts['shortcuts'][idx]
                        logger.info(f"Removed shortcut for game: {game_name}")

        # Add or update games in shortcuts
        for game_name in current_games:
            game_path = os.path.join(game_installation_path, game_name)

            
            global currentGame
            currentGame += 1
            logger.info(f"Current game: {game_name}")
            logger.info(f"Games processed: {currentGame}/{totalGames}")

            if game_name in existing_games:
                logger.info(f"{game_name} already in Steam")

            if game_name not in existing_games:

                exe_file = find_largest_exe(game_path)
                if exe_file:
                    logger.info(f"Largest .exe file found: {exe_file}")
                else:
                    logger.error("No .exe files found in the game directory.")
                exe_path = os.path.join(game_path, exe_file)
                
                appid = generate_appid(game_name, exe_path)             
                # Search for the game on SteamGridDB and fetch images
                headers = {
                    'Authorization': f'Bearer {steamgriddb_api_key}'
                }
                search_url = f'https://www.steamgriddb.com/api/v2/search/autocomplete/{game_name}'
                response = requests.get(search_url, headers=headers)
                logger.info(f"Searching SteamGridDB for {game_name}, URL: {search_url}, Status Code: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if data['success']:
                        game_id = data['data'][0]['id']  # Assuming first result is the best match
                        game_name = data['data'][0]['name']
                        save_images(appid, game_id)

                # Add shortcut entry
                new_entry = {
                    "appid": appid, #change to game_id
                    "appname": game_name,
                    "exe": f'"{exe_path}"',
                    "StartDir": f'"{game_path}"',
                    "LaunchOptions": "",
                    "IsHidden": 0,
                    "AllowDesktopConfig": 1,
                    "OpenVR": 0,
                    "Devkit": 0,
                    "DevkitGameID": "",
                    "LastPlayTime": 0,
                    "tags": {}
                }
                shortcuts['shortcuts'][str(len(shortcuts['shortcuts']))] = new_entry
                logger.info(f"Added shortcut for game: {game_name}")




        # Save the updated shortcuts file
        with open(shortcuts_file, 'wb') as f:
            vdf.binary_dump(shortcuts, f)
            logger.info("Shortcuts file updated and saved.")



    except Exception as e:
        logger.error(f"Error updating shortcuts: {e}")


def GUI():

    parser = GooeyParser(description='Get your NonSteam Games added on Steam.')

    parser.add_argument(
        'game_installation_path',
        widget='DirChooser',
        metavar='NonSteam Games Folder',
        action='store',
        default = game_installation_path if game_installation_path else ''
        )
    
    parser.add_argument(
        'steamgriddb_api_key',
        metavar='SteamgridDB API Key',
        help='You can get yours in the link below:\nhttps://www.steamgriddb.com/profile/preferences/api\nSubstitute the link with the key after you have generated it',
        default = steamgriddb_api_key if steamgriddb_api_key else "https://www.steamgriddb.com/profile/preferences/api",
        action='store'
        )
    
    parser.add_argument(
        'steamdir_path',
        metavar='Steam Installation Path',
        widget='DirChooser',
        help = "By default C:\\Program Files (x86)\\Steam",
        default=steamdir_path if steamdir_path else 'C:\\Program Files (x86)\\Steam',
        action='store'
        )

    return parser.parse_args()

def storeVariablesFromGUI(args):
    global game_installation_path, steamgriddb_api_key, steamdir_path

    game_installation_path = args.game_installation_path
    steamgriddb_api_key = args.steamgriddb_api_key
    steamdir_path = args.steamdir_path
    
    storedParametersJSON = {}
    storedParametersJSON["game_installation_path"] = game_installation_path
    storedParametersJSON["steamgriddb_api_key"] = steamgriddb_api_key
    storedParametersJSON["steamdir_path"] = steamdir_path

    saveJsonFile(storedParametersJSONFilename, storedParametersJSON)

##Regex to reflect progress on GUI
@Gooey(progress_regex=r"Games processed: (?P<current>\d+)/(?P<total>\d+)$",
       progress_expr="current / total * 100")
def main():
    """Main function to check for new or removed games and update Steam shortcuts accordingly."""
    try:
        #We get the data from the GUI as arguments and store it into our JSON to avoid having to introduce it each time
        argumentsGUI = GUI()
        storeVariablesFromGUI(argumentsGUI)

        logger.info("Reading current games from installation directory...")
        current_games = read_current_games()

        #Workaround since backslash are not allowed in f-strings
        nl = '\n'
        #Parsed to have a game per line
        logger.info(f"Current games: {nl.join(str(current_games).split(','))}")

        determineUserdataFolder()

        logger.info("Updating shortcuts and fetching images...")
        update_shortcuts(current_games)

    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")

if __name__ == "__main__":
    main()
