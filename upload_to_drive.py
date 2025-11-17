import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import pickle

# Quyền truy cập Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """Xác thực và tạo service Google Drive"""
    creds = None
    
    # File token.pickle lưu access token và refresh token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Nếu không có credentials hợp lệ, yêu cầu đăng nhập
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Lưu credentials cho lần sau
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    service = build('drive', 'v3', credentials=creds)
    return service

def create_folder(service, folder_name, parent_id=None):
    """Tạo folder trên Google Drive"""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"Đã tạo folder '{folder_name}' với ID: {folder.get('id')}")
    return folder.get('id')

def upload_file(service, file_path, folder_id=None):
    """Upload file lên Google Drive"""
    file_name = os.path.basename(file_path)
    
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    print(f"Đã upload '{file_name}'")
    print(f"File ID: {file.get('id')}")
    print(f"Link xem: {file.get('webViewLink')}")
    return file.get('id')

def upload_content(service, file_name, content, folder_id=None):
    """Upload nội dung trực tiếp lên Google Drive (không cần file tạm)"""
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    media = MediaIoBaseUpload(
        io.BytesIO(content.encode('utf-8')),
        mimetype='text/markdown',
        resumable=True
    )
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    print(f"Đã upload '{file_name}'")
    print(f"File ID: {file.get('id')}")
    print(f"Link xem: {file.get('webViewLink')}")
    return file.get('id')

def list_files(service, folder_id=None, page_size=10):
    """Liệt kê files trong Google Drive"""
    query = f"'{folder_id}' in parents" if folder_id else None
    
    results = service.files().list(
        q=query,
        pageSize=page_size,
        fields="files(id, name, createdTime, webViewLink)"
    ).execute()
    
    files = results.get('files', [])
    
    if not files:
        print('Không tìm thấy file nào.')
    else:
        print('Danh sách files:')
        for file in files:
            print(f"  - {file['name']} (ID: {file['id']})")
            print(f"    Link: {file.get('webViewLink')}")
    
    return files

def find_or_create_folder(service, folder_name):
    """Tìm folder theo tên, nếu không có thì tạo mới"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    folders = results.get('files', [])
    
    if folders:
        folder_id = folders[0]['id']
        print(f"Đã tìm thấy folder '{folder_name}' với ID: {folder_id}")
        return folder_id
    else:
        folder_id = create_folder(service, folder_name)
        return folder_id

def upload_lesson_with_title(service, content, video_title, folder_id=None):
    """Upload bài học với tên file theo tiêu đề video"""
    import datetime
    import re
    
    # Làm sạch tiêu đề để dùng làm tên file
    clean_title = re.sub(r'[<>:"/\\|?*]', '', video_title)
    clean_title = clean_title.strip()[:100]  # Giới hạn 100 ký tự
    
    # Thêm timestamp để tránh trùng tên
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_title}_{timestamp}.md"
    
    return upload_content(service, filename, content, folder_id)

if __name__ == '__main__':
    import sys
    
    # Tạo service
    service = get_drive_service()
    
    # Tìm hoặc tạo folder VideoSummarize
    folder_id = find_or_create_folder(service, 'VideoSummarize')
    
    # Kiểm tra xem có truyền tiêu đề video không
    if len(sys.argv) > 1:
        video_title = sys.argv[1]
        # Upload với tên file theo tiêu đề
        if os.path.exists('lesson_output.md'):
            with open('lesson_output.md', 'r', encoding='utf-8') as f:
                content = f.read()
            upload_lesson_with_title(service, content, video_title, folder_id)
        else:
            print("Không tìm thấy file lesson_output.md")
    else:
        # Upload file lesson_output.md với tên mặc định
        if os.path.exists('lesson_output.md'):
            upload_file(service, 'lesson_output.md', folder_id)
        else:
            print("Không tìm thấy file lesson_output.md")
    
    # Liệt kê files trong folder VideoSummarize
    print("\n" + "="*50)
    print("Files trong folder VideoSummarize:")
    list_files(service, folder_id=folder_id, page_size=10)
