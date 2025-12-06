import subprocess
import json
import tempfile
import os
from typing import List


def run_pylint(file_path: str, timeout: int = 10) -> List[dict]:
	"""Run pylint on a file and return parsed JSON results.
	Requires pylint installed and available on PATH.
	"""
	cmd = ["pylint", "--output-format=json", file_path]
	try:
		proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
	except subprocess.TimeoutExpired:
		raise

	if proc.returncode not in (0, 32, 1, 2, 4, 8):
		# Some non-zero codes still include JSON output; parse if present
		pass

	out = proc.stdout.strip()
	if not out:
		return []

	try:
		data = json.loads(out)
		return data if isinstance(data, list) else []
	except json.JSONDecodeError:
		return []


def run_black_on_content(content: str, timeout: int = 10) -> str:
	"""Format Python content using black. Returns formatted content.
	Writes to a temp file and formats it.
	"""
	import shutil

	with tempfile.NamedTemporaryFile("w+", suffix=".py", delete=False, encoding="utf-8") as tf:
		tf.write(content)
		tf.flush()
		temp_path = tf.name

	try:
		cmd = ["black", temp_path]
		subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
		with open(temp_path, "r", encoding="utf-8") as fh:
			formatted = fh.read()
	finally:
		try:
			os.remove(temp_path)
		except Exception:
			pass

	return formatted

