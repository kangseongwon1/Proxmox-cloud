#!/usr/bin/env python3
"""
기존 admin 사용자의 비밀번호를 admin123!로 재설정하는 스크립트
"""
import os
import sys
import psycopg2
from werkzeug.security import generate_password_hash

def fix_admin_password():
    """admin 사용자의 비밀번호를 재설정"""
    
    # 환경 변수에서 데이터베이스 URL 가져오기
    database_url = os.environ.get('DATABASE_URL', 'postgresql://proxmox:proxmox123@localhost:5432/proxmox_manager')
    
    print("🔧 Admin 비밀번호 재설정 시작")
    print(f"📊 데이터베이스 URL: {database_url}")
    
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ PostgreSQL 연결 성공")
        
        # admin 사용자 확인
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("❌ admin 사용자를 찾을 수 없습니다.")
            print("💡 먼저 init_postgres_schema.py를 실행하여 사용자를 생성하세요.")
            sys.exit(1)
        
        admin_id = admin_user[0]
        print(f"✅ admin 사용자 발견 (ID: {admin_id})")
        
        # 비밀번호 해시 생성
        admin_password = 'admin123!'
        admin_password_hash = generate_password_hash(admin_password)
        
        # 비밀번호 업데이트
        print("🔐 비밀번호 해시 생성 중...")
        cursor.execute("""
            UPDATE users 
            SET password_hash = %s, role = %s
            WHERE id = %s
        """, (admin_password_hash, 'admin', admin_id))
        
        conn.commit()
        
        print("✅ Admin 비밀번호가 성공적으로 재설정되었습니다.")
        print(f"👤 사용자명: admin")
        print(f"🔑 비밀번호: admin123!")
        print("⚠️  보안을 위해 로그인 후 비밀번호를 변경하세요!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 비밀번호 재설정 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_admin_password()

