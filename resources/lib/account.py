import requests
from resources.lib.globals import *
import xbmc, xbmcaddon, xbmcgui
import time, uuid


LOGIN_URL = 'https://dce-frontoffice.imggaming.com/api/v2/login'
REFRESH_URL = 'https://dce-frontoffice.imggaming.com/api/v2/token/refresh'
STREAM_BASE_URL = 'https://dce-frontoffice.imggaming.com/api/v2/stream/'
EVENT_BASE_URL = 'https://dce-frontoffice.imggaming.com/api/v2/event/'

class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''
    session_key = ''
    icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
    verify = True

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')
        self.login_token = self.addon.getSetting('login_token')
        self.refresh_token = self.addon.getSetting('refresh_token')
        self.last_login = self.addon.getSetting('last_login')

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM,
                                    option=xbmcgui.ALPHANUM_HIDE_INPUT)

        if self.username == '' or self.password == '':
            dialog.notification("Error Occured", "", self.icon, 5000, False)
            sys.exit()

        payload = '{{"id":"{}","secret":"{}"}}'.format(self.username, self.password)

        r = requests.post(LOGIN_URL, headers=SIMPLE_HEADER, data=payload, verify=self.verify)
        if not check_request_result(r, 201):
            sys.exit()

        self.login_token = r.json()['authorisationToken']
        self.refresh_token = r.json()['refreshToken']
        self.last_login = str(time.time())

        self.addon.setSetting('login_token', self.login_token)
        self.addon.setSetting('refresh_token', self.refresh_token)
        self.addon.setSetting('last_login', self.last_login)
        self.addon.setSetting('username', self.username)
        self.addon.setSetting('password', self.password)

    def reauthorize(self):
        payload = ('{"refreshToken":"%s"}') % (self.refresh_token)
        r = requests.post(REFRESH_URL, headers=generate_authorization_header(self.login_token), data=payload, verify=True)
        if not check_request_result(r, 201):
            self.login()
            return
        self.login_token = r.json()['authorisationToken']
        self.last_login = str(time.time())
        self.addon.setSetting('login_token', self.login_token)
        self.addon.setSetting('last_login', self.last_login)

    def logout(self):
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('refresh_token', '')
        self.addon.setSetting('last_login', '')
        self.username = ''
        self.password = ''
        self.login_token = ''
        self.refresh_token = ''
        self.last_login = ''

    def get_stream(self, path):
        if((time.time() - float(self.last_login)) > 10740.0):
            self.reauthorize()

        url = STREAM_BASE_URL + path
        r = requests.get(url, headers=generate_authorization_header(self.login_token), verify=True)
        if not check_request_result(r, 200):
            sys.exit()
        url = r.json()['playerUrlCallback']

        hls_url = ''
        while hls_url == '' or 'cdnfastly' in hls_url:
            r = requests.get(url)
            if not check_request_result(r, 200):
                sys.exit()
            hls_url = r.json()['hlsUrl']
        return hls_url

    def get_event_stream(self, content_id):
        if((time.time() - float(self.last_login)) > 10740.0):
            self.reauthorize()

        url = EVENT_BASE_URL + content_id
        r = requests.get(url, headers=generate_authorization_header(self.login_token), verify=True)
        if not check_request_result(r, 200):
            sys.exit()

        sportId = r.json()['events'][0]['sportId']
        propertyId = r.json()['events'][0]['propertyId']
        tournamentId = r.json()['events'][0]['tournamentId']
        id = r.json()['events'][0]['id']
        return self.get_stream('event/' + str(sportId) + '/'+ str(propertyId) + '/' + str(tournamentId) + '/' + str(id))
