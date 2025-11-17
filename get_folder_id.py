import os
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_drive_service():
    """Lấy service Google Drive từ token đã xác thực"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    service = build('drive', 'v3', credentials=creds)
    return service

def find_or_create_folder(service, folder_name):
    """Tìm folder theo tên, nếu không có thì tạo mới"""
    # Tìm folder
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    folders = results.get('files', [])
    
    if folders:
        folder_id = folders[0]['id']
        print(f"Đã tìm thấy folder '{folder_name}' với ID: {folder_id}")
        return folder_id
    else:
        # Tạo folder mới
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"Đã tạo folder mới '{folder_name}' với ID: {folder_id}")
        return folder_id

if __name__ == '__main__':
    service = get_drive_service()
    folder_id = find_or_create_folder(service, 'VideoSummarize')
    print(f"\nLưu ID này để dùng: {folder_id}")
