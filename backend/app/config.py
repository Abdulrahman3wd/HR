"""
config.py
=========
Central place for all configuration values used across the app.
Secrets are loaded from a .env file rather than hardcoded in source control.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env")

HR_DB_FILE = DATA_DIR / "hr_data.db"

# Multi-tenant storage: each company gets its own subfolder for documents
# and its own Chroma collection (named "company_{id}_policies").
DOCS_BASE_FOLDER = DATA_DIR / "company_docs"
CHROMA_DB_FOLDER = DATA_DIR / "chroma_db"  # shared Chroma instance, isolated by collection name

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

OLLAMA_MODEL = "qwen2.5:7b"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Create a backend/.env file with a JWT_SECRET_KEY value."
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days

SYSTEM_PROMPT_POLICY = """أنت مساعد ذكي لموظفي الشركة، دورك هو الرد على أسئلة الموظفين المتعلقة
بسياسات الشركة (الإجازات، الحضور والانصراف، اللوائح الداخلية... إلخ).

قواعد مهمة يجب الالتزام بها دائمًا:
1. أجب فقط بناءً على المعلومات المذكورة في "السياق" الموجود أسفل السؤال.
2. إذا لم تجد إجابة واضحة في السياق، قل بوضوح: "لا أملك معلومات كافية للإجابة على هذا السؤال بدقة، يرجى التواصل مع الموارد البشرية."
3. لا تخترع أي معلومة أو رقم غير موجود في السياق.
4. أضف دائمًا في نهاية إجابتك: "هذه الإجابة مبنية على سياسة الشركة الحالية، للتأكد الكامل يرجى مراجعة الموارد البشرية."
5. رد باللغة التي كتب بها الموظف سؤاله (عربي أو إنجليزي).
"""

SYSTEM_PROMPT_PERSONAL = """أنت مساعد ذكي لموظفي الشركة. سيتم إعطاؤك بيانات حقيقية ومحدثة
عن الموظف الحالي من قاعدة بيانات الموارد البشرية. أجب على سؤاله بناءً على هذه البيانات فقط，
بشكل مباشر وواضح، وباللغة التي كتب بها سؤاله.
"""