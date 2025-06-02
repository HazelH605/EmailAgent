import configparser
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """
    从配置文件加载配置信息
    """
    config = configparser.ConfigParser()
    config.read('config.ini')  # 读取配置文件

    # 创建配置字典
    config_data = {
        'email': {
            'user': config.get('EMAIL', 'User'),
            'password': config.get('EMAIL', 'Password'),
            'imap_server': config.get('EMAIL', 'IMAP_Server')
        },
        'openai': {
            'api_key': config.get('OPENAI', 'API_KEY')
        },
        'logging': {
            'dir': config.get('LOGGING', 'Dir', fallback='logs')
        },
        'processing': {
            'max_emails': int(config.get('PROCESSING', 'MaxEmails', fallback='3'))
        }
    }

    return config_data


def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置是否完整
    """
    errors = []

    if not config['email']['user']:
        errors.append("必须提供邮箱账号")
    if not config['email']['password']:
        errors.append("必须提供邮箱密码/授权码")
    if not config['openai']['api_key']:
        errors.append("必须提供OpenAI API密钥")

    if errors:
        print("配置错误:")
        for error in errors:
            print(f"- {error}")
        print("\n请创建config.ini文件并包含以下内容:")
        print("""
[EMAIL]
User = your@email.com
Password = your_password
IMAP_Server = imap.example.com

[OPENAI]
API_KEY = your_api_key

[LOGGING]
Dir = logs

[PROCESSING]
MaxEmails = 3
        """)
        return False

    return True