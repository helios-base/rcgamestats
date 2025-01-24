import requests

def stopfile_check(host_name,api_key):
    result_post_url = "http://127.0.0.1:5000/communication/create_stop_file"

    headers = {
        'x-api-key': api_key,
        'x-host-name': host_name
    }

    result_response = requests.post(result_post_url,headers=headers)

    print("レスポンス内容:", result_response.text)

    print(result_response)
    if result_response.json().get('stop_check') == True:
        stop_file_path = '/home/fugakatayama/rcgame/client/condition/stop.txt'
        with open(stop_file_path, 'w') as f:
            f.write('stop')
            return 
    else:
        return     
