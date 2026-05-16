import sys
import os

path = os.path.expanduser('~/AMPM_Brain/src/tools.py')
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到出錯的那一段並替換成正確的格式
start_line = -1
for i, line in enumerate(lines):
    if '"system_stats"' in line and 'description' in lines[i+1]:
        start_line = i
        break

if start_line != -1:
    new_tool = [
        '        self.registry["system_stats"] = {\n',
        '            "description": "查詢系統硬碟和記憶體使用狀況",\n',
        '            "type": "builtin",\n',
        '            "code": "def execute(): import subprocess; disk = subprocess.run([\'df\', \'-h\'], capture_output=True, text=True).stdout; mem = subprocess.run([\'free\', \'-h\'], capture_output=True, text=True).stdout; return f\'硬碟:\\n{disk}\\n記憶體:\\n{mem}\'",\n',
        '            "created_at": __import__("datetime").datetime.now().isoformat(),\n',
        '            "last_used": None,\n',
        '            "use_count": 0\n',
        '        }\n'
    ]
    # 替換掉舊的錯誤區塊（約 91 到 99 行）
    lines[start_line:start_line+8] = new_tool

    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ tools.py 的零件引號已修復！")
else:
    print("❌ 找不到需要修復的區塊，請確認檔案內容。")
