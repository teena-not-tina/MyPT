# src/utils/passwordHasher.py (비밀번호 해싱 유틸리티)
# 이 기능은 보통 Flask의 werkzeug.security나 bcrypt 라이브러리에서 제공합니다.
# 직접 구현할 필요는 거의 없습니다.
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    return check_password_hash(hashed_password, password)
