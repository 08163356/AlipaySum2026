"""
2026 分数组合计算器
- 输入姓名和分数
- 自动查找三人分数和等于2026的组合
- 找到的组合锁定，不再参与后续计算
"""
from __future__ import annotations
from typing import Optional, List, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import sqlite3
import threading
from pathlib import Path

# 数据库锁，处理并发写入
db_lock = threading.Lock()
DB_PATH = Path(__file__).parent / "data.db"


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 用户表：存储姓名、分数、是否已锁定
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            score INTEGER NOT NULL,
            locked INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 组合表：存储找到的2026组合
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            user3_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users(id),
            FOREIGN KEY (user2_id) REFERENCES users(id),
            FOREIGN KEY (user3_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    init_db()
    yield


app = FastAPI(title="2026组合计算器", lifespan=lifespan)

# 挂载静态文件
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


class UserInput(BaseModel):
    name: str
    score: int


class UserResponse(BaseModel):
    id: int
    name: str
    score: int
    locked: bool


class CombinationResponse(BaseModel):
    id: int
    users: List[UserResponse]
    total: int


def find_combination_for_new_user(conn, new_user_id: int, new_score: int) -> Optional[Tuple[int, int]]:
    """
    为新用户查找是否存在两个未锁定用户，三人分数和为2026
    返回 (user1_id, user2_id) 或 None
    """
    cursor = conn.cursor()
    
    # 查找所有未锁定的用户（排除新用户自己）
    cursor.execute("""
        SELECT id, score FROM users 
        WHERE locked = 0 AND id != ?
        ORDER BY id
    """, (new_user_id,))
    
    unlocked_users = cursor.fetchall()
    
    # 需要找到两个用户，使得 new_score + score1 + score2 = 2026
    target = 2026 - new_score
    
    # 使用双指针或哈希表查找
    score_map = {row['score']: row['id'] for row in unlocked_users}
    
    for i, user1 in enumerate(unlocked_users):
        needed = target - user1['score']
        # 在剩余用户中查找
        for user2 in unlocked_users[i+1:]:
            if user2['score'] == needed:
                return (user1['id'], user2['id'])
    
    return None


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回主页"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>请确保 static/index.html 存在</h1>"


@app.post("/api/users", response_model=dict)
async def add_user(user: UserInput):
    """添加新用户并检查是否形成2026组合"""
    if not user.name.strip():
        raise HTTPException(status_code=400, detail="姓名不能为空")
    
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # 插入新用户
            cursor.execute(
                "INSERT INTO users (name, score) VALUES (?, ?)",
                (user.name.strip(), user.score)
            )
            new_user_id = cursor.lastrowid
            conn.commit()
            
            # 查找是否能形成2026组合
            combination = find_combination_for_new_user(conn, new_user_id, user.score)
            
            new_combination = None
            if combination:
                user1_id, user2_id = combination
                
                # 锁定三个用户
                cursor.execute(
                    "UPDATE users SET locked = 1 WHERE id IN (?, ?, ?)",
                    (new_user_id, user1_id, user2_id)
                )
                
                # 记录组合
                cursor.execute(
                    "INSERT INTO combinations (user1_id, user2_id, user3_id) VALUES (?, ?, ?)",
                    (user1_id, user2_id, new_user_id)
                )
                conn.commit()
                
                # 获取组合详情
                cursor.execute(
                    "SELECT id, name, score, locked FROM users WHERE id IN (?, ?, ?)",
                    (user1_id, user2_id, new_user_id)
                )
                users = [dict(row) for row in cursor.fetchall()]
                new_combination = {
                    "users": users,
                    "total": sum(u['score'] for u in users)
                }
            
            return {
                "success": True,
                "user": {
                    "id": new_user_id,
                    "name": user.name.strip(),
                    "score": user.score,
                    "locked": combination is not None
                },
                "new_combination": new_combination
            }
            
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            conn.close()


@app.get("/api/users", response_model=list)
async def get_users():
    """获取所有用户"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, score, locked FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


@app.get("/api/combinations", response_model=list)
async def get_combinations():
    """获取所有2026组合"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.user1_id, c.user2_id, c.user3_id
        FROM combinations c
        ORDER BY c.created_at DESC
    """)
    
    combinations = []
    for row in cursor.fetchall():
        cursor.execute(
            "SELECT id, name, score, locked FROM users WHERE id IN (?, ?, ?)",
            (row['user1_id'], row['user2_id'], row['user3_id'])
        )
        users = [dict(u) for u in cursor.fetchall()]
        combinations.append({
            "id": row['id'],
            "users": users,
            "total": sum(u['score'] for u in users)
        })
    
    conn.close()
    return combinations


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as locked FROM users WHERE locked = 1")
    locked_users = cursor.fetchone()['locked']
    
    cursor.execute("SELECT COUNT(*) as total FROM combinations")
    total_combinations = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "total_users": total_users,
        "locked_users": locked_users,
        "unlocked_users": total_users - locked_users,
        "total_combinations": total_combinations
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
