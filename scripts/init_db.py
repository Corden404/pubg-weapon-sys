"""Database initialization helpers.

Currently this script ensures an admin user exists.

Usage:
  python scripts/init_db.py

Env:
  ADMIN_STUDENT_ID   (default: admin)
  ADMIN_PASSWORD     (default: admin123)

Mongo connection:
  Uses the same secrets.toml resolution approach as other scripts.
"""

import os
import toml
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def get_db_connection():
	try:
		current_dir = os.path.dirname(os.path.abspath(__file__))
		project_root = os.path.dirname(current_dir)
		secrets_path = os.path.join(project_root, ".streamlit", "secrets.toml")

		config = toml.load(secrets_path)
		uri = config["mongo"]["uri"]

		client = MongoClient(uri, server_api=ServerApi("1"))
		client.admin.command("ping")
		return client.pubg_sys
	except Exception as e:
		print(f"连接失败: {e}")
		return None


def make_hash(password: str) -> str:
	import hashlib

	return hashlib.sha256(str.encode(password)).hexdigest()


def ensure_admin(db):
	admin_id = os.getenv("ADMIN_STUDENT_ID", "admin")
	admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

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
		print(f"已创建管理员账号: {admin_id}")
	else:
		if existing.get("role") != "admin":
			db.users.update_one({"student_id": admin_id}, {"$set": {"role": "admin"}})
			print(f"已将用户 {admin_id} 升级为管理员")
		else:
			print(f"管理员账号已存在: {admin_id}")


if __name__ == "__main__":
	db = get_db_connection()
	if db is None:
		raise SystemExit(1)
	ensure_admin(db)
