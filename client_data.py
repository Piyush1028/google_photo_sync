import os
# Please edit and put the directory path of your client secret json file
# which you have saved
location_client_secret = 'Edit and put the folder path where client_secret.json file is stored' # Example: 'D:\project\gpsync'
# Please rename your client secret json file as client_secret.json
client_secret = os.path.join(location_client_secret, 'client_secret.json')
# this will store the authentication details for future use, and will not
# require authentication every time
credential_store = os.path.join(location_client_secret, 'credentials.dat')
