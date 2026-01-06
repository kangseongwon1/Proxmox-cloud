#!/usr/bin/env python3
"""
기존 datastores 테이블에 누락된 컬럼을 추가하는 스크립트
"""
import os
import sys
import psycopg2

def fix_datastores_schema():
    """datastores 테이블에 누락된 컬럼 추가"""
    
    # 환경 변수에서 데이터베이스 URL 가져오기
    database_url = os.environ.get('DATABASE_URL', 'postgresql://proxmox:proxmox123@localhost:5432/proxmox_manager')
    
    print("🔧 Datastores 테이블 스키마 수정 시작")
    print(f"📊 데이터베이스 URL: {database_url}")
    
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ PostgreSQL 연결 성공")
        
        # 기존 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'datastores'
            ORDER BY ordinal_position;
        """)
        existing_columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        print("📋 기존 컬럼:", list(existing_columns.keys()))
        
        # id 컬럼이 SERIAL인지 확인하고 VARCHAR로 변경 필요 여부 확인
        if 'id' in existing_columns:
            if existing_columns['id'] in ['integer', 'bigint']:
                print("⚠️  id 컬럼이 INTEGER 타입입니다. VARCHAR로 변경이 필요합니다.")
                print("⚠️  기존 데이터가 있다면 수동으로 마이그레이션해야 합니다.")
                # 기존 데이터가 없으면 테이블 재생성
                cursor.execute("SELECT COUNT(*) FROM datastores")
                count = cursor.fetchone()[0]
                if count == 0:
                    print("✅ datastores 테이블이 비어있습니다. 테이블 재생성...")
                    cursor.execute("DROP TABLE IF EXISTS datastores CASCADE;")
                    cursor.execute("""
                        CREATE TABLE datastores (
                            id VARCHAR(100) PRIMARY KEY,
                            name VARCHAR(100) UNIQUE NOT NULL,
                            type VARCHAR(50) NOT NULL,
                            size BIGINT DEFAULT 0,
                            used BIGINT DEFAULT 0,
                            available BIGINT DEFAULT 0,
                            content TEXT,
                            enabled BOOLEAN DEFAULT TRUE,
                            is_default_hdd BOOLEAN DEFAULT FALSE,
                            is_default_ssd BOOLEAN DEFAULT FALSE,
                            is_system_default BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    print("✅ 테이블 재생성 완료")
                else:
                    print("❌ 기존 데이터가 있어서 자동 마이그레이션을 건너뜁니다.")
                    print("💡 수동으로 마이그레이션하거나 데이터를 백업 후 재생성하세요.")
        
        # 누락된 컬럼 추가
        columns_to_add = {
            'is_default_hdd': 'BOOLEAN DEFAULT FALSE',
            'is_default_ssd': 'BOOLEAN DEFAULT FALSE',
            'is_system_default': 'BOOLEAN DEFAULT FALSE'
        }
        
        for column_name, column_def in columns_to_add.items():
            if column_name not in existing_columns:
                print(f"➕ {column_name} 컬럼 추가 중...")
                cursor.execute(f"ALTER TABLE datastores ADD COLUMN {column_name} {column_def};")
                print(f"✅ {column_name} 컬럼 추가 완료")
            else:
                print(f"✅ {column_name} 컬럼 이미 존재")
        
        # shared 컬럼이 있으면 제거 (모델에 없음)
        if 'shared' in existing_columns:
            print("🗑️  shared 컬럼 제거 중... (모델에 없음)")
            cursor.execute("ALTER TABLE datastores DROP COLUMN IF EXISTS shared;")
            print("✅ shared 컬럼 제거 완료")
        
        # type 컬럼이 NOT NULL인지 확인
        cursor.execute("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'datastores' AND column_name = 'type';
        """)
        type_nullable = cursor.fetchone()
        if type_nullable and type_nullable[0] == 'YES':
            print("🔧 type 컬럼을 NOT NULL로 변경 중...")
            cursor.execute("ALTER TABLE datastores ALTER COLUMN type SET NOT NULL;")
            print("✅ type 컬럼 NOT NULL 설정 완료")
        
        # 최종 테이블 구조 확인
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'datastores'
            ORDER BY ordinal_position;
        """)
        final_columns = cursor.fetchall()
        
        print("\n📋 최종 테이블 구조:")
        for col_name, col_type, is_nullable in final_columns:
            nullable = "NULL" if is_nullable == 'YES' else "NOT NULL"
            print(f"  - {col_name}: {col_type} ({nullable})")
        
        conn.close()
        print("\n🎉 Datastores 테이블 스키마 수정 완료!")
        
    except Exception as e:
        print(f"❌ 스키마 수정 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    fix_datastores_schema()

