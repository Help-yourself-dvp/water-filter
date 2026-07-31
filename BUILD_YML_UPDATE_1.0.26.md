# Обновление build.yml до версии 1.0.26

Как и в прошлый раз, GitHub не разрешает мне менять файлы в папке
`.github/workflows/` автоматически. Нужно внести правки вручную.

В этот раз правок **четыре**, но все они простые: три коротких
и две вставки готового текста.

Все изменения — в ветке:

```
arena/019fb764-water-filter
```

---

## Что добавляет версия 1.0.26

Экран «Настроить уведомления»: приложение само определяет
производителя телефона, показывает инструкцию именно для этой
прошивки и открывает нужный экран настроек одной кнопкой.

Это решает проблему, которую вы обнаружили при тестировании:
без разрешения на автозапуск уведомления после перезагрузки не приходят.

Файлы `index.html`, `PROJECT.md` и `README.md` уже обновлены и загружены.

---

## Откройте файл в редакторе

Скопируйте ссылку в адресную строку браузера:

```
https://github.com/Help-yourself-dvp/water-filter/edit/arena/019fb764-water-filter/.github/workflows/build.yml
```

Вы сразу попадёте в редактор нужного файла в нужной ветке.

---

## Правка 1 — номер версии

Это **строки 50 и 51**.

**Было:**

```
          sed -i 's/versionCode 1/versionCode 26/g' android/app/build.gradle
          sed -i 's/versionName "1.0"/versionName "1.0.25"/g' android/app/build.gradle
```

**Стало:**

```
          sed -i 's/versionCode 1/versionCode 27/g' android/app/build.gradle
          sed -i 's/versionName "1.0"/versionName "1.0.26"/g' android/app/build.gradle
```

Меняются два числа: `26` → `27` и `1.0.25` → `1.0.26`.

---

## Правка 2 — вставка методов моста

Найдите **строку 110** (`Ctrl + F`, введите `public class BackupBridge`):

```
              public class BackupBridge {
```

Сразу под ней идёт строка 111:

```
                  @JavascriptInterface
```

Поставьте курсор **в конец строки 110**, нажмите Enter
и вставьте следующий текст:

```java
                  /* Производитель устройства — для подсказки по автозапуску */
                  @JavascriptInterface
                  public String getManufacturer() {
                      try {
                          return Build.MANUFACTURER == null ? "" : Build.MANUFACTURER;
                      } catch (Exception e) {
                          return "";
                      }
                  }

                  /* Выключены ли оптимизации батареи для приложения */
                  @JavascriptInterface
                  public boolean isBatteryOptimizationIgnored() {
                      try {
                          PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                          return pm != null && pm.isIgnoringBatteryOptimizations(getPackageName());
                      } catch (Exception e) {
                          return true;
                      }
                  }

                  /* Открыть нужный экран системных настроек */
                  @JavascriptInterface
                  public void openSettingsScreen(final String which) {
                      runOnUiThread(new Runnable() {
                          @Override
                          public void run() {
                              openSettings(which);
                          }
                      });
                  }
```

После вставки строка `@JavascriptInterface` и `public void saveBackup(...)`
должны остаться на месте, ниже вставленного текста.

Ничего удалять не нужно — только вставить.

---

## Правка 3 — вставка методов настроек

Найдите строку (`Ctrl + F`, введите `===== Разрешения`):

```
              /* ===== Разрешения ===== */
```

До правки 2 это была строка 177, после вставки она сместилась вниз —
ищите по тексту.

Поставьте курсор **в начало этой строки**
и вставьте следующий текст, а затем нажмите Enter,
чтобы `/* ===== Разрешения ===== */` осталась на отдельной строке ниже:

