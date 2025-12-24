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

# --- 路径黑魔法：确保能导入 utils ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.database import get_db, check_hashes, make_hash

app = FastAPI(title="PUBG Weapon System API")


def _get_admin_credentials() -> tuple[str, str]:
    admin_id = os.getenv("ADMIN_STUDENT_ID", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    return admin_id, admin_password


@app.on_event("startup")
def ensure_admin_user() -> None:
    """Ensure an admin account exists.

    This project uses a simplified auth model (no JWT). For usability,
    we bootstrap an admin user on startup based on environment variables.
    """
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
        # Backfill role if the user existed before this feature.
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
    student_id: str
    password: str

# --- 2. 登录接口 ---
@app.post("/api/login")
def login(req: LoginRequest):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # 查询用户
    user = db.users.find_one({"student_id": req.student_id})
    
    # 校验密码
    if user and check_hashes(req.password, user['password']):
        # 登录成功，返回用户信息 (实际项目中这里会发 JWT Token)
        role = user.get("role", "user")
        return {
            "status": "success", 
            "user": {
                "student_id": user['student_id'],
                "inventory_count": len(user.get('inventory', [])),
                "role": role,
                "is_admin": role == "admin",
            }
        }
    
    # 登录失败
    raise HTTPException(status_code=401, detail="账号或密码错误")

# --- 3. 获取用户背包接口 ---
@app.get("/api/inventory/{student_id}")
def get_inventory(student_id: str):
    db = get_db()
    user = db.users.find_one({"student_id": student_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    inventory = user.get('inventory', [])
    
    # 简单的统计数据，供前端画图用
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

    Inventory items are stored as an array. We delete by index to avoid
    datetime matching/precision issues.
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

    # Unset the array element then pull nulls to compact.
    db.users.update_one({"student_id": student_id}, {"$unset": {f"inventory.{index}": 1}})
    db.users.update_one({"student_id": student_id}, {"$pull": {"inventory": None}})
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
    ammo_count: int

@app.post("/api/inventory/add")
def add_to_inventory(req: AddItemRequest):
    db = get_db()
    
    # 构造要存的数据
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
        return {"status": "success", "message": f"已添加 {req.weapon_name}"}
    
    raise HTTPException(status_code=400, detail="添加失败")


# --- 6. AI 分析接口 ---
@app.post("/api/analyze")
async def analyze_audio(file: UploadFile = File(...)):
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

        return {"status": "success", "data": results}

    finally:
        # 4. 清理临时文件 (好习惯)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _require_admin(x_student_id: str = Header(None, alias="X-Student-Id")) -> str:
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
    """Admin-only: list all users and their inventory enriched with weapon details."""
    # We validate admin using the same header.
    admin_id = _require_admin(x_student_id)
    db = get_db()

    users = list(db.users.find({}, {"_id": 0, "password": 0}))
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