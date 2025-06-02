from openai import OpenAI
import datetime
from typing import Dict, Any
import utils

def classify_email(email_data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    使用LLM对邮件进行分类
    """
    # 设置OpenAI API密钥
    DEEPSEEK_API_KEY = config['openai']['api_key']

    # 创建分类提示
    prompt = f"""
    请对以下邮件进行分类，只返回分类结果（code, question 或 spam）：

    分类规则：
    1. 如果邮件包含可执行的Python代码 -> code
    2. 如果邮件包含需要回答的问题 -> question
    3. 如果是广告或营销邮件 -> spam

    邮件主题: {email_data['subject']}
    发件人: {email_data['from']}
    邮件内容:
    {email_data['body'][:500]}{'...' if len(email_data['body']) > 500 else ''}

    只返回分类结果单词，不要任何其他文本。
    """

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.siliconflow.cn")
    model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个邮件分类助手，只返回分类结果单词。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            stream=False
        )
        classification = response.choices[0].message.content.strip().lower()

        # 确保返回有效的分类
        if classification not in ['code', 'question', 'spam']:
            return "spam"  # 默认为垃圾邮件

        return classification

    except Exception as e:
        print(f"邮件分类失败: {str(e)}")
        return "spam"  # 出错时默认为垃圾邮件


def process_code_email(email_data: Dict[str, Any], config: Dict[str, Any], logger: Any) -> str:
    """
    处理包含代码的邮件
    """
    # 提取代码
    code = utils.extract_python_code(email_data['body'])

    if not code:
        return "未找到有效的Python代码"

    logger.info(f"提取到代码:\n{code}")

    # 安全执行代码并捕获输出
    result = utils.execute_code(code, logger)

    # 创建响应内容
    response = f"""
    您的代码执行结果：

    ```
    {result}
    ```

    原始代码：
    ```python
    {code}
    ```

    ---
    此邮件由自动邮件处理Agent生成
    处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """

    return response

def answer_question_email(email_data: Dict[str, Any], config: Dict[str, Any], logger: Any) -> str:
    """
    回答邮件中的问题
    """
    # 设置OpenAI API密钥
    DEEPSEEK_API_KEY = config['openai']['api_key']

    # 创建问题回答提示
    prompt = f"""
    你是一个邮件处理助手，需要回答以下邮件中的问题：

    邮件主题: {email_data['subject']}
    发件人: {email_data['from']}
    邮件内容:
    {email_data['body']}

    请用友好、专业的语气回复邮件中的问题。
    """
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.siliconflow.cn")
    model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的邮件助手，需要回答用户的问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            stream=False
        )

        answer = response.choices[0].message.content.strip()

        # 添加签名
        answer += f"\n\n---\n此邮件由自动邮件处理Agent生成\n处理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        return answer

    except Exception as e:
        logger.error(f"问题回答失败: {str(e)}")
        return f"抱歉，处理您的邮件时出错: {str(e)}"


def handle_spam_email(email_data: Dict[str, Any], logger: Any) -> str:
    """
    处理垃圾邮件
    """
    logger.info(f"检测到垃圾邮件: {email_data['subject']}")
    return "已忽略垃圾邮件"


def log_processing_result(logger: Any, email_data: Dict[str, Any],
                          classification: str, result: str) -> None:
    """
    记录处理结果
    """
    log_entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'email_id': email_data['id'].decode() if isinstance(email_data['id'], bytes) else email_data['id'],
        'subject': email_data['subject'],
        'from': email_data['from'],
        'classification': classification,
        'result': result[:100] + '...' if len(result) > 100 else result
    }

    logger.info(f"邮件处理结果: {log_entry}")