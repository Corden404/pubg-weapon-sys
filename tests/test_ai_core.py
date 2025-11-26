import sys
import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.ai_core import extract_features, predict_cloud

class TestAICore:
    
    # --- 测试 1: 本地特征提取 ---
    @patch('logic.ai_core.librosa')
    def test_extract_features_shape(self, mock_librosa):
        # 1. 准备假数据
        fake_y = np.random.rand(22050 * 2) 
        fake_sr = 22050
        mock_librosa.load.return_value = (fake_y, fake_sr)
        
        # 模拟特征返回
        mock_librosa.feature.zero_crossing_rate.return_value = np.array([[0.1]])
        mock_librosa.feature.rms.return_value = np.array([[0.2]])
        mock_librosa.feature.spectral_centroid.return_value = np.array([[1000]])
        mock_librosa.feature.mfcc.return_value = np.random.rand(13, 100)

        result = extract_features("dummy_audio.mp3")

        assert result is not None
        assert result.shape == (1, 16) 

    # --- 测试 2: 云端预测 (Mock Client 和 handle_file) ---
    
    # 注意：这里我们要 Patch 两个东西：
    # 1. logic.ai_core.Client (模拟网络请求)
    # 2. logic.ai_core.handle_file (模拟文件检查，防止因文件不存在报错)
    @patch('logic.ai_core.handle_file') 
    @patch('logic.ai_core.Client')
    def test_predict_cloud_success(self, mock_client_class, mock_handle_file):
        """测试：模拟云端 API 返回成功结果"""
        
        # 让 handle_file 什么都不做，直接返回路径字符串，骗过检查
        mock_handle_file.return_value = "dummy.mp3"
        
        # 设置 Client 的行为
        mock_instance = mock_client_class.return_value
        mock_instance.predict.return_value = {
            "label": "AKM",
            "confidences": [{"label": "AKM", "confidence": 0.95}]
        }

        # 调用函数
        result = predict_cloud("dummy.mp3")

        # 验证
        # 此时 handle_file 被 mock 了，不会报错，代码会走到 client.predict
        assert result['label'] == "AKM"
        assert result['confidences'][0]['confidence'] == 0.95

    @patch('logic.ai_core.handle_file')
    @patch('logic.ai_core.Client')
    def test_predict_cloud_failure(self, mock_client_class, mock_handle_file):
        """测试：模拟网络断连"""
        
        # 同样骗过文件检查
        mock_handle_file.return_value = "dummy.mp3"
        
        # 让 predict 抛出异常
        mock_instance = mock_client_class.return_value
        mock_instance.predict.side_effect = Exception("Connection Timeout")

        result = predict_cloud("dummy.mp3")

        # 验证
        assert "error" in result
        assert "Connection Timeout" in result["error"]