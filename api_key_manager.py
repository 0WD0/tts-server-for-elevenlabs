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
	error_count: int = 0           # 总错误次数
	consecutive_errors: int = 0    # 连续错误次数
	last_used: float = 0
	last_error: Optional[str] = None
	permanently_disabled: bool = False  # 永久禁用标志
	cooldown_until: float = 0

class ApiKeyManager:
	def __init__(self, keys: List[str], consecutive_errors_limit: int = 2):
		"""
		初始化 API Key 管理器
		:param keys: API key 列表
		:param consecutive_errors_limit: 连续错误次数限制，达到后永久禁用
		"""
		self.consecutive_errors_limit = consecutive_errors_limit
		self.keys: Dict[str, ApiKeyStatus] = {
			key: ApiKeyStatus(key=key) for key in keys
		}
		self._current_key: Optional[str] = None

	def get_key(self) -> Optional[str]:
		"""获取一个可用的 API key"""
		now = time.time()
		available_keys = [
			k for k, v in self.keys.items()
			if v.is_active and not v.permanently_disabled
		]

		if not available_keys:
			logger.error("No API keys available!")
			return None

		# 优先选择连续错误次数最少的 key
		available_keys.sort(key=lambda k: self.keys[k].consecutive_errors)
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
		key_status.consecutive_errors += 1
		key_status.last_error = error

		if key_status.consecutive_errors >= self.consecutive_errors_limit:
			key_status.permanently_disabled = True
			key_status.is_active = False
			logger.warning(f"API key {key[:8]}... has been permanently disabled due to {key_status.consecutive_errors} consecutive errors.")
			logger.warning(f"Last error: {error}")

	def report_success(self, key: str) -> None:
		"""报告 API key 使用成功"""
		if key not in self.keys:
			return

		key_status = self.keys[key]
		key_status.consecutive_errors = 0  # 重置连续错误计数

	def get_status(self) -> Dict[str, Dict]:
		"""获取所有 API key 的状态"""
		now = time.time()
		return {
			f"{k[:8]}...": {
				"active": v.is_active,
				"permanently_disabled": v.permanently_disabled,
				"total_errors": v.error_count,
				"consecutive_errors": v.consecutive_errors,
				"last_used": f"{int(now - v.last_used)}s ago" if v.last_used > 0 else "never",
				"last_error": v.last_error,
			}
			for k, v in self.keys.items()
		}
