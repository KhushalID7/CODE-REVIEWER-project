import difflib
from typing import List


def make_unified_diff(original: str, updated: str, path: str = "file.py") -> str:
	"""Return a unified diff between original and updated content."""
	o_lines = original.splitlines(keepends=True)
	u_lines = updated.splitlines(keepends=True)
	diff = difflib.unified_diff(o_lines, u_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
	return "".join(diff)


def apply_patch_to_content(original: str, patch_text: str) -> str:
	"""Apply a unified diff patch to original content and return patched content.
	This implements a minimal unified diff applier; supports single-file diffs.
	Raises ValueError if patch cannot be applied.
	"""
	if not patch_text:
		return original

	orig_lines = original.splitlines()
	patched_lines: List[str] = []

	# Parse patch hunks
	lines = patch_text.splitlines()
	i = 0
	curr = 0  # pointer in orig_lines (0-based)

	while i < len(lines):
		line = lines[i]
		if line.startswith('@@'):
			# Hunk header: @@ -start,count +start,count @@
			header = line
			try:
				parts = header.split(' ')
				old_range = parts[1]
				# old_range like '-3,7'
				old_start = int(old_range.split(',')[0].lstrip('-')) - 1
			except Exception:
				raise ValueError('Malformed hunk header')

			# copy unchanged lines before hunk
			while curr < old_start and curr < len(orig_lines):
				patched_lines.append(orig_lines[curr])
				curr += 1

			i += 1
			# process hunk lines
			while i < len(lines) and not lines[i].startswith('@@'):
				h = lines[i]
				if not h:
					# blank line in diff corresponds to a context line of ''
					# treat as context
					patched_lines.append('')
				elif h.startswith(' '):
					# context: copy from original
					content = h[1:]
					patched_lines.append(content)
					curr += 1
				elif h.startswith('-'):
					# removed line: skip original
					curr += 1
				elif h.startswith('+'):
					# added line: append without consuming original
					patched_lines.append(h[1:])
				else:
					# other markers - ignore
					pass
				i += 1
		else:
			i += 1

	# append remaining original lines
	while curr < len(orig_lines):
		patched_lines.append(orig_lines[curr])
		curr += 1

	# Reconstruct with newline
	return "\n".join(patched_lines) + ("\n" if original.endswith('\n') else '')

