from getpass import getpass
from werkzeug.security import generate_password_hash
from db import connect_db


def main():
    username = input('생성할 아이디 [operator]: ').strip() or 'operator'
    password = getpass('새 비밀번호 (12자 이상): ')
    confirm = getpass('비밀번호 다시 입력: ')
    if len(password) < 12 or password != confirm:
        raise SystemExit('12자 이상이며 두 번 입력한 값이 같아야 합니다. 다시 실행해 주세요.')
    with connect_db() as conn:
        result = conn.execute(
            'INSERT INTO users (username, password_hash) VALUES (%s, %s) '
            'ON CONFLICT (username) DO NOTHING',
            (username, generate_password_hash(password)),
        )
    if result.rowcount == 1:
        print(f'{username} 계정을 만들었습니다.')
    else:
        print(f'{username} 계정이 이미 있습니다. 기존 비밀번호를 유지합니다.')


if __name__ == '__main__':
    main()
