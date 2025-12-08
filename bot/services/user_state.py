"""
用户状态管理服务
用于跟踪用户当前的操作状态
"""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime, timedelta


class UserState(Enum):
    """用户状态枚举"""
    IDLE = "idle"  # 空闲状态
    
    # 等待上押截图状态
    WAITING_DEPOSIT_LA_ZHUAN = "waiting_deposit_la_zhuan"  # 拉专群
    WAITING_DEPOSIT_KAI_GONG = "waiting_deposit_kai_gong"  # 开公群
    WAITING_DEPOSIT_GUANGGAO = "waiting_deposit_guanggao"  # 买广告
    WAITING_DEPOSIT_HUIYUAN = "waiting_deposit_huiyuan"    # 买会员
    
    # 等待用户输入
    WAITING_GROUP_ID = "waiting_group_id"  # 自助验群 - 等待群编号输入
    
    # 人工客服会话
    IN_HUMAN_SESSION = "in_human_session"  # 正在与人工客服对话


class UserStateData:
    """用户状态数据"""
    def __init__(self, state: UserState, service_type: str = "", created_at: datetime = None):
        self.state = state
        self.service_type = service_type
        self.created_at = created_at or datetime.now()
    
    def is_expired(self, expire_seconds: int = 3600) -> bool:
        """检查状态是否过期"""
        return datetime.now() - self.created_at > timedelta(seconds=expire_seconds)


class UserStateManager:
    """
    用户状态管理器
    
    使用内存存储，生产环境建议使用 Redis
    """
    
    def __init__(self, expire_seconds: int = 3600):
        self._states: Dict[int, UserStateData] = {}
        self.expire_seconds = expire_seconds
    
    def get_state(self, user_id: int) -> UserState:
        """获取用户当前状态"""
        if user_id not in self._states:
            return UserState.IDLE
        
        state_data = self._states[user_id]
        
        # 检查是否过期
        if state_data.is_expired(self.expire_seconds):
            self.clear_state(user_id)
            return UserState.IDLE
        
        return state_data.state
    
    def get_state_data(self, user_id: int) -> Optional[UserStateData]:
        """获取用户状态完整数据"""
        if user_id not in self._states:
            return None
        
        state_data = self._states[user_id]
        if state_data.is_expired(self.expire_seconds):
            self.clear_state(user_id)
            return None
        
        return state_data
    
    def set_state(self, user_id: int, state: UserState, service_type: str = "") -> None:
        """设置用户状态"""
        self._states[user_id] = UserStateData(
            state=state,
            service_type=service_type,
            created_at=datetime.now()
        )
    
    def clear_state(self, user_id: int) -> None:
        """清除用户状态"""
        if user_id in self._states:
            del self._states[user_id]
    
    def is_waiting_deposit(self, user_id: int) -> bool:
        """检查用户是否在等待上押截图状态"""
        state = self.get_state(user_id)
        return state in [
            UserState.WAITING_DEPOSIT_LA_ZHUAN,
            UserState.WAITING_DEPOSIT_KAI_GONG,
            UserState.WAITING_DEPOSIT_GUANGGAO,
            UserState.WAITING_DEPOSIT_HUIYUAN,
        ]
    
    def is_waiting_input(self, user_id: int) -> bool:
        """检查用户是否在等待输入状态"""
        state = self.get_state(user_id)
        return state == UserState.WAITING_GROUP_ID


# 创建全局状态管理器实例
user_state_manager = UserStateManager()

