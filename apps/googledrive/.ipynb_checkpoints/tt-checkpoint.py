from backends import DefaultGoogleDriveClient

google_drive_client = DefaultGoogleDriveClient()

response = google_drive_client.media_upload(
    name='tt_test.html',
    file_path='tt_test.html',
    from_mimetype=google_drive_client.XLSX_MIME_TYPE,
    parents=['1HMW-KtLHPhH0DDQ9vSU5bIfgre5qhfFk'],
)
file_id = response.get('id')
google_drive_client.set_public_permission(file_id)
