import sys
import os
import pytest
import joblib
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit before importing logic.ai_core to avoid config file errors
# and to bypass @st.cache_resource
mock_st = MagicMock()
mock_st.cache_resource = lambda func: func
sys.modules['streamlit'] = mock_st

from logic.ai_core import load_local_models

class TestModelLoading:
    
    def test_load_local_models_success(self, tmp_path):
        """
        测试：当模型文件存在且有效时，能否正确加载
        tmp_path 是 pytest 自带的功能，会自动创建一个临时文件夹，测试完自动删除
        """
        # 1. 创建一个假的 dummy 模型
        fake_model_data = {"models": {"distance": "fake_rf_dist", "direction": "fake_rf_dir"}}
        
        # 2. 把这个假模型保存到临时文件夹里的 .pkl 文件
        fake_model_file = tmp_path / "weapon_classifier.pkl"
        joblib.dump(fake_model_data, fake_model_file)
        
        # 3. 关键点：我们要 Mock 掉 os.path.exists，让它指向我们的假文件
        # 同时 Mock 掉 joblib.load，虽然我们真的存了文件，但为了保险也可以 mock 加载过程
        # 但这里我们选择 Patch 'logic.ai_core.os.path.exists' 来欺骗路径检查
        
        # 注意：因为你的源代码里路径是写死的 "data/processed/...", 
        # 我们需要 Patch 那个硬编码的路径，或者 Patch joblib.load 让它直接读我们的假数据。
        
        # 方案：直接 Patch joblib.load，这是最稳的
        with patch('logic.ai_core.joblib.load') as mock_load:
            with patch('logic.ai_core.os.path.exists') as mock_exists:
                # 让代码以为文件存在
                mock_exists.return_value = True
                # 让加载函数返回我们的假数据
                mock_load.return_value = fake_model_data
                
                # 调用函数
                result = load_local_models()
                
                # 断言
                assert result is not None
                assert result['models']['distance'] == "fake_rf_dist"
                print("\n本地模型加载逻辑验证通过")

    def test_load_local_models_missing_file(self):
        """
        测试：当文件不存在时，函数应该返回 None 而不是让程序崩溃
        """
        with patch('logic.ai_core.os.path.exists') as mock_exists:
            # 模拟文件不存在
            mock_exists.return_value = False
            
            result = load_local_models()
            
            # 断言应该返回 None (根据你的代码逻辑)
            assert result is None
            print("\n模型缺失容错逻辑验证通过")