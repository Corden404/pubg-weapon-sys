import sys
import os
import pytest

# --- 关键：把项目根目录加入 Python 搜索路径，否则找不到 utils 模块 ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.database import make_hash, check_hashes

class TestSecurity:
    def test_hash_generation(self):
        """测试：加密后的字符串应该不再是明文"""
        password = "secret_password"
        hashed = make_hash(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 产生的长度固定是 64 字符

    def test_hash_verification_success(self):
        """测试：正确的密码应该校验通过"""
        password = "my_password_123"
        hashed = make_hash(password)
        
        # 验证逻辑
        assert check_hashes(password, hashed) is True

    def test_hash_verification_failure(self):
        """测试：错误的密码应该校验失败"""
        password = "correct_password"
        hashed = make_hash(password)
        
        # 用错误的密码去试
        assert check_hashes("wrong_password", hashed) is False