# 2026 分数组合计算器

一个用于查找三人分数之和等于 2026 的 Web 应用。支持多人同时访问，自动匹配并锁定组合。

## 功能特性

- **添加参与者**：输入姓名和分数，自动保存
- **自动匹配**：每次添加新人时，自动检测是否能与已有用户组成和为 2026 的三人组合
- **锁定机制**：一旦找到组合，三人锁定，不再参与后续匹配
- **查询状态**：输入姓名查询匹配状态，已匹配则显示组合详情
- **实时统计**：显示总人数、等待配对人数、已找到组合数
- **并发支持**：使用数据库锁保证数据一致性，支持上百人同时访问

## 技术栈

- **后端**：Python + FastAPI
- **前端**：原生 HTML/CSS/JavaScript
- **数据库**：SQLite

## 快速开始

### 环境要求

- Python 3.8+（推荐 3.9+）

### 本地运行

```bash
# 克隆项目
git clone https://github.com/08163356/AlipaySum2026.git
cd AlipaySum2026

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app:app --host 0.0.0.0 --port 8026
```

访问 http://localhost:8026 即可使用。

### 服务器部署

```bash
# 克隆项目
git clone -b dev https://github.com/08163356/AlipaySum2026.git
cd AlipaySum2026

# 创建虚拟环境并安装依赖
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 使用服务脚本管理
chmod +x service.sh
./service.sh start
```

### 服务管理命令

```bash
./service.sh start    # 启动服务
./service.sh stop     # 停止服务
./service.sh restart  # 重启服务
./service.sh status   # 查看状态
./service.sh logs     # 查看实时日志
```

### 生产环境（多 Worker）

```bash
./venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8026 --workers 4
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页 |
| POST | `/api/users` | 添加用户 `{"name": "张三", "score": 600}` |
| GET | `/api/users` | 获取所有用户列表 |
| GET | `/api/combinations` | 获取所有 2026 组合 |
| GET | `/api/stats` | 获取统计信息 |
| GET | `/api/search?name=xxx` | 查询用户匹配状态 |

## 错误排查

### 1. `No module named uvicorn`

**原因**：依赖未安装或未激活虚拟环境

**解决**：
```bash
# 确保激活虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### 2. `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`

**原因**：Python 版本低于 3.10

**解决**：升级到 Python 3.9+ 或使用已兼容的代码版本

### 3. 端口被占用 `[Errno 10048]` 或 `Address already in use`

**原因**：8026 端口已被其他程序占用

**解决**：
```bash
# 查找占用端口的进程
netstat -tlnp | grep 8026

# 杀掉进程或换一个端口
python -m uvicorn app:app --host 0.0.0.0 --port 8027
```

### 4. 外网无法访问

**排查步骤**：

1. 确认服务正在运行：
```bash
curl http://127.0.0.1:8026/api/stats
```

2. 检查防火墙：
```bash
# 查看防火墙状态
sudo firewall-cmd --state

# 开放端口
sudo firewall-cmd --zone=public --add-port=8026/tcp --permanent
sudo firewall-cmd --reload
```

3. 检查 iptables：
```bash
sudo iptables -I INPUT -p tcp --dport 8026 -j ACCEPT
```

4. 云服务器需在控制台**安全组**添加 8026 端口入站规则

### 5. `pip install` 失败或速度慢

**解决**：使用国内镜像
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6. 服务启动后立即退出

**排查**：查看日志
```bash
cat app.log
```

常见原因：
- Python 版本不兼容
- 依赖未完全安装
- 端口冲突

## 数据说明

- 数据存储在 `data.db`（SQLite 数据库）
- 数据库包含两张表：
  - `users`：用户信息（姓名、分数、是否锁定）
  - `combinations`：已找到的 2026 组合

### 清空数据

```bash
rm data.db
./service.sh restart
```

## 目录结构

```
AlipaySum2026/
├── app.py              # 后端服务
├── requirements.txt    # Python 依赖
├── service.sh          # 服务管理脚本
├── static/
│   └── index.html      # 前端页面
├── data.db             # 数据库（运行后生成）
├── app.log             # 运行日志（运行后生成）
└── README.md           # 说明文档
```

## License

MIT
