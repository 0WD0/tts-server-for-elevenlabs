from typing import Dict, List, Optional
from elevenlabs.client import ElevenLabs
import time

class ApiKeyStatus:
	def __init__(self, key: str):
		self.key = key
		self.is_active = True
		self.error_count = 0
		self.consecutive_errors = 0
		self.last_used : float = 0
		self.last_error : Optional[str] = None
		self.client = ElevenLabs(api_key=key)

class ApiKeyManager:
	def __init__(self, keys: List[str], consecutive_errors_limit: int = 2):
		"""
		初始化 API key 管理器
		:param keys: API key 列表
		:param consecutive_errors_limit: 连续错误次数限制，超过后永久禁用
		"""
		self.key_status: Dict[str, ApiKeyStatus] = {}
		self.consecutive_errors_limit = consecutive_errors_limit
		
		# 初始化每个 key 的状态
		for key in keys:
			if key.strip():
				self.key_status[key] = ApiKeyStatus(key)
	
	def get_key(self) -> Optional[str]:
		"""
		获取一个可用的 API key
		优先返回连续错误次数最少的 key
		"""
		available_keys = [
			(status.consecutive_errors, status.key)
			for status in self.key_status.values()
			if status.is_active
		]
		
		if not available_keys:
			return None
		
		# 按连续错误次数排序，返回错误最少的
		_, best_key = min(available_keys)
		self.key_status[best_key].last_used = time.time()
		return best_key
			
	
	def get_client(self) -> Optional[ElevenLabs]:
		"""
		获取一个可用的 ElevenLabs 客户端
		"""
		key = self.get_key()
		if key:
			return self.key_status[key].client
		return None

	def report_error(self, key: str, error: str):
		"""
		报告 API key 使用时发生的错误
		如果连续错误次数超过限制，将永久禁用该 key
		"""
		if key not in self.key_status:
			return
		
		status = self.key_status[key]
		status.error_count += 1
		status.consecutive_errors += 1
		status.last_error = error
		
		# 如果连续错误次数超过限制，永久禁用
		if status.consecutive_errors >= self.consecutive_errors_limit:
			status.is_active = False
	
	def report_success(self, key: str):
		"""
		报告 API key 使用成功
		重置连续错误计数
		"""
		if key not in self.key_status:
			return
		
		status = self.key_status[key]
		status.consecutive_errors = 0
	
	def get_status(self) -> Dict:
		"""
		获取所有 API key 的状态
		"""
		return {
			key: {
				"is_active": status.is_active,
				"error_count": status.error_count,
				"consecutive_errors": status.consecutive_errors,
				"last_used": status.last_used,
				"last_error": status.last_error
			}
			for key, status in self.key_status.items()
		}
