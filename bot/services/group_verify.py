"""
群验证服务
用于自助验群功能
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GroupInfo:
    """群信息数据类"""
    group_id: str
    group_type: str  # 专群/公群/飞博
    owner_name: str
    status: str  # active/closed/suspended
    deposit_amount: float
    created_at: str


class GroupVerifyService:
    """
    群验证服务

    支持从 SQLite 数据库查询群信息
    如果数据库不可用，使用模拟数据作为后备
    """

    # 是否使用数据库查询
    _use_database: bool = True

    # 模拟群数据 (作为后备方案)
    _mock_groups: Dict[str, GroupInfo] = {
        "专群A12345": GroupInfo(
            group_id="专群A12345",
            group_type="专群",
            owner_name="张老板",
            status="active",
            deposit_amount=5000.0,
            created_at="2024-01-15"
        ),
        "公群12345": GroupInfo(
            group_id="公群12345",
            group_type="公群",
            owner_name="李老板",
            status="active",
            deposit_amount=15000.0,
            created_at="2024-02-20"
        ),
        "飞博13": GroupInfo(
            group_id="飞博13",
            group_type="飞博",
            owner_name="王老板",
            status="active",
            deposit_amount=20000.0,
            created_at="2024-03-10"
        ),
    }

    @classmethod
    def set_use_database(cls, use_db: bool) -> None:
        """设置是否使用数据库"""
        cls._use_database = use_db

    @classmethod
    def parse_group_id(cls, text: str) -> Optional[str]:
        """
        解析用户输入的群编号
        
        支持格式:
        - 专群A12345
        - 公群12345
        - 飞博13
        """
        text = text.strip()
        
        # 匹配群编号格式
        patterns = [
            r"^(专群[A-Za-z]?\d+)$",
            r"^(公群\d+)$",
            r"^(飞博\d+)$",
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @classmethod
    def verify_group(cls, group_id: str) -> Optional[GroupInfo]:
        """
        验证群编号

        优先从数据库查询，如果数据库不可用则使用模拟数据

        Returns:
            GroupInfo 或 None
        """
        if cls._use_database:
            try:
                from ..database import get_db
                db = get_db()
                db_group = db.get_group_by_id(group_id)
                if db_group:
                    # 将数据库模型转换为本地 GroupInfo
                    return GroupInfo(
                        group_id=db_group.group_id,
                        group_type=db_group.group_type,
                        owner_name=db_group.owner_name,
                        status=db_group.status,
                        deposit_amount=db_group.deposit_amount,
                        created_at=db_group.created_at,
                    )
                return None
            except Exception as e:
                # 数据库查询失败，回退到模拟数据
                print(f"[GroupVerify] 数据库查询失败，使用模拟数据: {e}")
                return cls._mock_groups.get(group_id)

        # 使用模拟数据
        return cls._mock_groups.get(group_id)
    
    @classmethod
    def format_verify_result(cls, group_id: str) -> str:
        """格式化验证结果消息"""
        group_info = cls.verify_group(group_id)
        
        if group_info is None:
            return f"❌ 未找到群编号: {group_id}\n\n请确认群编号是否正确，格式示例:\n• 专群A12345\n• 公群12345\n• 飞博13"
        
        status_emoji = "✅" if group_info.status == "active" else "⚠️"
        status_text = {
            "active": "正常运营",
            "closed": "已关闭",
            "suspended": "暂停中"
        }.get(group_info.status, "未知")
        
        return f"""✅ 群验证结果

📋 群编号: {group_info.group_id}
📂 类型: {group_info.group_type}
👤 负责人: {group_info.owner_name}
{status_emoji} 状态: {status_text}
💰 押金: {group_info.deposit_amount}U
📅 创建时间: {group_info.created_at}

如有疑问请联系客服"""

