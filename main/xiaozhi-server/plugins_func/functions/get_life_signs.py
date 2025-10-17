import pymysql
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action

TAG = __name__
logger = setup_logging()


QUERY_LIFE_SIGNS_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_life_signs",
        "description": "查询 life_signs 库中的生命体征信息，返回最后一条数据。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

# --- 数据库连接 ---
def get_db_connection(conn, database: str):
    """根据配置获取数据库连接"""
    logger.bind(tag=TAG).info(f"连接数据库: {database}")
    db_conf = conn.config["plugins"].get("db_conf", {})  # 统一配置
    return pymysql.connect(
        host=db_conf.get("host", "192.168.17.100"),
        port=int(db_conf.get("port", 3306)),
        user=db_conf.get("user", "wsluser"),
        password=db_conf.get("password", "123456"),
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


# --- 查询生命体征 ---
@register_function("get_life_signs", QUERY_LIFE_SIGNS_FUNCTION_DESC, ToolType.SYSTEM_CTL)
def get_life_signs(conn):
    """查询 life_signs.med_robot_vital_data 表的最后一条记录"""
    try:
        connection = get_db_connection(conn, "life_signs")
        with connection.cursor() as cursor:
            # 假设表里有自增ID或者时间字段，比如 id 或者 create_time，按它排序
            sql = "SELECT * FROM med_robot_vital_data ORDER BY TIME_POINT DESC LIMIT 1"
            cursor.execute(sql)
            result = cursor.fetchone()
        connection.close()

        if not result:
            return ActionResponse(Action.REQLLM, "未找到相关生命体征数据", None)

        # 根据表字段名输出
        sign_text = (
            f"设备标签:{result.get('DEVICE_LABEL')} "
            f"心率:{result.get('HR')} "
            f"体温:{result.get('TEMP')} "
            f"血氧:{result.get('SPO2')} "
            f"无创收缩压:{result.get('NIBPs')} "
            f"无创舒张压:{result.get('NIBPd')} "
            f"步数:{result.get('Steps')}"
        )
        return ActionResponse(Action.REQLLM, sign_text, None)

    except Exception as e:
        logger.error(f"查询 med_robot_vital_data 失败: {e}")
        return ActionResponse(Action.REQLLM, None, f"查询失败: {e}")