```java
              /* ===== Экраны системных настроек ===== */

              private void openSettings(String which) {
                  if ("battery".equals(which)) {
                      if (tryStart(new Intent(
                              Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                              Uri.parse("package:" + getPackageName())))) return;
                      openAppDetails();
                      return;
                  }
                  if ("autostart".equals(which)) {
                      if (tryAutostart()) return;
                      openAppDetails();
                      return;
                  }
                  openAppDetails();
              }

              private boolean tryAutostart() {
                  String[][] targets = new String[][] {
                      { "com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity" },
                      { "com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity" },
                      { "com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity" },
                      { "com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity" },
                      { "com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity" },
                      { "com.oppo.safe", "com.oppo.safe.permission.startup.StartupAppListActivity" },
                      { "com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity" },
                      { "com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity" },
                      { "com.samsung.android.lool", "com.samsung.android.sm.ui.battery.BatteryActivity" },
                      { "com.letv.android.letvsafe", "com.letv.android.letvsafe.AutobootManageActivity" },
                      { "com.asus.mobilemanager", "com.asus.mobilemanager.entry.FunctionActivity" }
                  };
                  for (String[] t : targets) {
                      Intent i = new Intent();
                      i.setClassName(t[0], t[1]);
                      if (tryStart(i)) return true;
                  }
                  return false;
              }

              private void openAppDetails() {
                  tryStart(new Intent(
                          Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                          Uri.parse("package:" + getPackageName())));
              }

              /*
               * На Android 11+ resolveActivity часто возвращает null из-за
               * ограничений видимости пакетов, поэтому просто пробуем запустить
               * и ловим исключение.
               */
              private boolean tryStart(Intent intent) {
                  try {
                      intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                      startActivity(intent);
                      return true;
                  } catch (Exception e) {
                      return false;
                  }
              }
```

Проще так: встаньте в начало строки `/* ===== Разрешения ===== */`,
нажмите Enter один раз (строка уедет вниз), поднимитесь на пустую
строку выше и вставьте текст туда.

Опять же — ничего не удаляем, только вставляем.

---

## Правка 4 — имя файла APK

В самом конце файла (`Ctrl + F`, введите `Rename APK`)
замените `v1.0.25-build26` на `v1.0.26-build27` в **четырёх местах**:

**Было:**

```
      - name: Rename APK
        run: |
          cp android/app/build/outputs/apk/debug/app-debug.apk \
             android/app/build/outputs/apk/debug/AquaControlPro-v1.0.25-build26.apk

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: AquaControlPro-v1.0.25-build26
          path: android/app/build/outputs/apk/debug/AquaControlPro-v1.0.25-build26.apk
```

**Стало:**

```
      - name: Rename APK
        run: |
          cp android/app/build/outputs/apk/debug/app-debug.apk \
             android/app/build/outputs/apk/debug/AquaControlPro-v1.0.26-build27.apk

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: AquaControlPro-v1.0.26-build27
          path: android/app/build/outputs/apk/debug/AquaControlPro-v1.0.26-build27.apk
```

---

## Сохранение

1. Нажмите зелёную кнопку **Commit changes...**
2. В поле сообщения напишите:
   ```
   build.yml: помощник настройки разрешений (1.0.26 build 27)
   ```
3. Убедитесь, что выбрано
   **Commit directly to the `arena/019fb764-water-filter` branch**.
4. Нажмите **Commit changes**.

---

## Сборка

1. Откройте `https://github.com/Help-yourself-dvp/water-filter/actions`
2. Слева выберите **Build Native Android APK**.
3. Нажмите **Run workflow**, выберите ветку
   `arena/019fb764-water-filter`, нажмите зелёную кнопку.
4. Дождитесь зелёной галочки ✅ (5–10 минут).
5. Скачайте артефакт `AquaControlPro-v1.0.26-build27`.

Если сборка упала с красным крестиком ❌ — чаще всего это
съехавшие отступы при вставке. Пришлите текст ошибки.

---

## Проверка на телефоне

Установите APK поверх текущей версии.

1. **Важно для теста:** сначала зайдите в настройки телефона
   и **отзовите** ранее выданные разрешения на автозапуск —
   иначе экран не появится, он показывается только когда
   разрешений нет.
2. Запустите приложение. Через секунду должен появиться экран
   **«Чтобы напоминания приходили»**.
3. Проверьте, что подсказка внизу соответствует вашему телефону.
4. Нажмите **«Открыть настройку»** в пункте 1 — должно открыться
   системное окно про батарею.
5. Разрешите, вернитесь в приложение — в пункте 1 должна появиться
   зелёная отметка **✓ Уже разрешено**.
6. Нажмите **«Открыть настройку»** в пункте 2 — должен открыться
   экран автозапуска (на вашей прошивке) или общие настройки приложения.
7. Нажмите **Готово**.
8. Перезапустите приложение — экран больше не должен появляться.
9. Внизу нажмите **🔔 Настроить уведомления** — экран должен
   открыться снова.

---

## Что дальше

После проверки версия 1.0.26 становится стабильной,
и её имеет смысл влить в ветку `main` через Pull Request,
чтобы вернуть автоматическую сборку.
