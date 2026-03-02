# Agent Puncher

Agent Puncher 是一个功能强大的 LLM 网关工具，用于捕获、处理和记录 LLM API 请求，提供了完整的请求转发、日志记录和 Web 界面功能。通过Agent Puncher, 用户可以实时查看 agent 的交互过程，以便更深入理解 agent 的工作原理。

## 功能特点

- 🚀 **请求转发**：将请求转发到外部 LLM API（如 OpenAI 等）
- 📊 **详细日志**：记录所有请求和响应，包括提示词、响应内容、令牌使用情况等
- 🔄 **流式响应**：支持流式响应处理，实时返回生成结果
- 🖥️ **Web 界面**：内置简洁的 Web 界面，方便查看和管理
- ⚙️ **配置管理**：支持通过 API 或配置文件管理 LLM API 设置
- 📱 **跨域支持**：内置 CORS 中间件，支持跨域请求

## 技术栈

- **后端**：Python 3.10+, FastAPI
- **数据库**：SQLite
- **前端**：HTML, CSS, JavaScript
- **依赖**：aiohttp, uvicorn

## 安装和使用

### 1. 克隆项目

```bash
git clone git@github.com:bokuan/agent-puncher.git
cd agent-puncher
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 设置

你可以通过以下两种方式配置 LLM API 信息：

#### 方式一：编辑配置文件

编辑 `config.json` 文件，设置你的 LLM API 信息：

```json
{
  "external_api_base_url": "https://api.openai.com/v1",
  "external_api_key": "your-api-key-here",
  "web_model": "gpt-3.5-turbo"
}
```

#### 方式二：通过 Web 界面设置

在web页面直接设置 API 信息，包括 API 基础 URL、API 密钥和默认模型。

### 4. 启动服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:5685` 启动。

## API 调用

- **POST http://127.0.0.1:5685/v1/chat/completions**
  - 兼容 OpenAI API 格式的聊天补全端点
  - 支持流式和非流式响应
  - 自动记录所有请求和响应，包括请求和相应的元数据

## Web 界面

访问 `http://127.0.0.1:5685/web/` 查看内置的 Web 界面，可用于：
- 发送聊天请求
- 查看历史记录
- 管理配置

## 日志记录

系统会记录以下信息：
- 时间戳
- 提示词内容
- 响应内容
- 令牌使用情况
- 外部 API URL
- 请求头信息
- 请求体信息

日志存储在 SQLite 数据库 `llm_gateway.db` 中。


## 项目结构

```
agent-puncher/
├── web/           # 前端代码
│   ├── app.js          # 前端应用逻辑
│   ├── index.html      # 前端界面
│   └── style.css       # 前端样式
├── __pycache__/        # Python 编译缓存
├── .env                # 环境变量文件
├── .gitignore          # Git 忽略文件
├── config.json         # 配置文件
├── config.py           # 配置管理模块
├── database.py         # 数据库操作模块
├── llm_gateway.db      # SQLite 数据库文件
├── main.py             # 主应用入口
├── README.md           # 英文说明文档
├── README_zh-CN.md     # 中文说明文档
└── requirements.txt    # 依赖文件
```

## 注意事项

1. 请妥善保管你的 API 密钥，不要将其提交到版本控制系统
2. 项目默认使用 SQLite 数据库，适用于开发和小规模使用
3. 对于生产环境，建议使用更强大的数据库系统
4. 如需修改端口或主机，请编辑 `main.py` 文件中的 `uvicorn.run` 配置

## 贡献

欢迎提交问题和 Pull Request！

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
