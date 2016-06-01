from google_photo_sync import *
from client_data import *

email = raw_input('enter the email for google photo account --> ')

gd_client = OAuth2Login(client_secret, credential_store, email)

current_dir = os.getcwd()
updirectory = current_dir + '\%s\%s' % ('testing_gpsync', 'test_album')
dwlddirectory = updirectory + '\%s' % ('test_album')


def album_download_test(gd_client, dwlddirectory):
    webAlbums = gd_client.GetUserFeed()
    for album in webAlbums.entry:
        if album.title.text == 'test_album':
            download_album(gd_client, album, dwlddirectory)

    localphototitle = os.listdir(dwlddirectory)
    assert (len(localphototitle) == 2), 'album download test failed'
    assert (localphototitle == ['testphoto1.jpg',
                                'testphoto2.jpg']), 'album download test failed'
    print '\n==================ALBUM DOWNLOAD TEST PASSED==================\n'


def album_upload_test(gd_client):
    localAlbums = get_local_albums(find_media(updirectory))
    upload_album(gd_client, 'test_album', localAlbums['test_album'])
    albums = gd_client.GetUserFeed()
    for album in albums.entry:
        if album.title.text == 'test_album':
            numphotos = album.numphotos.text
            assert (numphotos == '2'), 'album upload test failed'

            webphototitle = []
            photos = get_photos_for_picasa_album(gd_client, album)
            for photo in photos:
                webphototitle.append(photo.title.text)
            assert (webphototitle == ['testphoto1.jpg',
                                      'testphoto2.jpg']), 'album upload test failed'
    print '\n==================ALBUM UPLOAD TEST PASSED==================\n'


def album_sync_by_add_test(gd_client, dwlddirectory):
    photo1path = dwlddirectory + '\%s' % ('testphoto1.jpg')
    os.remove(photo1path)
    localAlbums = get_local_albums(find_media(dwlddirectory))
    webAlbums = get_web_albums(gd_client)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    for photo in photos:
        if photo.title.text == 'testphoto2.jpg':
            gd_client.Delete(photo)

    download_missing_photo(gd_client, ['test_album'], webAlbums, localAlbums)
    upload_missing_photo(gd_client, ['test_album'], localAlbums, webAlbums)

    localphototitle = os.listdir(dwlddirectory)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    webphototitle = []
    for photo in photos:
        webphototitle.append(photo.title.text)
    assert (len(webphototitle) == 2), 'album Sync by add test failed'
    assert (webphototitle == ['testphoto1.jpg',
                              'testphoto2.jpg']), 'album Sync by add test failed'
    assert (len(localphototitle) == 2), 'album Sync by add test failed'
    assert (localphototitle == [
            'testphoto1.jpg', 'testphoto2.jpg']), 'album Sync by add test failed'

    print '\n==================ALBUM SYNC BY ADDING TEST PASSED==================\n'


def album_sync_by_del_test(gd_client, dwlddirectory):

    photo1path = dwlddirectory + '\%s' % ('testphoto1.jpg')
    os.remove(photo1path)
    localAlbums = get_local_albums(find_media(dwlddirectory))
    webAlbums = get_web_albums(gd_client)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    for photo in photos:
        if photo.title.text == 'testphoto2.jpg':
            gd_client.Delete(photo)

    del_extra_from_web(gd_client, ['test_album'], localAlbums, webAlbums)

    del_extra_from_local(gd_client, ['test_album'], localAlbums, webAlbums)

    localphototitle = os.listdir(dwlddirectory)
    photos = get_photos_for_picasa_album(gd_client, webAlbums['test_album'])
    webphototitle = []
    for photo in photos:
        webphototitle.append(photo.title.text)
    assert (len(webphototitle) == 0), 'album Sync by deletion test failed'
    assert (webphototitle == []), 'album Sync by deletion test failed'
    assert (len(localphototitle) == 0), 'album Sync by deletion test failed'
    assert (localphototitle == []), 'album Sync by deletion test failed'

    print '\n==================ALBUM SYNC BY DELETING TEST PASSED==================\n'

album_upload_test(gd_client)
album_download_test(gd_client, dwlddirectory)
album_sync_by_add_test(gd_client, dwlddirectory)
album_sync_by_del_test(gd_client, dwlddirectory)

os.rmdir(dwlddirectory)
testalbum = find_album(gd_client, 'test_album')
gd_client.Delete(testalbum)

print '\n==================ALL TESTS PASSED SUCCESSFULLY==================\n'
