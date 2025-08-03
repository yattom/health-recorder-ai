#!/usr/bin/env python3
"""
健康記録.2025.mdをJSONファイルに変換するスクリプト
"""

import json
import re
from datetime import datetime
import os

def parse_date(date_str):
    """日付文字列をパースしてdatetimeオブジェクトに変換"""
    # 曜日情報を削除
    date_str = re.sub(r'\([月火水木金土日]\)', '', date_str)
    
    # YYYY-M-D または YYYY-MM-DD の形式をサポート
    if '-' in date_str:
        parts = date_str.split('-')
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        return datetime(year, month, day)
    
    return None

def create_timestamp(date_obj, time_period):
    """日付と時間帯から ISO フォーマットのタイムスタンプを作成"""
    if time_period == '朝':
        hour, minute = 8, 30
    elif time_period == '夕':
        hour, minute = 17, 30
    else:  # 運動量など
        hour, minute = 12, 0  # 昼とする
    
    timestamp = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return timestamp.isoformat()

def create_filename(date_obj, time_period):
    """ファイル名を生成"""
    if time_period == '朝':
        hour, minute = 8, 30
    elif time_period == '夕':
        hour, minute = 17, 30
    else:  # 運動量など
        hour, minute = 12, 0
    
    timestamp = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return f"health_record_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"

def clean_content(content):
    """Windows改行コードをLinux形式に変換し、内容をクリーンアップ"""
    # Windows改行をLinux改行に変換
    content = content.replace('\r\n', '\n')
    # 末尾の空白文字を削除
    content = content.strip()
    return content

def parse_health_record(file_path):
    """健康記録ファイルをパースして構造化データを返す"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    entries = []
    current_entry = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # ヘッダー行を検出（#### で始まる）
        if line.startswith('#### '):
            # 前のエントリを保存
            if current_entry:
                entries.append(current_entry)
            
            # 新しいエントリを開始
            header = line[4:].strip()  # #### を削除
            
            # 日付と時間帯を抽出
            match = re.match(r'(\d{4}-\d{1,2}-\d{1,2})(?:\([月火水木金土日]\))?\s*[（(]?([^）)]*)[）)]?', header)
            if match:
                date_str = match.group(1)
                time_period = match.group(2) if match.group(2) else '朝'
                
                date_obj = parse_date(date_str)
                if date_obj:
                    current_entry = {
                        'date': date_str,
                        'time_period': time_period,
                        'date_obj': date_obj,
                        'content_lines': [],
                        'line_start': i + 1
                    }
        
        # 内容行を収集（空行でない、#### で始まらない行）
        elif current_entry and line and not line.startswith('#'):
            current_entry['content_lines'].append(line)
    
    # 最後のエントリを保存
    if current_entry:
        entries.append(current_entry)
    
    return entries

def convert_to_json_files(entries, output_dir, start_idx=0, end_idx=None):
    """エントリをJSONファイルに変換"""
    if end_idx is None:
        end_idx = len(entries)
    
    os.makedirs(output_dir, exist_ok=True)
    created_files = []
    
    for i in range(start_idx, min(end_idx, len(entries))):
        entry = entries[i]
        
        # 内容を結合
        content = '\n'.join(entry['content_lines'])
        content = clean_content(content)
        
        # JSONデータを作成
        json_data = {
            "health_record": content,
            "timestamp": create_timestamp(entry['date_obj'], entry['time_period'])
        }
        
        # ファイル名を生成
        filename = create_filename(entry['date_obj'], entry['time_period'])
        filepath = os.path.join(output_dir, filename)
        
        # JSONファイルを書き込み
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        created_files.append(filename)
        print(f"Created: {filename}")
    
    return created_files

if __name__ == '__main__':
    # 健康記録ファイルをパース
    print("Parsing 健康記録.2025.md...")
    entries = parse_health_record('/home/yattom/work/health-recorder-ai/健康記録.2025.md')
    print(f"Found {len(entries)} entries")
    
    # 最初の5エントリをテスト変換
    print("\nConverting first 5 entries for testing...")
    created_files = convert_to_json_files(
        entries, 
        '/home/yattom/work/health-recorder-ai/data', 
        start_idx=0, 
        end_idx=5
    )
    
    print(f"\nCreated {len(created_files)} files:")
    for filename in created_files:
        print(f"  - {filename}")