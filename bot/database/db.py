"""
SQLite 数据库管理
"""

import os
import sqlite3
from typing import Optional, List
from contextlib import contextmanager

from .models import GroupInfo


class Database:
    """SQLite 数据库管理类"""
    
    def __init__(self, db_path: str = "bot_data.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    @property
    def connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标上下文管理器"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def init_tables(self) -> None:
        """初始化数据库表"""
        with self.get_cursor() as cursor:
            # 创建群信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT UNIQUE NOT NULL,
                    group_type TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    deposit_amount REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            
            # 创建索引
            # 注意: group_id 字段的 UNIQUE 约束已自动创建唯一索引，无需额外创建
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_groups_status
                ON groups(status)
            """)
    
    def get_group_by_id(self, group_id: str) -> Optional[GroupInfo]:
        """
        根据群编号查询群信息
        
        Args:
            group_id: 群编号 (如 专群A12345)
            
        Returns:
            GroupInfo 或 None
        """
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM groups WHERE group_id = ?",
                (group_id,)
            )
            row = cursor.fetchone()
            if row:
                return GroupInfo.from_row(tuple(row))
            return None
    
    def insert_group(self, group: GroupInfo) -> int:
        """
        插入群信息
        
        Returns:
            插入的记录 ID
        """
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO groups (group_id, group_type, owner_name, status, deposit_amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                group.group_id,
                group.group_type,
                group.owner_name,
                group.status,
                group.deposit_amount,
                group.created_at,
                group.updated_at,
            ))
            return cursor.lastrowid
    
    def update_group(self, group: GroupInfo) -> bool:
        """更新群信息"""
        from datetime import datetime
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE groups 
                SET group_type = ?, owner_name = ?, status = ?, 
                    deposit_amount = ?, updated_at = ?
                WHERE group_id = ?
            """, (
                group.group_type,
                group.owner_name,
                group.status,
                group.deposit_amount,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                group.group_id,
            ))
            return cursor.rowcount > 0
    
    def get_all_groups(self) -> List[GroupInfo]:
        """获取所有群信息"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM groups ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [GroupInfo.from_row(tuple(row)) for row in rows]
    
    def count_groups(self) -> int:
        """统计群数量"""
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM groups")
            return cursor.fetchone()[0]


# 全局数据库实例
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        from ..config import config
        db_path = os.getenv("SQLITE_PATH", "bot_data.db")
        _db_instance = Database(db_path)
        _db_instance.init_tables()
    return _db_instance

