"""
数据模型定义
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GroupInfo:
    """群信息数据类"""
    group_id: str
    group_type: str  # 专群/公群/飞博
    owner_name: str
    status: str  # active/closed/suspended
    deposit_amount: float
    created_at: str
    id: Optional[int] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_row(cls, row: tuple) -> "GroupInfo":
        """从数据库行创建实例"""
        return cls(
            id=row[0],
            group_id=row[1],
            group_type=row[2],
            owner_name=row[3],
            status=row[4],
            deposit_amount=row[5],
            created_at=row[6],
            updated_at=row[7] if len(row) > 7 else None,
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "owner_name": self.owner_name,
            "status": self.status,
            "deposit_amount": self.deposit_amount,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

