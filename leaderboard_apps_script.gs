// ═══════════════════════════════════════════════════════════════════════════
// Google Apps Script для доски трофеев Roguelike-CardGame
// ───────────────────────────────────────────────────────────────────────────
// КАК ПОДКЛЮЧИТЬ (один раз):
//   1. Открой свою Google-таблицу лидерборда.
//   2. Меню: Расширения → Apps Script.
//   3. Удали весь старый код, вставь ЭТОТ файл целиком.
//   4. Вверху нажми «Развернуть» → «Новое развёртывание» → тип «Веб-приложение».
//        • Описание: любое (напр. "leaderboard v2").
//        • Запуск от имени: «Я».
//        • У кого есть доступ: «Все» (Anyone). ← ВАЖНО, иначе игра не достучится.
//   5. Скопируй URL развёртывания (…/exec).
//   6. Если URL ИЗМЕНИЛСЯ — вставь его в managers/network_manager.py
//        (GOOGLE_SCRIPT_URL) и server.py. Если оставил то же развёртывание —
//        URL прежний, менять в коде ничего не нужно.
//
//   NB: при каждом изменении скрипта надо заново «Развернуть» (или «Управление
//       развёртываниями» → редактировать → новая версия), иначе правки не вступят.
//
// ЧТО ДЕЛАЕТ:
//   • doPost — принимает забег от игры (JSON), дописывает строку в лист, и в ОТВЕТ
//     отдаёт текущий ТОП (тот же формат, что doGet) — игра сразу видит обновление.
//   • doGet — отдаёт ТОП-N как JSON-массив объектов (читается при открытии доски).
//   • Оба отдают поле class → на клиенте дедуп склеит локальную и сетевую строку
//     одного забега (а не покажет дважды).
// ═══════════════════════════════════════════════════════════════════════════

// Сколько строк отдавать в доску.
var TOP_N = 50;

// Заголовки столбцов листа (первая строка). Порядок = порядок колонок A..E.
// Менять можно, но синхронно с полями ниже.
var HEADERS = ['username', 'class', 'max_floor', 'kills', 'max_damage'];


function _sheet() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  // Если лист пуст — проставим заголовки (чтобы getDataRange знал структуру).
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
  }
  return sh;
}


// Прочитать все забеги из листа как массив объектов, отсортировать и обрезать до TOP_N.
function _topRows() {
  var sh = _sheet();
  var last = sh.getLastRow();
  if (last < 2) return [];                       // только заголовок / пусто

  var values = sh.getRange(2, 1, last - 1, HEADERS.length).getValues();
  var rows = values.map(function (r) {
    return {
      username:   String(r[0] || '?'),
      'class':    String(r[1] || '—'),
      max_floor:  Number(r[2] || 0),
      kills:      Number(r[3] || 0),
      max_damage: Number(r[4] || 0)
    };
  });

  // Сорт: этаж↓, затем убийства↓, затем урон↓ (как в клиенте leaderboard_rows).
  rows.sort(function (a, b) {
    return (b.max_floor - a.max_floor)
        || (b.kills - a.kills)
        || (b.max_damage - a.max_damage);
  });

  return rows.slice(0, TOP_N);
}


function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}


// GET — отдать текущий ТОП доски.
function doGet(e) {
  return _json(_topRows());
}


// POST — принять забег, записать строку, вернуть обновлённый ТОП.
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sh = _sheet();
    sh.appendRow([
      String(data.username || '?'),
      String(data['class'] || '—'),     // ← класс ПИШЕМ, чтобы doGet его отдавал
      Number(data.max_floor || 0),
      Number(data.kills || 0),
      Number(data.max_damage || 0)
    ]);
    // В ответ — свежий ТОП (игра кладёт его в кэш доски сразу после смерти).
    return _json(_topRows());
  } catch (err) {
    return _json({ status: 'error', message: String(err) });
  }
}
