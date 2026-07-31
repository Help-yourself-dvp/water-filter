# Шаг вручную: обновление build.yml (версия 1.0.25)

Файл `.github/workflows/build.yml` **не удалось изменить автоматически**.

GitHub запрещает приложениям (в том числе этому) редактировать файлы сборки
в папке `.github/workflows/` без специального разрешения. Это защита GitHub,
а не ошибка проекта.

Поэтому три небольших правки нужно внести вручную через сайт GitHub.
Ниже — подробная инструкция. Все остальные файлы (index.html, PROJECT.md,
README.md) уже обновлены и загружены.

**Важно:** без этих правок новая функция сохранения в файл работать не будет —
приложение покажет старое окно с текстом.

---

## Как открыть файл для редактирования

1. Откройте в браузере репозиторий:
   `https://github.com/Help-yourself-dvp/water-filter`
2. Вверху слева нажмите на выпадающий список веток (там написано `main`).
3. Выберите ветку:
   ```
   arena/019fb764-water-filter
   ```
4. Нажмите на папку `.github`, затем на папку `workflows`.
5. Нажмите на файл `build.yml`.
6. В правом верхнем углу нажмите на значок карандаша ✏️ (Edit this file).

Теперь вы находитесь в редакторе. Выполните правки 1, 2 и 3.

---

## Правка 1 — номер версии

Найдите две строки (примерно строка 50). Для поиска нажмите `Ctrl + F`
и введите `versionCode`.

**Было:**

```
          sed -i 's/versionCode 1/versionCode 25/g' android/app/build.gradle
          sed -i 's/versionName "1.0"/versionName "1.0.24"/g' android/app/build.gradle
```

**Заменить на:**

```
          sed -i 's/versionCode 1/versionCode 26/g' android/app/build.gradle
          sed -i 's/versionName "1.0"/versionName "1.0.25"/g' android/app/build.gradle
```

Меняются только два числа: `25` → `26` и `1.0.24` → `1.0.25`.

---

## Правка 2 — код MainActivity (главная правка)

Это самая большая правка. Здесь добавляется нативный код,
который открывает системное окно сохранения файла Android.

Найдите строку (`Ctrl + F`, введите `Patch MainActivity`):

```
      - name: Patch MainActivity for exact alarms and battery optimization
```

Выделите **весь блок** начиная с этой строки и заканчивая строкой,
которая идет прямо перед:

```
      - name: Patch manifest and icons
```

То есть удаляется всё от `- name: Patch MainActivity ...`
до строки `          EOF` включительно (это примерно 55 строк).

Строку `- name: Patch manifest and icons` **удалять не нужно**.

**Вставьте вместо удалённого блока следующий текст:**

```yaml
      - name: Patch MainActivity (alarms, battery, backup save bridge)
        run: |
          mkdir -p android/app/src/main/java/com/aquacontrol/pro
          cat > android/app/src/main/java/com/aquacontrol/pro/MainActivity.java << 'EOF'
          package com.aquacontrol.pro;

          import android.app.AlarmManager;
          import android.content.Intent;
          import android.net.Uri;
          import android.os.Build;
          import android.os.Bundle;
          import android.os.PowerManager;
          import android.provider.Settings;
          import android.webkit.JavascriptInterface;
          import android.webkit.WebView;

          import com.getcapacitor.BridgeActivity;

          import org.json.JSONObject;

          import java.io.OutputStream;

          public class MainActivity extends BridgeActivity {

              private static final int REQ_SAVE_BACKUP = 7301;
              private String pendingBackupJson = null;

              @Override
              protected void onCreate(Bundle savedInstanceState) {
                  super.onCreate(savedInstanceState);
                  requestExactAlarmPermission();
                  requestIgnoreBatteryOptimizations();
                  installBackupBridge();
              }

              /* ===== Сохранение резервной копии через системное окно Android ===== */

              private void installBackupBridge() {
                  try {
                      WebView wv = getBridge().getWebView();
                      if (wv != null) {
                          wv.addJavascriptInterface(new BackupBridge(), "AquaExport");
                      }
                  } catch (Exception e) {
                  }
              }

              public class BackupBridge {
                  @JavascriptInterface
                  public void saveBackup(final String json, final String fileName) {
                      pendingBackupJson = json;
                      final String name = (fileName == null || fileName.length() == 0)
                              ? "aquacontrol-backup.json"
                              : fileName;
                      runOnUiThread(new Runnable() {
                          @Override
                          public void run() {
                              try {
                                  Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                                  intent.addCategory(Intent.CATEGORY_OPENABLE);
                                  intent.setType("application/json");
                                  intent.putExtra(Intent.EXTRA_TITLE, name);
                                  startActivityForResult(intent, REQ_SAVE_BACKUP);
                              } catch (Exception e) {
                                  pendingBackupJson = null;
                                  notifyBackupResult(false, "Системное окно сохранения недоступно");
                              }
                          }
                      });
                  }
              }

              @Override
              protected void onActivityResult(int requestCode, int resultCode, Intent data) {
                  if (requestCode == REQ_SAVE_BACKUP) {
                      String json = pendingBackupJson;
                      pendingBackupJson = null;
                      Uri uri = (data == null) ? null : data.getData();
                      if (resultCode == RESULT_OK && uri != null && json != null) {
                          OutputStream os = null;
                          try {
                              os = getContentResolver().openOutputStream(uri, "w");
                              os.write(json.getBytes("UTF-8"));
                              os.flush();
                              notifyBackupResult(true, "Резервная копия сохранена");
                          } catch (Exception e) {
                              notifyBackupResult(false, "Не удалось записать файл");
                          } finally {
                              try { if (os != null) os.close(); } catch (Exception e2) { }
                          }
                      } else {
                          notifyBackupResult(false, "Сохранение отменено");
                      }
                      return;
                  }
                  super.onActivityResult(requestCode, resultCode, data);
              }

              private void notifyBackupResult(final boolean ok, final String message) {
                  runOnUiThread(new Runnable() {
                      @Override
                      public void run() {
                          try {
                              WebView wv = getBridge().getWebView();
                              if (wv == null) return;
                              String js = "window.onBackupSaveResult && window.onBackupSaveResult("
                                      + ok + "," + JSONObject.quote(message) + ");";
                              wv.evaluateJavascript(js, null);
                          } catch (Exception e) {
                          }
                      }
                  });
              }

              /* ===== Разрешения ===== */

              private void requestExactAlarmPermission() {
                  if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                      try {
                          AlarmManager am = (AlarmManager) getSystemService(ALARM_SERVICE);
                          if (am != null && !am.canScheduleExactAlarms()) {
                              Intent intent = new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM);
                              intent.setData(Uri.parse("package:" + getPackageName()));
                              startActivity(intent);
                          }
                      } catch (Exception e) {
                      }
                  }
              }

              private void requestIgnoreBatteryOptimizations() {
                  try {
                      PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                      if (pm != null && !pm.isIgnoringBatteryOptimizations(getPackageName())) {
                          Intent intent = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                          intent.setData(Uri.parse("package:" + getPackageName()));
                          startActivity(intent);
                      }
                  } catch (Exception e) {
                  }
              }
          }
          EOF
```

