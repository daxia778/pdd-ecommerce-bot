import time
import hashlib
import json
import httpx
from typing import Dict, Any
from config.settings import settings
from src.utils.logger import logger

class PddApiClient:
    """
    拼多多开放平台 API 客户端
    封装签名生成和网络请求逻辑。
    """
    def __init__(self):
        self.gateway_url = "https://gw-api.pinduoduo.com/api/router"
        self.client_id = settings.pdd_app_key
        self.client_secret = settings.pdd_app_secret
        self.access_token = settings.pdd_access_token
        
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        生成拼多多 API 签名
        官方规则: MD5(client_secret + key1+value1 + key2+value2... + client_secret)
        按 key 的首字母升序排序
        """
        sorted_keys = sorted(params.keys())
        sign_str = self.client_secret
        
        for k in sorted_keys:
            v = params[k]
            # 这里拼多多要求布尔类型转字符串或不加入特定结构，具体依官方最新文档为准
            # 标准做法是将 value 转为字符串
            if isinstance(v, (dict, list)):
                sign_str += f"{k}{json.dumps(v, separators=(',', ':'))}"
            else:
                sign_str += f"{k}{v}"
                
        sign_str += self.client_secret
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    async def send_customer_message(self, mall_id: str, buyer_id: str, content: str) -> bool:
        """
        调用拼多多 API 给买家发送客服消息
        此处的 API type 名称 (`pdd.pop.cs.message.send`) 需要替换为您申请的实际 API 名称
        """
        if not self.client_id or not self.client_secret or not self.access_token:
            logger.warning("PDD API 凭证未配置，无法发送真实消息（已降级为仅日志模式）")
            # 在测试环境或未配置凭证下模拟成功
            return True
            
        params = {
            "type": "pdd.pop.cs.message.send",  # 示例 API 名称，具体参阅 PDD 开放平台文档
            "client_id": self.client_id,
            "access_token": self.access_token,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "V1",
            # 业务参数
            "mall_id": mall_id,
            "buyer_id": buyer_id,
            "message_type": "text",
            "content": content
        }
        
        params["sign"] = self._generate_sign(params)
        
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"PDD API | 正在发送消息至买家 {buyer_id[:8]}...")
                response = await client.post(
                    self.gateway_url,
                    json=params,
                    timeout=10.0
                )
                
                resp_data = response.json()
                # 检查拼多多返回的错误包体，这里假设包含 error_response 字段为失败
                if "error_response" in resp_data:
                    logger.error(f"PDD API 错误返回: {resp_data['error_response']}")
                    return False
                
                logger.info(f"PDD API | 消息发送成功")
                return True
                
        except Exception as e:
            logger.error(f"PDD API | 请求异常: {e}")
            return False

pdd_api_client = PddApiClient()
