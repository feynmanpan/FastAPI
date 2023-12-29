import os
from .backends import DefaultGoogleDriveClient

#################################################################


cwd = os.path.dirname(os.path.realpath(__file__))
fn = 'upload_me.txt'
upload_path = os.path.join(cwd, fn)
file_id = ''


def upload(cd=0):
    '''寫死測試上傳固定檔案到固定目錄'''
    global file_id
    try:
        google_drive_client = DefaultGoogleDriveClient()
        if cd == 0:
            response = google_drive_client.media_upload(
                name=fn,
                file_path=upload_path,  # 'upload_me.html',
                from_mimetype=google_drive_client.XLSX_MIME_TYPE,
                parents=['1HMW-KtLHPhH0DDQ9vSU5bIfgre5qhfFk'],
            )
            file_id = response.get('id')
            google_drive_client.set_public_permission(file_id)
        else:
            # 更新
            # file_id = "1d_xQ6Tgj1Sh98MicKZlC_DVU7JAy-evv"
            google_drive_client.media_update(
                file_id=file_id,
                file_path=upload_path,
                from_mimetype=google_drive_client.XLSX_MIME_TYPE
            )
    except Exception as e:
        msg = False, f'{["上傳","更新"][cd]}失敗: {fn}::{str(e)}'
    else:
        msg = True, f'{["上傳","更新"][cd]}成功: {fn}={file_id}'
    finally:
        return msg


if __name__ == '__main__':
    upload()
