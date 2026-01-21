#!/usr/bin/env python3
"""
기존 DB에서 admin 사용자에게 앱에서 사용하는 권한 키를 보정으로 추가합니다.

왜 필요한가?
- 과거 시드/스키마는 'server_create' 같은 레거시 키를 넣었는데,
  현재 UI/라우트는 'create_server' 같은 키를 검사합니다.
- admin role이라도 UI는 session['permissions']로만 버튼 노출을 제어하는 곳이 있어
  키 불일치가 있으면 "서버 생성 권한이 없습니다"가 표시될 수 있습니다.
"""

import os
import sys
import psycopg2


APP_PERMISSION_KEYS = [
    'view_all',
    'create_server', 'delete_server', 'start_server', 'stop_server', 'reboot_server',
    'manage_server',
    'manage_users',
    'assign_roles', 'remove_role',
    'manage_firewall_groups', 'assign_firewall_groups', 'remove_firewall_groups', 'manage_firewall',
    'backup_management',
    'manage_storage', 'manage_network',
    'view_logs',
]


def main() -> None:
    db_url = os.environ.get('DATABASE_URL', 'postgresql://proxmox:proxmox123@localhost:5432/proxmox_manager')

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT id, username, role FROM users WHERE username = 'admin'")
        row = cur.fetchone()
        if not row:
            print("❌ users 테이블에 admin 사용자가 없습니다.")
            sys.exit(1)

        admin_id, username, role = row
        print(f"✅ admin 확인: id={admin_id}, username={username}, role={role}")

        # role이 admin이 아니면 경고만 (강제 변경은 하지 않음)
        if role != 'admin':
            print("⚠️  admin 사용자의 role이 'admin'이 아닙니다. (현재 값:", role, ")")
            print("⚠️  UI/라우트의 관리자 우회 로직은 role=='admin' 기준입니다.")

        # 권한 추가
        inserted = 0
        for perm in APP_PERMISSION_KEYS:
            cur.execute(
                """
                INSERT INTO user_permissions (user_id, permission)
                VALUES (%s, %s)
                ON CONFLICT (user_id, permission) DO NOTHING
                """,
                (admin_id, perm),
            )
            # rowcount는 ON CONFLICT DO NOTHING에서 0/1로 동작
            inserted += int(cur.rowcount or 0)

        print(f"✅ admin 권한 보정 완료: 신규 추가 {inserted}개")

        cur.execute("SELECT permission FROM user_permissions WHERE user_id=%s ORDER BY permission", (admin_id,))
        perms = [r[0] for r in cur.fetchall()]
        print("📋 admin 현재 권한 목록:")
        for p in perms:
            print(" -", p)

        conn.close()
    except Exception as e:
        print(f"❌ 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


