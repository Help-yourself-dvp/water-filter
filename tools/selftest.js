/*
 * Быстрая самопроверка index.html без телефона и без браузера.
 *
 *   node tools/selftest.js
 *
 * Что проверяется:
 *   1. скрипт вообще загружается (нет опечаток, ломающих всё приложение);
 *   2. все функции из onclick существуют, все getElementById находят элементы;
 *   3. расчёт срока службы, работа с датами, экранирование текста;
 *   4. какие уведомления и на какое время реально планируются.
 *
 * Это дешёвая проверка перед сборкой APK. Она не заменяет проверку на телефоне,
 * но ловит большинство ошибок за секунду.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

let failed = 0;
function check(name, ok, extra) {
    console.log((ok ? '  OK   ' : '  СБОЙ ') + name + (extra ? '  → ' + extra : ''));
    if (!ok) failed++;
}
function eq(name, got, want) {
    check(name, String(got) === String(want), String(got) + (String(got) === String(want) ? '' : ' (ожидалось ' + want + ')'));
}

/* ------------------------------------------------ 1. статические проверки разметки */

console.log('\n[1] Разметка и связи');

const scripts = html.match(/<script>([\s\S]*?)<\/script>/g) || [];
const code = scripts.map(s => s.replace(/^<script>/, '').replace(/<\/script>$/, '')).join('\n');
check('найден блок <script>', scripts.length === 1, scripts.length + ' шт.');

