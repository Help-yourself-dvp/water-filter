# Файлы, которые нужно перенести в .github/workflows/

## release.yml — релизная сборка APK для магазина

Файл лежит здесь **временно**, потому что автоматизация не имеет права
создавать файлы в каталоге `.github/workflows/` без отдельного разрешения GitHub.

Пока файл лежит в `ci/`, он **не работает** — GitHub Actions видит только
`.github/workflows/`.

Как включить (любой из двух способов):

**Способ 1 — попросить AI.** Написать в диалоге: «подключись к репозиторию через device flow».
AI выдаст короткий код и ссылку https://github.com/login/device — после подтверждения
он перенесёт файл сам.

**Способ 2 — вручную через сайт GitHub.**

1. Открыть https://github.com/Help-yourself-dvp/water-filter/blob/main/ci/release.yml
2. Нажать кнопку «Raw», выделить весь текст, скопировать.
3. Открыть https://github.com/Help-yourself-dvp/water-filter/new/main
4. В поле имени файла ввести: `.github/workflows/release.yml`
5. Вставить скопированный текст.
6. Внизу нажать «Commit changes».
7. Удалить `ci/release.yml`, чтобы не было двух копий.

После этого в разделе Actions появится workflow **Build Release APK (RuStore)**.
