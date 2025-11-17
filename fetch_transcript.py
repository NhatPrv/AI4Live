#!/usr/bin/env python3
"""
Fetch transcript helper - runs independently to avoid PHP subprocess network issues
Usage: python fetch_transcript.py VIDEO_ID LANGUAGE OUTPUT_FILE
"""
import sys
import json
from youtube_transcript_api import YouTubeTranscriptApi

def fetch_transcript(video_id, language='vi'):
    """Fetch transcript from YouTube"""
    try:
        # Create API instance
        api = YouTubeTranscriptApi()
        
        # Get list of available transcripts
        transcript_list = api.list(video_id)
        
        # Try requested language first
        for transcript in transcript_list:
            if transcript.language_code == language:
                fetched = api.fetch(video_id, [language])
                data = [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in fetched]
                return {'success': True, 'transcript': data, 'language': language}
        
        # Try fallback languages
        fallback_langs = ['vi', 'vi-VN', 'en', 'en-US']
        for lang in fallback_langs:
            if lang == language:
                continue
            for transcript in transcript_list:
                if transcript.language_code == lang:
                    fetched = api.fetch(video_id, [lang])
                    data = [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in fetched]
                    return {'success': True, 'transcript': data, 'language': lang}
        
        # If all fails, try first available transcript
        if transcript_list:
            first_lang = transcript_list[0].language_code
            fetched = api.fetch(video_id, [first_lang])
            data = [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in fetched]
            return {'success': True, 'transcript': data, 'language': first_lang}
        
        return {'success': False, 'error': 'No transcript available for this video'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(json.dumps({'success': False, 'error': 'Usage: fetch_transcript.py VIDEO_ID LANGUAGE OUTPUT_FILE'}))
        sys.exit(1)
    
    video_id = sys.argv[1]
    language = sys.argv[2]
    output_file = sys.argv[3]
    
    result = fetch_transcript(video_id, language)
    
    # Write result to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Print summary to stdout
    if result['success']:
        print(json.dumps({'success': True, 'count': len(result['transcript']), 'language': result['language']}))
    else:
        print(json.dumps(result))
    
    sys.exit(0 if result['success'] else 1)
