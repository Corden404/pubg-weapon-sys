# 绝地求生武器管理与声纹识别系统 (PUBG Weapon System)

这是一个基于 Python 和 Next.js 的全栈课程项目，集成了武器数据管理、用户背包系统以及基于机器学习的枪声识别功能。项目采用前后端分离架构，结合了现代 Web 技术与 AI 模型。

## 🌟 项目亮点

*   **双重 AI 识别架构**：结合云端大模型 (Hugging Face) 和本地机器学习模型 (Random Forest) 进行音频分析，提高识别准确率。
*   **现代化前端界面**：使用 Next.js + Tailwind CSS + Shadcn UI 构建，提供流畅的用户体验和响应式设计。
*   **实时数据交互**：基于 FastAPI 和 MongoDB 构建的高性能后端，支持实时库存更新和数据查询。
*   **可视化仪表盘**：直观展示用户背包状态、弹药统计和武器分布。

## 🛠️ 技术栈

### 后端 (Backend)
*   **框架**: FastAPI (Python)
*   **数据库**: MongoDB (Pymongo)
*   **AI/ML**: 
    *   `Librosa`: 音频特征提取 (MFCC)
    *   `Scikit-learn`: 本地随机森林模型
    *   `Gradio Client`: 调用 Hugging Face 云端模型
*   **工具**: Uvicorn, Pydantic

### 前端 (Frontend)
*   **框架**: Next.js 15 (React)
*   **样式**: Tailwind CSS
*   **组件库**: Shadcn UI, Lucide React
*   **图表**: Recharts
*   **语言**: TypeScript

## 📂 项目结构

```
pubg-weapon-sys/
├── backend/                # FastAPI 后端代码
│   └── main.py            # API 入口文件
├── frontend/               # Next.js 前端项目
│   ├── app/               # 页面路由 (App Router)
│   ├── components/        # UI 组件
│   └── public/            # 静态资源
├── logic/                  # AI 核心逻辑
│   └── ai_core.py         # 模型加载与推理逻辑
├── data/                   # 数据与模型文件
│   └── processed/         # 训练好的模型 (.pkl) 和特征数据
├── scripts/                # 实用脚本
│   ├── create_demo_user.py # 创建测试用户
│   └── init_db.py         # 数据库初始化
├── utils/                  # 通用工具
│   └── database.py        # 数据库连接配置
└── requirements.txt        # Python 依赖列表
```

## 🚀 快速开始

### 1. 环境准备
确保你的开发环境已安装：
*   Python 3.8+
*   Node.js 18+
*   MongoDB (可以使用 MongoDB Atlas 云数据库)

### 2. 后端设置

1.  **安装 Python 依赖**
    ```bash
    pip install -r requirements.txt
    ```

2.  **配置数据库**
    *   在环境变量中设置 `MONGO_URI`，或者在 `.streamlit/secrets.toml` 中配置。
    *   或者直接修改 `utils/database.py` (仅限开发环境)。

3.  **初始化数据 (可选)**
    创建一个测试用户 (账号: `demo`, 密码: `demo`)：
    ```bash
    python scripts/create_demo_user.py
    ```

4.  **启动后端服务**
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```
    后端将在 `http://localhost:8000` 启动。

### 3. 前端设置

1.  **进入前端目录**
    ```bash
    cd frontend
    ```

2.  **安装依赖**
    ```bash
    npm install
    ```

3.  **启动开发服务器**
    ```bash
    npm run dev
    ```
    前端将在 `http://localhost:3000` 启动。

## 📖 功能使用指南

### 1. 登录系统
*   访问 `http://localhost:3000`。
*   使用测试账号登录：
    *   **学号**: `demo`
    *   **密码**: `demo`

### 2. 仪表盘 (Dashboard)
*   登录后进入仪表盘，查看当前的背包概览。
*   可以看到总弹药数、武器数量以及最近获取的物品。

### 3. 武器图鉴 (Catalog)
*   点击侧边栏的 "武器图鉴"。
*   浏览所有可用的 PUBG 武器。
*   点击任意武器卡片，输入弹药数量，点击 "确认添加" 将其加入背包。

### 4. 声纹分析 (Analyze) - AI 核心功能
*   点击侧边栏的 "声纹分析"。
*   上传一段枪声的音频文件 (.mp3 或 .wav)。
*   点击 "开始分析"。
*   系统将展示：
    *   **云端模型结果**: 基于 Hugging Face 的深度学习模型预测。
    *   **本地模型结果**: 基于随机森林 (Random Forest) 的预测。
    *   **置信度**: AI 对预测结果的确信程度。

## 🤝 贡献与开发
欢迎提交 Issue 或 Pull Request 来改进本项目。

1.  Fork 本仓库
2.  创建特性分支 (`git checkout -b feature/AmazingFeature`)
3.  提交更改 (`git commit -m 'Add some AmazingFeature'`)
4.  推送到分支 (`git push origin feature/AmazingFeature`)
5.  提交 Pull Request

## 📄 许可证
本项目采用 MIT 许可证。
