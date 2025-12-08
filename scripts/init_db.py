"""
数据库初始化脚本
创建表并填充示例数据
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database import Database, GroupInfo


# 示例群数据
SAMPLE_GROUPS = [
    GroupInfo(
        group_id="专群A12345",
        group_type="专群",
        owner_name="张老板",
        status="active",
        deposit_amount=5000.0,
        created_at="2024-01-15",
    ),
    GroupInfo(
        group_id="公群12345",
        group_type="公群",
        owner_name="李老板",
        status="active",
        deposit_amount=15000.0,
        created_at="2024-02-20",
    ),
    GroupInfo(
        group_id="飞博13",
        group_type="飞博",
        owner_name="王老板",
        status="active",
        deposit_amount=20000.0,
        created_at="2024-03-10",
    ),
    GroupInfo(
        group_id="专群B54321",
        group_type="专群",
        owner_name="赵老板",
        status="active",
        deposit_amount=8000.0,
        created_at="2024-04-05",
    ),
    GroupInfo(
        group_id="公群67890",
        group_type="公群",
        owner_name="孙老板",
        status="closed",
        deposit_amount=12000.0,
        created_at="2024-05-15",
    ),
    GroupInfo(
        group_id="飞博88",
        group_type="飞博",
        owner_name="周老板",
        status="active",
        deposit_amount=25000.0,
        created_at="2024-06-20",
    ),
]


def init_database(db_path: str = "bot_data.db", force: bool = False) -> None:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        force: 是否强制重新初始化（删除现有数据）
    """
    print(f"正在初始化数据库: {db_path}")
    
    # 如果强制重置，删除现有数据库
    if force and os.path.exists(db_path):
        os.remove(db_path)
        print(f"已删除现有数据库: {db_path}")
    
    # 创建数据库实例
    db = Database(db_path)
    
    # 初始化表
    db.init_tables()
    print("✅ 数据库表已创建")
    
    # 检查是否已有数据
    existing_count = db.count_groups()
    if existing_count > 0 and not force:
        print(f"数据库已有 {existing_count} 条群记录，跳过示例数据填充")
        print("使用 --force 参数强制重新初始化")
        return
    
    # 插入示例数据
    inserted = 0
    for group in SAMPLE_GROUPS:
        try:
            db.insert_group(group)
            inserted += 1
            print(f"  + 插入群: {group.group_id} ({group.owner_name})")
        except Exception as e:
            print(f"  ! 跳过群 {group.group_id}: {e}")
    
    print(f"\n✅ 初始化完成！插入了 {inserted} 条示例群记录")
    
    # 验证数据
    print("\n📋 当前数据库内容:")
    for group in db.get_all_groups():
        status_icon = "✅" if group.status == "active" else "⚠️"
        print(f"  {status_icon} {group.group_id} - {group.owner_name} - {group.deposit_amount}U")
    
    db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化土豆担保机器人数据库")
    parser.add_argument(
        "--db-path",
        default="bot_data.db",
        help="数据库文件路径 (默认: bot_data.db)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新初始化，删除现有数据"
    )
    
    args = parser.parse_args()
    init_database(args.db_path, args.force)

