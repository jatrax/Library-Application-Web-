import os
# Your AZURE settings
APPLICATION_ID = "1d62d205-5661-42f6-877a-35dd0ca0a7e4"
CLIENT_ID = "31f4f9f9-bcf9-4c70-ae45-13a7b930e1bb"
CLIENT_SECRET = "Mt-8Q~TiaOlG4TE38Hw1WpfOBCS9PbtOEZoCTa8-"
AUTHORITY = "https://login.microsoftonline.com/consumers"
AUTHORITY_URL = 'https://login.microsoftonline.com/consumers/'
REDIRECT_PATH = "/getAToken"
ENDPOINT = 'https://graph.microsoft.com/v1.0/users'
SCOPE = ["User.ReadBasic.All"]
SESSION_TYPE = "filesystem"
REDIRECT_URI = "http://localhost:5000/getAToken"
#Your DB settings
db_host = 'localhost'
db_user = 'root'
db_password = 'root'
db_table = "library"
#Place your logo in base.html line:160