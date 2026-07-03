
# -*- coding: utf-8 -*-
import os

doc_path = r'D:\桌面\desktop\code\knowOcean-python\docs\面试题\高频追问.md'
tmp = os.environ['TEMP']

# Read existing content
with open(doc_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Sections to append
new_parts = []
new_parts.append('')

# Section 14 header
new_parts.append('## 十四、Java 核心原理（4 题)')
new_parts.append('')
