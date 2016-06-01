# google_photo_sync
This is a Google Photos Two Way Sync Utility enabling syncing between Local Albums and Google Photos/Picasa Albums.

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
+ google-api-python-client (1.5.0)

    ```
    $ pip install --upgrade google-api-python-client
    ```
+ nose (1.3.7) for running nosetests

    ```
    $ pip install nose
    ```

### Authentication
For first time use and for a new user we require client_secret.json file for authentication your google account for OAuth2 authentication. Following are required steps:
+ First create a project through the Google Developer Console: at https://console.developers.google.com/
+ Under API manager, click Credentials. Then go to _**"OAuth Consent Screen"**_ and give product name "piyush_gpsync" or any other name and save it.
+ Then under credentials click _**"create credentials"**_ and select _**"OAuth Client ID"**_ and choose application type as _**"other"**_.
+ Once the Client ID has been created click _**"Download JSON"**_ and save the file as _**client_secret.json**_ to a location you wish.

## Usage:
+ When running for the first time after generating Client Secret, edit and put the directory location of _**"client_secret.json"**_ file under variable _**"location_client_secret"**_ in _**"client_data.py"**_ file and save it.
+ To begin the utility, run _**"google_photo_sync.py"**_ in command line ```$ python .\google_photo_sync.py```. It will prompt for entering email ID. Enter the same email as used for generating client secret.
+ Next it requires an existing Directory to be entered where you have local albums for syncing.
+ It will then require you to authorize this application through your web browser. Once you do this you will get a code which you have to copy and paste into the application. 
+ Now you will get various options for download of album, upload of album or syncing of album.

## Running Test:
+ A test program _**"test_using_nosetests.py"**_ has been added which uses the test files kept in the folder _**testing_gpsync**_.
+ The _**"testing_gpsync"**_ folder must be in the current working directory to work.
+ Edit and change the _**email**_ in file _**"test_using_nosetests.py"**_ to the email id used for client generation.
+ Run the test typing ```$ nosetests .\test_using_nosetests.py``` in command line.
+ There is another test _**"test.py"**_ with similar functinality but without ant framework.

### Note:
+ "google_photo_sync" requires authorisation only for the first time use, as it saves the credentials as "credentials.dat” file for future use. **But if you wish not to save the credentials please use "gpsync_auth_req_everytime.py". This will ask for authentication code every time you start the utility.**
+ Different users require different "client_secret.json" created from their respective accounts.
+ This utility now supports only photos('.png','.jpg','.jpeg' and '.gif' only), but can be extended to other photo types and some video formats.

