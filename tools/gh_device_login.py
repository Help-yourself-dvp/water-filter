#!/usr/bin/env python3
"""
Вход в GitHub через Device Flow — «код с экрана», как подключение телевизора.

Зачем: автоматизация Arena работает от имени GitHub App, у которого нет права
менять файлы в .github/workflows/ и запускать сборки. Device Flow даёт временный
ключ от имени владельца репозитория.

Как пользоваться:
    python3 tools/gh_device_login.py          — показать код и ждать подтверждения

Владелец открывает https://github.com/login/device, вводит код, нажимает Authorize.
Ключ сохраняется в /home/user/gh_access.json — ВНЕ репозитория, в git не попадает.
Отозвать доступ: https://github.com/settings/applications → GitHub CLI → Revoke access.
"""
import json, sys, time, urllib.parse, urllib.request

CLIENT_ID = '178c6fc778ccc68e1d6a'      # публичный client_id официального GitHub CLI
TOKEN_PATH = '/home/user/gh_access.json'


def post(url, params):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(),
                                 headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    d = post('https://github.com/login/device/code',
             {'client_id': CLIENT_ID, 'scope': 'repo workflow'})
    print('КОД:', d['user_code'])
    print('Открыть:', d['verification_uri'])
    print('Срок действия, мин:', round(d.get('expires_in', 900) / 60))
    sys.stdout.flush()

    interval = max(5, int(d.get('interval', 5)))
    deadline = time.time() + int(d.get('expires_in', 900)) - 10
    while time.time() < deadline:
        try:
            res = post('https://github.com/login/oauth/access_token', {
                'client_id': CLIENT_ID, 'device_code': d['device_code'],
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'})
        except Exception as e:
            print('сеть:', e, flush=True); time.sleep(interval); continue

        if res.get('access_token'):
            json.dump(res, open(TOKEN_PATH, 'w'))
            print('ГОТОВО, права:', res.get('scope', ''), flush=True)
            return 0
        err = res.get('error')
        if err == 'authorization_pending':
            print('ждём подтверждения...', flush=True)
        elif err == 'slow_down':
            interval += 5
        else:
            print('ОШИБКА:', err, flush=True)
            return 1
        time.sleep(interval)
    print('КОД ИСТЁК — запустите скрипт заново', flush=True)
    return 1


if __name__ == '__main__':
    sys.exit(main())
