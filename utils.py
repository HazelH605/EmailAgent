import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
import datetime
import os
import logging
import re
from typing import Dict, Any
import io
import contextlib

def setup_logging(log_dir: str) -> logging.Logger:
    """
    设置日志记录 - 修复编码问题
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"mail_agent_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logger = logging.getLogger("MailAgent")
    logger.setLevel(logging.INFO)

    # 创建文件处理器 - 使用UTF-8编码
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # 创建控制台处理器 - 使用UTF-8编码
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 创建格式化器并添加到处理器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def fetch_unread_emails(config: Dict[str, Any], logger: logging.Logger) -> tuple:
    """
    获取未读邮件
    """
    try:
        imap = imaplib.IMAP4_SSL(config['email']['imap_server'], 993)
        imap.login(config['email']['user'], config['email']['password'])
        status, message = imap.select("INBOX")
        if status != "OK":
            logger.error("搜索未读邮件失败")
            return imap, []
        status, msgnums = imap.search(None, 'UNSEEN')

        email_list = []
        msgnums = msgnums[0].split()

        logger.info(f"找到 {len(msgnums)} 封未读邮件")

        for msgnum in msgnums[:config['processing']['max_emails']]:
            try:
                status, data = imap.fetch(msgnum, "(RFC822)")
                if status != "OK":
                    logger.error(f"获取邮件 {msgnum} 失败")
                    continue

                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                # 解码主题
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")

                # 获取发件人
                from_header = msg["From"]

                # 提取邮件正文
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        # 只处理纯文本正文
                        if "attachment" not in content_disposition and content_type == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                email_data = {
                    'id': msgnum,
                    'subject': subject,
                    'from': from_header,
                    'body': body
                }

                email_list.append(email_data)
                logger.info(f"获取邮件: {subject}")

            except Exception as e:
                logger.error(f"处理邮件 {msgnum} 时出错: {str(e)}")

        return imap, email_list

    except Exception as e:
        logger.error(f"连接邮箱失败: {str(e)}")
        return None, []


def send_reply(config: Dict[str, Any], to: str, subject: str, content: str, logger: logging.Logger) -> bool:
    """
    发送回复邮件
    """
    try:
        # 设置邮件内容
        msg = MIMEText(content)
        msg["Subject"] = f"Re: {subject}"
        msg["From"] = config['email']['user']
        msg["To"] = to

        # 发送邮件
        with smtplib.SMTP_SSL(config['email']['imap_server'].replace("imap", "smtp"), 465) as server:
            server.login(config['email']['user'], config['email']['password'])
            server.send_message(msg)

        logger.info(f"已发送回复给: {to}")
        return True

    except Exception as e:
        logger.error(f"发送回复失败: {str(e)}")
        return False


def extract_python_code(text: str) -> str:
    """
    从文本中提取Python代码块
    """
    # 尝试匹配代码块
    code_blocks = re.findall(r'```python(.*?)```', text, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()

    # 如果没有找到代码块，尝试匹配以import开头的代码
    code_lines = []
    in_code = False

    for line in text.split('\n'):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            in_code = True
        elif in_code and line.strip() == '':
            break

        if in_code:
            code_lines.append(line)

    return '\n'.join(code_lines).strip()


def execute_code(code: str, logger: logging.Logger) -> str:
    """
    执行Python代码并捕获输出
    """
    try:
        # 创建缓冲区捕获输出
        output_buffer = io.StringIO()

        # 重定向标准输出和错误
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            # 执行代码
            exec(code, globals(), {})

        # 获取捕获的输出
        output = output_buffer.getvalue()

        return output if output else "代码执行成功，但未产生输出"

    except Exception as e:
        logger.error(f"代码执行失败: {str(e)}")
        return f"错误: {str(e)}"

def mark_email_as_read(imap, email_id: bytes, logger: logging.Logger) -> None:
    """
    将邮件标记为已读
    """
    try:
        imap.store(email_id, '+FLAGS', '\\Seen')
        logger.info(f"邮件 {email_id.decode()} 已标记为已读")
    except Exception as e:
        logger.error(f"标记邮件为已读失败: {str(e)}")


def close_imap_connection(imap, logger: logging.Logger) -> None:
    """
    关闭IMAP连接
    """
    try:
        imap.close()
        imap.logout()
        logger.info("IMAP连接已关闭")
    except Exception as e:
        logger.error(f"关闭IMAP连接失败: {str(e)}")