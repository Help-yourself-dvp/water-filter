# Обновление build.yml до версии 1.0.27

Как обычно, GitHub не даёт менять файлы сборки автоматически — нужны
ручные правки.

В этот раз правок **три**: две короткие и одна замена большого блока.

Ветка:

```
arena/019fb764-water-filter
```

---

## Что добавляет версия 1.0.27

**1. Исправлен баг, который вы нашли.**

Кнопка «Открыть настройку» в пункте про батарею ничего не делала,
если разрешение уже выдано. Причина в самом Android: системный запрос
`ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` — это именно *запрос
разрешения*, и когда разрешение уже есть, система молча его игнорирует.

Теперь приложение сначала проверяет состояние: если разрешение уже
выдано, открывается общий список настроек батареи, где настройку можно
посмотреть и при желании изменить.

**2. Добавлена проверка разрешения на показ уведомлений.**

То самое окно «Разрешить уведомления?» при первом запуске. Если
пользователь случайно нажал «Запретить», раньше это никак нельзя было
исправить из приложения. Теперь это пункт 1 в списке настройки.

**3. Перестроен интерфейс** (только `index.html`, уже загружен).

---

## Откройте файл в редакторе

```
https://github.com/Help-yourself-dvp/water-filter/edit/arena/019fb764-water-filter/.github/workflows/build.yml
```

---

## Правка 1 — номер версии

Это **строки 50 и 51**.

**Было:**

```
          sed -i 's/versionCode 1/versionCode 27/g' android/app/build.gradle
          sed -i 's/versionName "1.0"/versionName "1.0.26"/g' android/app/build.gradle
```

**Стало:**

```
          sed -i 's/versionCode 1/versionCode 28/g' android/app/build.gradle
          sed -i 's/versionName "1.0"/versionName "1.0.27"/g' android/app/build.gradle
```

---

## Правка 2 — замена блока MainActivity

Изменений в Java-коде несколько и они разбросаны по файлу, поэтому
надёжнее заменить весь блок целиком, а не искать каждое место.

**Что удалить: строки с 63 по 297 включительно.**

Строка 63 — начало блока (`Ctrl + F`, введите `Patch MainActivity`):

```
      - name: Patch MainActivity (alarms, battery, backup, settings bridge)
```

Строка 297 — конец блока, выглядит так:

```
          EOF
```

Проверьте себя: сразу после строки 297 идёт пустая строка 298,
а затем строка 299:

```
      - name: Patch manifest and icons
```

Строку 299 и всё, что ниже, **не трогаем**.

**Вставьте на место удалённого блока:**

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

          import androidx.core.app.NotificationManagerCompat;

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
                                /* Производитель устройства — для подсказки по автозапуску */
                  @JavascriptInterface
                  public String getManufacturer() {
                      try {
                          return Build.MANUFACTURER == null ? "" : Build.MANUFACTURER;
                      } catch (Exception e) {
                          return "";
                      }
                  }

                  /* Разрешены ли уведомления */
                  @JavascriptInterface
                  public boolean areNotificationsEnabled() {
                      try {
                          return NotificationManagerCompat.from(MainActivity.this).areNotificationsEnabled();
                      } catch (Exception e) {
                          return true;
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

                            /* ===== Экраны системных настроек ===== */

              private void openSettings(String which) {
                  if ("battery".equals(which)) {
                      /*
                       * ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS — это запрос
                       * разрешения. Если оно уже выдано, Android молча игнорирует
                       * запрос и ничего не открывает. Поэтому в этом случае сразу
                       * показываем экран со списком, где настройку можно изменить.
                       */
                      boolean granted = false;
                      try {
                          PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                          granted = pm != null && pm.isIgnoringBatteryOptimizations(getPackageName());
                      } catch (Exception e) {
                      }

                      if (!granted) {
                          if (tryStart(new Intent(
                                  Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                                  Uri.parse("package:" + getPackageName())))) return;
                      }

                      if (tryStart(new Intent(
                              Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))) return;
                      openAppDetails();
                      return;
                  }

                  if ("notifications".equals(which)) {
                      if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                          Intent i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS);
                          i.putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName());
                          if (tryStart(i)) return;
                      }
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

⚠️ Отступы критичны — копируйте блок целиком, вместе с пробелами
в начале строк.

---

## Правка 3 — имя файла APK

В конце файла (`Ctrl + F`, введите `Rename APK`) замените
`v1.0.26-build27` на `v1.0.27-build28` в **четырёх местах**:

**Было:**

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

**Стало:**

```
      - name: Rename APK
        run: |
          cp android/app/build/outputs/apk/debug/app-debug.apk \
             android/app/build/outputs/apk/debug/AquaControlPro-v1.0.27-build28.apk

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: AquaControlPro-v1.0.27-build28
          path: android/app/build/outputs/apk/debug/AquaControlPro-v1.0.27-build28.apk
```

---

## Сохранение

1. **Commit changes...**
2. Сообщение:
   ```
   build.yml: исправление кнопки батареи и проверка уведомлений (1.0.27 build 28)
   ```
3. Проверьте, что выбрано
   **Commit directly to the `arena/019fb764-water-filter` branch**.
4. **Commit changes**.

---

## Сборка

1. `https://github.com/Help-yourself-dvp/water-filter/actions`
2. **Build Native Android APK** → **Run workflow** →
   ветка `arena/019fb764-water-filter` → зелёная кнопка.
3. Дождитесь ✅ и скачайте `AquaControlPro-v1.0.27-build28`.

---

## Проверка на телефоне

### Исправленный баг

1. Откройте **⚙️ Настройки** → **Настройка уведомлений**.
2. В пункте 2 (батарея) должна стоять зелёная отметка
   **✓ Уже разрешено**.
3. Нажмите **«Открыть настройку»** — теперь должен открыться
   системный список настроек батареи (раньше не открывалось ничего).

### Разрешение на уведомления

4. В пункте 1 «Показ уведомлений» должна стоять отметка
   **✓ Уже разрешено**.
5. Для полной проверки: отключите уведомления приложения в настройках
   Android, вернитесь — отметка должна пропасть, а в разделе
   «Настройки» подпись изменится на «Уведомления запрещены».

### Новый интерфейс

6. Внизу карточки вместо четырёх больших кнопок — строка из четырёх
   значков: **Изменить · Добавить · Настройки · Удалить**.
7. Главный экран должен помещаться **без прокрутки**.
8. Значок **⚙️ Настройки** открывает раздел с уведомлениями
   и резервными копиями.
9. Проверьте, что экспорт и импорт из нового раздела работают.
10. Свайп между домами и точки внизу работают как раньше.

---

## Что дальше

После проверки — вливаем всё в `main` через Pull Request,
чтобы вернуть автосборку. Затем беремся за вкладку «Пей воду».