const handlers = new Set([...html.matchAll(/on(?:click|change)="([A-Za-z_$][\w$]*)\(/g)].map(m => m[1]));
const defined = new Set([
    ...[...code.matchAll(/function\s+([A-Za-z_$][\w$]*)\s*\(/g)].map(m => m[1]),
    ...[...code.matchAll(/window\.([A-Za-z_$][\w$]*)\s*=/g)].map(m => m[1]),
]);
const missingFn = [...handlers].filter(h => !defined.has(h));
check('все функции из onclick существуют', missingFn.length === 0, missingFn.join(', '));

const idsHtml = new Set([...html.matchAll(/id="([\w-]+)"/g)].map(m => m[1]));
const idsJs = new Set([...code.matchAll(/getElementById\('([\w-]+)'\)/g)].map(m => m[1]));
const missingId = [...idsJs].filter(i => !idsHtml.has(i));
check('все getElementById находят элемент', missingId.length === 0, missingId.join(', '));

const verTag = (html.match(/id="appVersionTag">([^<]+)</) || [])[1] || '';
const version = JSON.parse(fs.readFileSync(path.join(root, 'version.json'), 'utf8'));
const expected = 'версия ' + version.versionName + ' (build ' + version.versionCode + ')';
check('версия в index.html совпадает с version.json', verTag.indexOf(expected) >= 0, verTag);

/* ------------------------------------------------ 2. запуск скрипта с заглушками */

console.log('\n[2] Запуск скрипта');

const store = {};
function fakeEl(id) {
    return {
        id, value: '', max: '', textContent: '', innerText: '', innerHTML: '',
        style: {}, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
        addEventListener() {}, getAttribute() { return null; }, setAttribute() {},
        focus() {}, select() {}, click() {}, appendChild() {}, remove() {},
        getContext() {
            return {
                clearRect() {}, beginPath() {}, arc() {}, fill() {}, moveTo() {}, lineTo() {},
                closePath() {}, set fillStyle(v) {}, get fillStyle() { return ''; }
            };
        }
    };
}
const scheduled = [];   // всё, что приложение попросило запланировать
let pending = [];       // «уже стоящие в очереди» уведомления — как на телефоне
global.document = {
    body: fakeEl('body'),
    getElementById: fakeEl,
    querySelectorAll: () => [],
    querySelector: () => null,
    createElement: () => fakeEl('tmp'),
    addEventListener: () => {},
    visibilityState: 'visible'
};
global.localStorage = {
    getItem: k => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: k => { delete store[k]; }
};
global.window = {
    addEventListener() {}, innerWidth: 400, innerHeight: 800,
    Capacitor: {
        Plugins: {
            LocalNotifications: {
                async requestPermissions() { return { display: 'granted' }; },
                async createChannel() {},
                async getPending() { return { notifications: pending.map(n => ({ id: n.id })) }; },
                async cancel(opts) {
                    const ids = new Set((opts.notifications || []).map(n => n.id));
                    pending = pending.filter(n => !ids.has(n.id));
                },
                async schedule(opts) {
                    scheduled.push(...opts.notifications);
                    pending = pending.concat(opts.notifications);
                },
                addListener() {}
            }
        }
    }
};
global.requestAnimationFrame = () => 0;
global.setInterval = () => 0;
try { Object.defineProperty(global, 'navigator', { value: { clipboard: null }, configurable: true }); } catch (e) {}

let api;
try {
    api = new Function(code + ';return {inputToTs, atHour, dateToInput, esc, getFilterTiming,' +
        ' notifyHour, peopleMult, appData, forceRescheduleAll, showToast, isFirstRun,' +
        ' wizardFinish, filterNameForType};')();
    check('скрипт загрузился без ошибок', true);
} catch (e) {
    check('скрипт загрузился без ошибок', false, e.message);
    process.exit(1);
}

/* ------------------------------------------------ 3. расчёты */

console.log('\n[3] Даты и расчёт срока');

const ts = api.inputToTs('2026-07-01', 0);
const d = new Date(ts);
eq('дата 2026-07-01 разобрана верно', d.getDate() + '.' + (d.getMonth() + 1), '1.7');
eq('время внутри дня = 12:00 (без сдвига часовых поясов)', d.getHours(), 12);
eq('пустое поле даты → запасное значение', api.inputToTs('', 555), 555);
check('дата из будущего обрезается до сегодня', api.inputToTs('2099-01-01', 0) <= Date.now());

const at = api.atHour(new Date(2026, 7, 20, 23, 40).getTime(), 10);
const ad = new Date(at);
eq('напоминание переносится на выбранный час', ad.getHours() + ':' + ad.getMinutes() + ' ' + ad.getDate(), '10:0 20');

const t = api.getFilterTiming({ baseDays: 90, cycleMs: null, people: 2, hardness: 1.25, lastDate: Date.now() });
eq('90 дн × 0.75 (2 чел) ÷ 1.25 (жёсткая вода) = 54 дн', Math.round(t.resourceMs / 86400000), 54);
eq('обычный фильтр не считается тестовым', t.isTest, false);

eq('пользовательский текст экранируется',
    api.esc('<b>"Дача" & Co\'s</b>'),
    '&lt;b&gt;&quot;Дача&quot; &amp; Co&#39;s&lt;/b&gt;');

console.log('\n[4] Настройки напоминаний');
eq('промежуток напоминания по умолчанию — утро (9:00)', api.notifyHour(), 9);
api.appData.settings.notifyHour = 20;
eq('произвольный час приводится к вечернему промежутку', api.notifyHour(), 19);
api.appData.settings.notifyHour = 9;
eq('предупреждение заранее по умолчанию, дней', api.appData.settings.preDays, 7);
eq('режим проверки выключен', api.appData.settings.devMode, false);

/* ------------------------------------------------ 5. первый запуск и мастер настройки */

console.log('\n[5] Первый запуск');
eq('пустое хранилище считается первым запуском', api.isFirstRun, true);
eq('демонстрационные дома не создаются', api.appData.locations.length, 0);
eq('демонстрационные фильтры не создаются', api.appData.filters.length, 0);
eq('название по типу фильтра', api.filterNameForType('Осмос'), 'Обратный осмос');

/* ------------------------------------------------ 6. реальное планирование уведомлений */

(async function () {
    console.log('\n[6] Мастер настройки');
    await api.wizardFinish();
    eq('мастер создал один объект', api.appData.locations.length, 1);
    eq('мастер создал один фильтр', api.appData.filters.length, 1);
    check('текущий фильтр выбран', !!api.appData.currentFilterId, api.appData.currentFilterId);

    console.log('\n[7] Планирование уведомлений');
    api.appData.filters = [{
        id: 'f_test', locationId: api.appData.locations[0].id, name: 'Кувшин', type: 'Кувшин',
        baseDays: 90, cycleMs: null, people: 1, hardness: 1,
        lastDate: Date.now(), brand: '', buyUrl: ''
    }];
    scheduled.length = 0;
    pending = [];
    await api.forceRescheduleAll();

    eq('запланировано уведомлений', scheduled.length, 3);
    const hours = scheduled.map(n => new Date(n.schedule.at).getHours());
    check('все уведомления в начале выбранного промежутка (9:00)', hours.every(h => h === 9), hours.join(', '));
    const days = scheduled
        .map(n => Math.round((new Date(n.schedule.at).getTime() - Date.now()) / 86400000))
        .sort((a, b) => a - b);
    eq('за 7 дней / в срок / через неделю после', days.join(' | '), '83 | 90 | 97');
    check('у всех уведомлений свой номер', new Set(scheduled.map(n => n.id)).size === 3);

    console.log('');
    if (failed) {
        console.log('ПРОВЕРКА НЕ ПРОЙДЕНА: ошибок — ' + failed);
        process.exit(1);
    }
    console.log('Все проверки пройдены.');
})();
