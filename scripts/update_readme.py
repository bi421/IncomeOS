import re
from pathlib import Path

readme = Path("README.md")
content = readme.read_text(encoding="utf-8")

arch_pattern = re.compile(
    r"# Architecture.*?The final layers are intentionally not considered complete yet\.",
    re.DOTALL
)

new_arch = """# Architecture

```text
+----------------------------------------+
| GitHub Evidence                        |
| Real Repositories                      |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Repository Analyzer                    |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Skill Detection                        |
| + Evidence                             |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Capability Profile                     |
| + Confidence                           |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Opportunity Matching                   |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Search + Audit                         |
| External Evidence                      |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Decision Engine                        |
|       V2                               |
+--------------------+-------------------+
                     v
+----------------------------------------+
| Action / Tracking                      |
+----------------------------------------+"""
new_content = arch_pattern.sub(new_arch, content)
readme.write_text(new_content, encoding="utf-8")
print("README.md амжилттай шинэчлэгдлээ.")
