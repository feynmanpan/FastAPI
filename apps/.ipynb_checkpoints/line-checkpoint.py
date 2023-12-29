from fastapi import Request
import requests

def send_line_notify(request: Request, message:str='OKOK'):
    token = 'pfBTtLVVjcjlBRZUmw9iEkelonBOoU56Xzd6SCfDb7J'
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': 'Bearer ' + token}
    data = {'message': message}
    response = requests.post(url, headers=headers, data=data)
#     response.raise_for_status()  # 檢查是否有錯誤發生
    print('Line Notify 發送成功！')
    return 'Line Notify 發送成功！'

# 填入你的 Line Notify 權杖和要發送的訊息
# token = 'pfBTtLVVjcjlBRZUmw9iEkelonBOoU56Xzd6SCfDb7J'
# message = '這是 Line Notify 測試訊息'

# send_line_notify(token, message)
