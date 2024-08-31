# import modules
from base import *
from ui.ui_print import *
import urllib.parse
import releases
import re

base_url = "http://localhost:8181"
name = "zilean"
timeout_sec = 10
session = requests.Session()


def setup(cls, new=False):
    from settings import settings_list
    from scraper.services import active
    settings = []
    for category, allsettings in settings_list:
        for setting in allsettings:
            if setting.cls == cls:
                settings += [setting]
    if settings == []:
        if not cls.name in active:
            active += [cls.name]
    back = False
    if not new:
        while not back:
            print("0) Back")
            indices = []
            for index, setting in enumerate(settings):
                print(str(index + 1) + ') ' + setting.name)
                indices += [str(index + 1)]
            print()
            if settings == []:
                print("Nothing to edit!")
                print()
                time.sleep(3)
                return
            choice = input("Choose an action: ")
            if choice in indices:
                settings[int(choice) - 1].input()
                if not cls.name in active:
                    active += [cls.name]
                back = True
            elif choice == '0':
                back = True
    else:
        print()
        indices = []
        for setting in settings:
            if setting.name == "Zilean Base URL":
                setting.setup()
                if not cls.name in active:
                    active += [cls.name]


def scrape(query, altquery):
    from scraper.services import active
    ui_print("[zilean] searching for " + query + " accepting titles that regex match " + altquery)
    global base_url
    scraped_releases = []
    if not 'zilean' in active:
        return scraped_releases

    matches_regex = altquery
    if altquery == "(.*)":
        matches_regex = query
    media_type = "show" if regex.search(r'(S[0-9]|complete|S\?[0-9])', matches_regex, regex.I) else "movie"

    opts = []
    title = query
    if media_type == "show":
        s = (regex.search(r'(?<=S)([0-9]+)', matches_regex, regex.I).group()
             if regex.search(r'(?<=S)([0-9]+)', matches_regex, regex.I) else None)
        e = (regex.search(r'(?<=E)([0-9]+)', matches_regex, regex.I).group()
             if regex.search(r'(?<=E)([0-9]+)', matches_regex, regex.I) else None)
        if s is not None and int(s) != 0:
            opts.append('season=' + str(int(s)))
        if e is not None and int(e) != 0:
            opts.append('episode=' + str(int(e)))
        title = re.sub(r'S[0-9]+', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'E[0-9]+', '', title, flags=re.IGNORECASE).strip()
    else:
        # find year match at the end of the query string
        year_regex = regex.search(r'(.*)\.([12][0-9]{3})$', query, regex.I)
        if year_regex:
            opts.append('year=' + year_regex.group(2))
            title = year_regex.group(1)

    title = title.replace('.?', '').replace('.', ' ').replace('?', ' ').strip()
    opts.append('query=' + urllib.parse.quote(title))

    if base_url.endswith('/'):
        base_url = base_url[:-1]
    search_url = base_url + "/dmm/filtered?" + '&'.join(opts)

    try:
        ui_print("[zilean] using search URL: " + search_url)
        response = session.get(search_url, timeout=timeout_sec)

        if not response.status_code == 200:
            ui_print('[zilean] error ' + str(
                response.status_code) + ': failed response from zilean. ' + response.content)
            return []

    except requests.exceptions.Timeout:
        ui_print('[zilean] error: zilean request timed out.')
        return []
    except:
        ui_print(
            '[zilean] error: zilean couldn\'t be reached. Make sure your zilean base url [' + base_url + '] is correctly formatted.')
        return []

    try:
        response = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))
    except:
        ui_print('[zilean] error: unable to parse response:' + response.content)
        return []

    ui_print('[zilean] ' + str(len(response)) + ' results found.')
    for result in response[:]:
        if regex.match(r'(' + altquery + ')', result.rawTitle, regex.I):
            links = ['magnet:?xt=urn:btih:' + result.infoHash + '&dn=&tr=']
            seeders = 0  # not available
            scraped_releases += [releases.release(
                '[zilean]', 'torrent', result.rawTitle, [], float(result.size) / 1000000000, links, seeders)]
        else:
            ui_print('[zilean] skipping ' + result.rawTitle + ' because it does not match deviation ' + altquery)

    return scraped_releases
