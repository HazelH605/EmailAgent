## 项目概述
这是一个基于 LangGraph 的邮件处理 Agent，能够自动处理邮箱中的未读邮件。系统通过智能分类将邮件分为三类（代码执行类、问题查询类、广告营销类），并针对不同类别执行相应操作（执行代码/回答问题/忽略垃圾邮件），最后通过邮件回复处理结果。

## 项目架构
```
📂 Mail-Agent/
├── config.py        # 配置管理模块
├── graph.py         # LangGraph 工作流定义
├── main.py          # 主程序入口
├── nodes.py         # 功能节点实现
├── utils.py         # 实用工具函数
└── requirements.txt # 项目依赖
```

## 文件功能说明

### 1. config.py
- **功能**：配置文件的加载与验证
- 从 `config.ini` 读取邮箱和 API 配置
- 验证必要配置项是否完整
- 提供配置错误时的提示信息

### 2. graph.py
- **核心**：LangGraph 状态机定义
- 定义 Agent 状态结构 `AgentState`
- 构建邮件处理工作流：
  ```
  分类 → 条件路由 → 处理节点 → 日志 → 回复 → 结束
  ```
- 实现 6 个功能节点和条件路由逻辑

### 3. main.py
- **程序入口**：系统主流程控制
- 加载配置并验证
- 初始化日志系统
- 创建工作流并生成可视化图
- 获取/处理未读邮件
- 状态机执行与异常处理

### 4. nodes.py
- **功能实现**：各节点的具体业务逻辑
- `classify_email`：使用 LLM 进行邮件分类
- `process_code_email`：提取并执行 Python 代码
- `answer_question_email`：使用 LLM 回答问题
- `handle_spam_email`：处理垃圾邮件
- `log_processing_result`：记录处理日志

### 5. utils.py
- **工具集**：辅助功能实现
- `setup_logging`：配置日志系统
- `fetch_unread_emails`：获取未读邮件
- `send_reply`：发送回复邮件
- `extract_python_code`：从文本提取 Python 代码
- `execute_code`：安全执行代码
- `mark_email_as_read`：标记邮件为已读

### 6. requirements.txt
- 项目依赖库列表
- 主要依赖：LangGraph, OpenAI, 邮件处理库


## 使用说明

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **创建配置文件**：
   在项目根目录创建 `config.ini`，内容如下：
   ```ini
   [EMAIL]
   User = your@email.com
   Password = your_password_or_auth_code
   IMAP_Server = imap.example.com
   
   [OPENAI]
   API_KEY = your_api_key
   
   [LOGGING]
   Dir = logs
   
   [PROCESSING]
   MaxEmails = 5
   ```

3. **运行程序**：
   ```bash
   python main.py
   ```

## 注意事项

1. **邮箱配置**：
   - 使用 IMAP 协议访问邮箱
   - 密码需使用邮箱服务商提供的授权码（非登录密码）
   - 确保邮箱服务商允许未知第三方的访问（例如163就会被拦截）

2. **API 密钥**：
   - 项目使用 DeepSeek-R1 模型（硅流平台）
   - 替换为自己在https://siliconflow.cn/上获取的API key

3. **安全限制**：
   - 代码执行在沙盒环境中进行
   - 默认限制最大处理邮件数（MaxEmails）

4. **日志系统**：
   - 日志存储在 `logs/` 目录
   - 包含时间戳、邮件ID、分类结果等关键信息
   - 每日生成独立日志文件


> **注意**：执行未知来源代码存在安全风险。