⚠️ Отступы очень важны. Проще всего: скопируйте текст выше целиком
(вместе с пробелами в начале строк) и вставьте его в редактор.

---

## Правка 3 — имя файла APK

Найдите в самом конце файла (`Ctrl + F`, введите `Rename APK`):

**Было:**

```
      - name: Rename APK
        run: |
          cp android/app/build/outputs/apk/debug/app-debug.apk \
             android/app/build/outputs/apk/debug/AquaControlPro-v1.0.24-build25.apk

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: AquaControlPro-v1.0.24-build25
          path: android/app/build/outputs/apk/debug/AquaControlPro-v1.0.24-build25.apk
```

**Заменить на:**

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

Меняется только `v1.0.24-build25` на `v1.0.25-build26` в четырёх местах.

---

## Сохранение изменений

1. Нажмите зелёную кнопку **Commit changes...** в правом верхнем углу.
2. В поле **Commit message** напишите:
   ```
   build.yml: экспорт резервной копии в файл (1.0.25 build 26)
   ```
3. Убедитесь, что выбран пункт
   **Commit directly to the `arena/019fb764-water-filter` branch**.
4. Нажмите **Commit changes**.

---

## Проверка сборки

1. Перейдите на вкладку **Actions** вверху страницы репозитория.
2. Слева выберите **Build Native Android APK**.
3. Если сборка не запустилась сама, нажмите **Run workflow**,
   выберите ветку `arena/019fb764-water-filter` и нажмите зелёную кнопку.
4. Дождитесь окончания (обычно 5–10 минут).
5. Должна появиться зелёная галочка ✅.
6. Откройте завершившуюся сборку и внизу в разделе **Artifacts**
   скачайте файл:
   ```
   AquaControlPro-v1.0.25-build26
   ```

Если сборка завершилась с красным крестиком ❌ — откройте её,
нажмите на шаг с ошибкой и пришлите текст ошибки.

---

## Проверка приложения на телефоне

Установите APK поверх старой версии (удалять приложение не нужно).

Проверьте по порядку:

1. Приложение запускается, все объекты и фильтры на месте.
2. Внизу экрана разверните раздел **💾 Резервная копия**.
3. Нажмите **📤 Сохранить копию в файл**.
4. Должно открыться **системное окно Android** с выбором папки
   и уже подставленным именем файла вида
   `aquacontrol-backup-2026-07-31-1420.json`.
5. Сохраните файл (можно в «Загрузки» или на Google Диск).
6. Внизу появится сообщение **«Резервная копия сохранена»**.
7. Нажмите **📤 Сохранить копию в файл** ещё раз и нажмите «Назад».
   Должно появиться сообщение **«Сохранение отменено»**.
8. Нажмите **📥 Восстановить из файла**, выберите сохранённый файл
   и подтвердите. Данные должны загрузиться без ошибок.
9. Проверьте, что уведомления по-прежнему приходят.

Если на шаге 4 открылось старое окно с текстом — значит правка 2
применилась не полностью. Напишите об этом.

---

## Что делать дальше

После успешной проверки версия 1.0.25 считается стабильной.

Следующая задача по плану (PROJECT.md, раздел 24):
автоматическая публикация APK в GitHub Releases.
