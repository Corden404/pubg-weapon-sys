"""PUBG Weapon System API (FastAPI)

这份后端同时服务于 Web 前端（Next.js）和可能存在的其他客户端。

几个关键约定：
1) 认证：当前是“简化版登录”，不发 JWT；前端用 localStorage 保存 student_id/role。
2) 管理员：通过启动时自举的 admin 账号 + role=admin 来区分权限。
3) 审计日志：重要操作写入 MongoDB 的 logs 集合（utils.logger.log_action）。
4) 数据库：MongoDB，通过 utils.database.get_db() 获取。

如果后续要上生产（或多人协作），建议把认证升级为 JWT，并把 allow_origins 收紧。
"""

import sys
import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import shutil
import tempfile
from fastapi import UploadFile, File
from logic.ai_core import predict_cloud, extract_features, load_local_models

# NOTE:
# backend/ 目录不是一个标准 Python package（没有被安装/打包），
# 这里通过临时把项目根目录塞进 sys.path，让后端能 import utils/*。
# 如果未来要发布/部署，建议改为 package 结构或用环境变量 PYTHONPATH。
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.database import get_db, check_hashes, make_hash
from utils.logger import log_action

app = FastAPI(title="PUBG Weapon System API")


def _get_admin_credentials() -> tuple[str, str]:
    # 这两个变量让你在不同环境（本地/Codespaces/服务器）里
    # 通过环境变量配置管理员账号，无需改代码。
    admin_id = os.getenv("ADMIN_STUDENT_ID", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    return admin_id, admin_password


@app.on_event("startup")
def ensure_admin_user() -> None:
    """Ensure an admin account exists.

    This project uses a simplified auth model (no JWT). For usability,
    we bootstrap an admin user on startup based on environment variables.
    """
    # 启动时自举管理员账号：
    # - 第一次启动会创建用户
    # - 后续启动保持幂等（不会重复创建）
    db = get_db()
    if db is None:
        return

    admin_id, admin_password = _get_admin_credentials()
    existing = db.users.find_one({"student_id": admin_id})
    if existing is None:
        db.users.insert_one(
            {
                "student_id": admin_id,
                "password": make_hash(admin_password),
                "role": "admin",
                "inventory": [],
                "created_at": datetime.now(),
            }
        )
    else:
        # 老数据兼容：如果之前已存在同名用户但没有 role 字段，补齐。
        if existing.get("role") != "admin":
            db.users.update_one({"student_id": admin_id}, {"$set": {"role": "admin"}})

# --- 允许跨域 (让前端能访问后端) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. 定义数据模型 (前端必须传这两个字段) ---
class LoginRequest(BaseModel):
    # student_id 作为“用户名”，保持与数据库 users.student_id 一致
    student_id: str
    password: str


class RegisterRequest(BaseModel):
    """注册请求

    说明：这里保持最小字段集，密码确认（confirm password）放在前端做。
    后端只负责：校验是否可注册、写库、返回结果。
    """

    student_id: str
    password: str

# --- 2. 登录接口 ---
@app.post("/api/login")
def login(req: LoginRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # 查询用户（简化版，不做账号锁定/限流；课堂项目够用）
    user = db.users.find_one({"student_id": req.student_id})
    
    # 密码是 SHA256（utils.database.make_hash）；这不是最佳实践，但符合练习项目需求。
    if user and check_hashes(req.password, user['password']):
        # 登录成功：返回 role 信息给前端，用于 UI 侧做“管理员页面”拦截。
        # 这里不发 JWT，所以不要把它当成强安全方案。
        role = user.get("role", "user")
        log_action(db, req.student_id, "LOGIN", {"role": role})
        return {
            "status": "success", 
            "user": {
                "student_id": user['student_id'],
                "inventory_count": len(user.get('inventory', [])),
                "role": role,
                "is_admin": role == "admin",
            }
        }
    
    # 登录失败：仍然写日志，但不要写入明文密码。
    log_action(db, req.student_id, "LOGIN_FAILED", {"reason": "账号或密码错误"}, level="WARN")
    raise HTTPException(status_code=401, detail="账号或密码错误")


@app.post("/api/register")
def register(req: RegisterRequest):
    """注册新用户（Web 前端使用）。

    约束：
    - student_id 必须唯一
    - 管理员账号为系统保留（ADMIN_STUDENT_ID），不允许普通注册占用
    """

    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    student_id = (req.student_id or "").strip()
    if not student_id:
        raise HTTPException(status_code=400, detail="学号不能为空")

    admin_id, _ = _get_admin_credentials()
    if student_id == admin_id:
        raise HTTPException(status_code=400, detail="该学号为系统保留管理员账号，不能注册")

    # 是否已存在
    existing = db.users.find_one({"student_id": student_id})
    if existing is not None:
        log_action(db, student_id, "REGISTER_FAILED", {"reason": "学号已存在"}, level="WARN")
        raise HTTPException(status_code=409, detail="该学号已存在")

    db.users.insert_one(
        {
            "student_id": student_id,
            "password": make_hash(req.password),
            "role": "user",
            "inventory": [],
            "created_at": datetime.now(),
        }
    )
    log_action(db, student_id, "REGISTER", {"role": "user"})
    return {"status": "success", "message": "注册成功"}

# --- 3. 获取用户背包接口 ---
@app.get("/api/inventory/{student_id}")
def get_inventory(student_id: str):
    db = get_db()
    user = db.users.find_one({"student_id": student_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # inventory 是数组，每个元素结构：{weapon_name, ammo_count, added_at}
    inventory = user.get('inventory', [])
    
    # 给前端做 dashboard 展示用的聚合字段，避免前端自己算一遍。
    stats = {
        "total_ammo": sum(item.get('ammo_count', 0) for item in inventory),
        "total_weapons": len(inventory),
        "recent_item": inventory[-1]['weapon_name'] if inventory else "无"
    }
    
    return {
        "status": "success",
        "inventory": inventory,
        "stats": stats
    }


@app.delete("/api/inventory/{student_id}/{index}")
def delete_inventory_item(student_id: str, index: int):
    """Delete one inventory entry by index (0-based).

    背包是数组结构，删除用“下标”而不是用 $pull 按对象匹配：
    - added_at 是 datetime，序列化/精度容易导致匹配失败
    - weapon_name 也可能重复（同一把武器多次入库）
    所以用 index 删除更稳定。
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    user = db.users.find_one({"student_id": student_id}, {"_id": 0, "inventory": 1})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    inventory = user.get("inventory", [])
    if index < 0 or index >= len(inventory):
        raise HTTPException(status_code=400, detail="index 越界")

    # 删除前把被删项取出来，写日志/排查问题更方便。
    removed_item = inventory[index]

    # MongoDB 没有直接的“按下标删除并自动收缩数组”操作。
    # 常用技巧：先 $unset 置空，再 $pull 把 None 清理掉。
    db.users.update_one({"student_id": student_id}, {"$unset": {f"inventory.{index}": 1}})
    db.users.update_one({"student_id": student_id}, {"$pull": {"inventory": None}})
    log_action(db, student_id, "INVENTORY_DELETE", {"index": index, "item": removed_item})
    return {"status": "success", "message": "删除成功"}

@app.get("/")
def root():
    return {"message": "System Online"}

# --- 4. 获取所有武器列表 ---
@app.get("/api/weapons")
def get_weapons():
    db = get_db()
    # 排除 _id 字段，因为它不能直接转 JSON
    weapons = list(db.game_weapons.find({}, {"_id": 0}))
    return {"status": "success", "weapons": weapons}

# --- 5. 添加物品到背包 ---
class AddItemRequest(BaseModel):
    student_id: str
    weapon_name: str
    # ammo_count 是“子弹数/弹药数”，这里强制 int：
    # - 业务上不接受小数
    # - 也避免数据库里混入 float 导致统计计算不稳定
    ammo_count: int

@app.post("/api/inventory/add")
def add_to_inventory(req: AddItemRequest):
    db = get_db()
    
    # 写入 users.inventory：只存背包条目（weapon_name + ammo_count + added_at）。
    # 武器的静态属性（damage/stats 等）仍然以 game_weapons 为准。
    item = {
        "weapon_name": req.weapon_name,
        "ammo_count": req.ammo_count,
        "added_at": datetime.now() # 记录时间
    }
    
    result = db.users.update_one(
        {"student_id": req.student_id},
        {"$push": {"inventory": item}}
    )
    
    if result.modified_count > 0:
        log_action(db, req.student_id, "ADD_ITEM", item)
        return {"status": "success", "message": f"已添加 {req.weapon_name}"}
    
    raise HTTPException(status_code=400, detail="添加失败")


# --- 6. AI 分析接口 ---
@app.post("/api/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    x_student_id: str | None = Header(None, alias="X-Student-Id"),
):
    # x_student_id：从前端透传的“当前用户”，用于审计日志。
    # 这个接口本身不做强认证（课堂项目），但日志能帮你定位谁在操作。
    # 1. 保存上传的文件到临时目录
    # 使用 tempfile 防止文件名冲突
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        results = {
            "cloud": {"label": "Unknown", "confidence": 0.0},
            "local": {"distance": "N/A", "direction": "N/A"}
        }

        # 2. 云端推理 (Hugging Face)
        try:
            cloud_res = predict_cloud(tmp_path)
            # 解析返回结果 (根据你的 ai_core 逻辑)
            if isinstance(cloud_res, dict) and 'label' in cloud_res:
                results["cloud"]["label"] = cloud_res['label']
                # 如果有置信度字段
                if 'confidences' in cloud_res:
                     results["cloud"]["confidence"] = cloud_res['confidences'][0]['confidence']
            elif isinstance(cloud_res, str):
                 results["cloud"]["label"] = cloud_res
        except Exception as e:
            print(f"Cloud Error: {e}")

        # 3. 本地推理 (Random Forest)
        # 本地模型不一定存在（例如没训练/没拷贝 pkl），所以这里允许返回 N/A。
        try:
            local_models = load_local_models()
            if local_models:
                feats = extract_features(tmp_path)
                if feats is not None:
                    # 获取原始预测结果 (可能是 "50m", "100m" 或 数字)
                    raw_dist = local_models['models']['distance'].predict(feats)[0]
                    raw_dir = local_models['models']['direction'].predict(feats)[0]
                    
                    # --- 数据清洗逻辑 (Fix: 去掉 'm' 和 '°') ---
                    
                    # 1. 处理距离 (Distance)
                    try:
                        # 如果是字符串，去掉 'm' 和空格
                        if isinstance(raw_dist, str):
                            clean_dist = raw_dist.lower().replace('m', '').strip()
                            results["local"]["distance"] = float(clean_dist)
                        else:
                            results["local"]["distance"] = float(raw_dist)
                    except ValueError:
                        # 如果实在转不了数字（比如预测结果是 "Far"），就原样返回
                        results["local"]["distance"] = raw_dist

                    # 2. 处理方位 (Direction)
                    try:
                        if isinstance(raw_dir, str):
                            clean_dir = raw_dir.lower().replace('°', '').replace('degree', '').strip()
                            results["local"]["direction"] = float(clean_dir)
                        else:
                            results["local"]["direction"] = float(raw_dir)
                    except ValueError:
                        results["local"]["direction"] = raw_dir

        except Exception as e:
            print(f"Local Error: {e}")

        # 写审计日志：只要带了 X-Student-Id 且数据库可用就记录。
        # 注意不要记录原始音频（体积大、也没必要）；记录结构化结果即可。
        db = get_db()
        if db is not None and x_student_id:
            log_action(db, x_student_id, "AI_ANALYZE", {"result": results})

        return {"status": "success", "data": results}

    finally:
        # 4. 清理临时文件 (好习惯)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _require_admin(x_student_id: str = Header(None, alias="X-Student-Id")) -> str:
    # 这里的“鉴权”是最简单的：用请求头携带 student_id，再查 users.role。
    # 不要把它当成安全方案；真正的管理员接口应该用 JWT/Session。
    if not x_student_id:
        raise HTTPException(status_code=401, detail="缺少管理员凭据")

    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    user = db.users.find_one({"student_id": x_student_id})
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="无管理员权限")
    return x_student_id


@app.get("/api/admin/users/weapons")
def admin_get_all_users_weapon_details(x_student_id: str = Header(None, alias="X-Student-Id")):
    """管理员接口：查看所有玩家背包，并把武器静态属性拼进去。

    返回结构：
    - users[i].inventory[j] 里会多一个 weapon 字段（来自 game_weapons）。
    这样前端不用多次请求，也不需要自己在浏览器里做 join。
    """
    # 同一个 header 既用于鉴权也用于审计（admin_id 返回给前端方便展示）。
    admin_id = _require_admin(x_student_id)
    db = get_db()

    users = list(db.users.find({}, {"_id": 0, "password": 0}))
    # 把武器表预先拉出来，做成 dict，加速 join。
    weapons = list(db.game_weapons.find({}, {"_id": 0}))
    weapon_by_name = {w.get("name"): w for w in weapons if w.get("name")}

    enriched = []
    for u in users:
        inv = u.get("inventory", []) or []
        inv_items = []
        for item in inv:
            wname = item.get("weapon_name")
            inv_items.append(
                {
                    **item,
                    "weapon": weapon_by_name.get(wname),
                }
            )

        enriched.append(
            {
                "student_id": u.get("student_id"),
                "role": u.get("role", "user"),
                "inventory": inv_items,
                "inventory_count": len(inv_items),
            }
        )

    return {"status": "success", "admin": admin_id, "users": enriched}

# --- 7. 更新武器数据 (管理员) ---
class UpdateWeaponRequest(BaseModel):
    damage: int
    type: str

@app.put("/api/weapons/{name}")
def update_weapon(name: str, req: UpdateWeaponRequest):
    db = get_db()
    
    result = db.game_weapons.update_one(
        {"name": name},
        {"$set": {"damage": req.damage, "type": req.type}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="武器不存在")
    
    return {"status": "success", "message": f"{name} 数据已更新"}