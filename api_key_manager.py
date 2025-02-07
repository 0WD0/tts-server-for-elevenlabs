from typing import List, Dict, Optional
import time
import random
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ApiKeyStatus:
	key: str
	is_active: bool = True
	error_count: int = 0
	last_used: float = 0
	last_error: Optional[str] = None
	cooldown_until: float = 0

class ApiKeyManager:
	def __init__(self, keys: List[str], max_errors: int = 3, cooldown_period: int = 300):
		"""
		初始化 API Key 管理器
		:param keys: API key 列表
		:param max_errors: 最大错误次数，超过后会暂时禁用该 key
		:param cooldown_period: 冷却时间（秒），key 被禁用后多久后重试
		"""
		self.max_errors = max_errors
		self.cooldown_period = cooldown_period
		self.keys: Dict[str, ApiKeyStatus] = {
			key: ApiKeyStatus(key=key) for key in keys
		}
		self._current_key: Optional[str] = None

	def get_key(self) -> Optional[str]:
		"""获取一个可用的 API key"""
		now = time.time()
		available_keys = [
			k for k, v in self.keys.items()
			if v.is_active and now >= v.cooldown_until
		]
		
		if not available_keys:
			# 如果没有可用的 key，尝试重新激活已冷却的 key
			for key_status in self.keys.values():
				if not key_status.is_active and now >= key_status.cooldown_until:
					key_status.is_active = True
					key_status.error_count = 0
					available_keys.append(key_status.key)

		if not available_keys:
			logger.error("No API keys available!")
			return None

		# 优先选择错误次数最少的 key
		available_keys.sort(key=lambda k: self.keys[k].error_count)
		selected_key = available_keys[0]
		
		self._current_key = selected_key
		self.keys[selected_key].last_used = now
		return selected_key

	def report_error(self, key: str, error: str) -> None:
		"""报告 API key 使用时的错误"""
		if key not in self.keys:
			return

		key_status = self.keys[key]
		key_status.error_count += 1
		key_status.last_error = error

		if key_status.error_count >= self.max_errors:
			key_status.is_active = False
			key_status.cooldown_until = time.time() + self.cooldown_period
			logger.warning(f"API key {key[:8]}... disabled due to too many errors. "
						 f"Will retry after {self.cooldown_period} seconds.")

	def report_success(self, key: str) -> None:
		"""报告 API key 使用成功"""
		if key not in self.keys:
			return

		key_status = self.keys[key]
		if key_status.error_count > 0:
			key_status.error_count = max(0, key_status.error_count - 1)

	def get_status(self) -> Dict[str, Dict]:
		"""获取所有 API key 的状态"""
		now = time.time()
		return {
			f"{k[:8]}...": {
				"active": v.is_active,
				"error_count": v.error_count,
				"last_used": f"{int(now - v.last_used)}s ago" if v.last_used > 0 else "never",
				"last_error": v.last_error,
				"cooldown_remaining": max(0, int(v.cooldown_until - now)) if v.cooldown_until > now else 0
			}
			for k, v in self.keys.items()
		}
