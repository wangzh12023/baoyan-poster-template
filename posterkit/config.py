"""读取并校验 poster.yaml，补全默认值。

YAML 里所有标量都按「文字」读：18:30 不会变成 1110，10.20 不会变成 10.2，不必到处加引号。"""
import re
from pathlib import Path

import yaml


class ConfigError(Exception):
    pass


class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag == "tag:yaml.org,2002:null"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

MAX_SPEAKERS = 5
DEFAULT_LABELS = dict(time=["时间", "TIME"], venue=["地点", "LOCATION"], organizer=["主办", "ORGANIZER"])
_RANGE = re.compile(r"(\d{1,2}[:：]\d{2})\s*[-–—~～至到]+\s*(\d{1,2}[:：]\d{2})")


def _range(s):
    """18:30-19:40 / 18:30~19:40 / 18：30 至 19：40 → 18:30 – 19:40"""
    return _RANGE.sub(lambda m: f"{m.group(1).replace('：', ':')} – {m.group(2).replace('：', ':')}", s)


def _text(v, where, required=False, raw=False):
    """取一段文字；raw=True 时原样保留（链接、文件名、颜色），否则顺手规范时间段写法"""
    if v is None or (isinstance(v, str) and not v.strip()):
        if required:
            raise ConfigError(f"poster.yaml 缺少「{where}」")
        return ""
    if isinstance(v, (list, dict)):
        raise ConfigError(f"「{where}」应该是一段文字")
    s = str(v).strip()
    return s if raw else _range(s)


def _pair(v, where, default):
    if v is None:
        return list(default)
    if isinstance(v, str):
        return [v, ""]
    if isinstance(v, list) and 1 <= len(v) <= 2:
        return [_text(x, where) for x in v] + ([""] if len(v) == 1 else [])
    raise ConfigError(f"「{where}」写成 [中文, 英文] 两项")


def _footnote(v, where):
    """场次末尾的小字：{time, text} 或一整句「19:40 – 20:00 中场休息」"""
    if v is None:
        return None
    if isinstance(v, dict):
        return dict(time=_text(v.get("time"), f"{where}.time"), text=_text(v.get("text"), f"{where}.text"))
    s = _text(v, where)
    m = re.match(r"\s*(\d{1,2}:\d{2} – \d{1,2}:\d{2})\s*(.*)", s)
    return dict(time=m.group(1), text=m.group(2)) if m else dict(time="", text=s)


def _file(v, base, where):
    if not v:
        return None
    p = (base / str(v)).resolve()
    if not p.exists():
        raise ConfigError(f"「{where}」指向的文件不存在：{p}")
    return p


def load(path):
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"找不到配置文件 {path}")
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"{path.name} 不是合法的 YAML（多半是缩进或冒号的问题）：\n{e}") from None
    base = path.parent.resolve()
    c = dict(base=base)

    c["year"] = _text(raw.get("year"), "year")
    c["title"] = _text(raw.get("title"), "title", required=True)
    sub = raw.get("subtitle") or []
    c["subtitle"] = [_text(s, "subtitle") for s in ([sub] if isinstance(sub, str) else sub)][:2]
    c["date"] = _text(raw.get("date"), "date", required=True)
    c["weekday"] = _text(raw.get("weekday"), "weekday")
    c["time"] = _text(raw.get("time"), "time")
    c["venue"] = _text(raw.get("venue"), "venue")

    sessions = raw.get("sessions") or []
    if len(sessions) != 2:
        raise ConfigError(f"sessions 需要正好 2 个场次（两栏版式），现在是 {len(sessions)} 个")
    c["sessions"] = []
    for si, s in enumerate(sessions, 1):
        where = f"sessions 第 {si} 场"
        speakers = s.get("speakers") or []
        if not 1 <= len(speakers) <= MAX_SPEAKERS:
            raise ConfigError(f"{where}：每场 1–{MAX_SPEAKERS} 位嘉宾，现在是 {len(speakers)} 位")
        c["sessions"].append(dict(
            name=_text(s.get("name"), f"{where}.name"),
            time=_text(s.get("time"), f"{where}.time"),
            footnote=_footnote(s.get("footnote"), f"{where}.footnote"),
            speakers=[dict(
                name=_text(p.get("name"), f"{where} 嘉宾 {pi}.name", required=True),
                time=_text(p.get("time"), f"{where} 嘉宾 {pi}.time"),
                school=_text(p.get("school"), f"{where} 嘉宾 {pi}.school"),
                dept=_text(p.get("dept"), f"{where} 嘉宾 {pi}.dept"),
                topic=_text(p.get("topic"), f"{where} 嘉宾 {pi}.topic"),
                tag=_text(p.get("tag"), f"{where} 嘉宾 {pi}.tag"),
            ) for pi, p in enumerate(speakers, 1)],
        ))

    f = raw.get("footer") or {}
    c["footer"] = dict(date=_text(f.get("date"), "footer.date"),
                       time=_text(f.get("time"), "footer.time") or c["time"],
                       venue=_text(f.get("venue"), "footer.venue") or c["venue"],
                       note=_text(f.get("note"), "footer.note"))
    lab = raw.get("labels") or {}
    c["labels"] = {k: _pair(lab.get(k), f"labels.{k}", d) for k, d in DEFAULT_LABELS.items()}

    lg = raw.get("logo")
    if isinstance(lg, str):
        lg = dict(file=lg)
    if lg:
        lines = lg.get("text") or []
        c["logo"] = dict(file=_file(lg.get("file"), base, "logo.file"),
                         color=_text(lg.get("color"), "logo.color", raw=True) or "keep",
                         text=[_text(t, "logo.text") for t in ([lines] if isinstance(lines, str) else lines)])
        if not c["logo"]["file"] and not c["logo"]["text"]:
            c["logo"] = None
    else:
        c["logo"] = None

    q = raw.get("qr")
    if isinstance(q, str):
        q = dict(url=q)
    if q:
        c["qr"] = dict(url=_text(q.get("url"), "qr.url", raw=True), image=_file(q.get("image"), base, "qr.image"),
                       style=_text(q.get("style"), "qr.style", raw=True) or "dots",
                       title=_pair([q.get("title", "交流群"), q.get("title_en", "")], "qr.title", ["", ""]),
                       id_label=_text(q.get("id_label"), "qr.id_label"), id=_text(q.get("id"), "qr.id"))
        if not c["qr"]["url"] and not c["qr"]["image"]:
            raise ConfigError("qr 需要 url（二维码内容）或 image（现成的二维码图片），不需要二维码就删掉整个 qr 段")
        if c["qr"]["style"] not in ("dots", "square"):
            raise ConfigError("qr.style 只能是 dots（圆点）或 square（方块）")
    else:
        c["qr"] = None

    c["fonts"] = raw.get("fonts") or {}
    return c
