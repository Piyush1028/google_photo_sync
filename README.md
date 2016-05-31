# google_photo_sync
This is a Google Photos Two Way Sync Utility enabling syncing between local albums and Google Photos/Picasa Albums.

## Features:
+ Download entire albums to specified local directory if not already present.
+ Upload entire albums to Google Photos account if not already present.
+ Download each Google Photos album as separate directory.
+ Upload each subdirectory (album) as separate album to Google account.
+ Ability to Sync between albums present at both places. It has two options:
  + Syncing by adding any missing file bidirectionally.
  + Syncing by deleting any extra file bidirectionally.
+ Ability to resume broken uploads.

## Requirements:
### Packages
+ Python 2.7
+ gdata (2.0.18)

    ```
    $ pip install gdata
    ```
+  google-api-python-client (1.5.0)

    ```
    $ pip install --upgrade google-api-python-client
    ```

### Authentication
For first time use and for a new user we require client_secret.json file for authentication your google account for OAuth2 authentication. Following are required steps:
+ First create a project through the Google Developer Console: at https://console.developers.google.com/
+ Under API manager, click Credentials. Then go to "OAuth Consent Screen" and give product name "piyush_gpsync" or any other name and save it.
+ Then under credentials click "create credentials" and select "OAuth Client ID" and choose application type as "other".
+ Once the Client ID has been created click "Download JSON" and save the file as client_secret.json to a location you wish.

## Usage:
+ When running for the first time after generating Client Secret, edit and put the directory location of "client_secret.json" file in "client_data.py" and save it.
+ To begin the utility, run "google_photo_sync.py" in command line. It will prompt for entering email ID. Enter the same email as used for generating client secret.
+ Next it requires an existing Directory to be entered where you have local albums for syncing.
+ It will then require you to authorize this application through your web browser. Once you do this you will get a code which you have to copy and paste into the application. 
+ Now you will get various options for download of album, upload of album or syncing of album.

### Note:

+ "google_photo_sync" requires authorisation only for the first time use, as it saves the credentials as "credentials.dat” file for future use. **But if you wish not to save the credentials please use "gpsync_auth_req_everytime.py". This will ask for authentication code every time you start the utility.**
+ Different users require different "client_secret.json" created from their respective accounts.
+ This utility now supports only photos('.png','.jpg','.jpeg' and '.gif' only), but can be extended to other photo types and some video formats.
+ **For running Nosetest, please edit and change the email Id to your email Id**
