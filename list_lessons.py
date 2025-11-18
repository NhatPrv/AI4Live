#!/usr/bin/env python3
"""
Script để lấy danh sách bài học từ Google Drive folder VideoSummarize
Trả về JSON để PHP xử lý
"""

import os
import sys
import json
import pickle
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_drive_service():
    """Lấy service Google Drive từ token đã xác thực"""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.pickle')
    
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    else:
        print(json.dumps({"error": "Chưa xác thực Google Drive. Chạy upload_to_drive.py trước."}), file=sys.stderr)
        sys.exit(1)
    
    service = build('drive', 'v3', credentials=creds)
    return service

def find_folder(service, folder_name):
    """Tìm folder theo tên"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    return None

def list_lessons(service, folder_id):
    """Liệt kê tất cả bài học trong folder"""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        pageSize=100,
        orderBy='modifiedTime desc',
        fields="files(id, name, createdTime, modifiedTime, webViewLink)"
    ).execute()
    
    files = results.get('files', [])
    
    lessons = []
    for f in files:
        lessons.append({
            'id': f['id'],
            'title': f['name'].replace('.md', '').replace('_', ' '),
            'fileName': f['name'],
            'createdTime': f.get('createdTime', ''),
            'modifiedTime': f.get('modifiedTime', ''),
            'link': f.get('webViewLink', '')
        })
    
    return lessons

if __name__ == '__main__':
    try:
        service = get_drive_service()
        folder_id = '1Z36vizWmxAP0PCgg1p83To7LQdaoMB0S'  # Fixed VideoSummarize folder ID
        lessons = list_lessons(service, folder_id)
        print(json.dumps(lessons, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
