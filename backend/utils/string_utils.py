'''
Author: ai-business-hql qingli.hql@alibaba-inc.com
Date: 2025-08-08 17:14:52
LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
LastEditTime: 2025-08-11 19:13:12
FilePath: /comfyui_copilot/backend/utils/string_utils.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
def error_format(e: Exception) -> str:
    error_message = str(e).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # 移除可能导致JSON解析错误的控制字符
    error_message = ''.join(char for char in error_message if ord(char) >= 32 or char in '\n\r\t')
    return error_message