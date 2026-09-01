from typing import Dict, List

class SkillDetector:
    """Файлын артефактаас skill evidence илрүүлэх"""
    
    SKILL_PATTERNS = {
        "Python": {
            "extensions": [".py"],
            "filenames": ["setup.py", "pyproject.toml", "requirements.txt", "Pipfile"],
            "directories": []
        },
        "TypeScript": {
            "extensions": [".ts", ".tsx"],
            "filenames": ["tsconfig.json"],
            "directories": []
        },
        "React / Next.js": {
            "extensions": [],
            "filenames": ["next.config.js", "next.config.ts", "vite.config.ts"],
            "directories": ["app", "pages", "components", "src"]
        },
        "Node.js": {
            "extensions": [".js"],
            "filenames": ["package.json", "package-lock.json", "yarn.lock"],
            "directories": []
        },
        "Testing": {
            "extensions": [],
            "filenames": ["pytest.ini", "conftest.py", "jest.config.js", "vitest.config.ts"],
            "directories": ["tests", "test", "__tests__"]
        },
        "C++": {
            "extensions": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
            "filenames": [],
            "directories": []
        },
        "CMake": {
            "extensions": [],
            "filenames": ["CMakeLists.txt"],
            "directories": []
        },
        "Data Engineering": {
            "extensions": [".sql"],
            "filenames": [],
            "directories": ["data", "etl", "pipeline"]
        },
        "Prisma / ORM": {
            "extensions": [".prisma"],
            "filenames": ["schema.prisma"],
            "directories": ["prisma"]
        },
        "Docker": {
            "extensions": [],
            "filenames": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
            "directories": []
        }
    }
    
    def detect_skills(self, files: List[dict]) -> Dict[str, int]:
        skill_scores = {skill: 0 for skill in self.SKILL_PATTERNS}
        
        for file in files:
            path = file["path"].lower()
            name = file["name"].lower()
            ext = file["extension"]
            
            for skill, patterns in self.SKILL_PATTERNS.items():
                if ext in patterns["extensions"]:
                    skill_scores[skill] += 1
                    continue
                if name in [f.lower() for f in patterns["filenames"]]:
                    skill_scores[skill] += 1
                    continue
                for dir_pattern in patterns["directories"]:
                    if f"/{dir_pattern}/" in path or path.startswith(f"{dir_pattern}/"):
                        skill_scores[skill] += 1
                        break
        
        return {skill: score for skill, score in skill_scores.items() if score > 0}
