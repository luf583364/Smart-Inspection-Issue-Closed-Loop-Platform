"""Inspection report generation.

Each submitted inspection becomes ONE self-contained HTML file stored under
settings.REPORTS_DIR (default ./reports). Photos are embedded as base64 data
URIs so a downloaded report renders fully offline. The file is named after the
record_no (e.g. IR202606030003.html) so the folder is easy to browse.
"""

from __future__ import annotations

import base64
import html
import mimetypes
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.models.attachment import Attachment
from app.services import inspection_record_service
from app.utils.enums import AttachmentCategory

STATUS_LABEL_ZH = {
    "in_progress": "进行中（草稿）",
    "completed": "已完成",
    "pending_assign": "待转发",
    "pending_handle": "待处理",
    "handling": "处理中",
    "pending_verify": "待核实",
    "rejected": "已驳回",
}

SOURCE_LABEL_ZH = {"manual": "手动", "qr": "扫码"}


def reports_dir() -> Path:
    d = Path(settings.REPORTS_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def report_path(record_no: str) -> Path:
    safe = "".join(c for c in record_no if c.isalnum() or c in ("-", "_")) or "report"
    return reports_dir() / f"{safe}.html"


def _e(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _img_data_uri(file_path_rel: str | None) -> str | None:
    if not file_path_rel:
        return None
    p = Path(settings.UPLOAD_DIR) / file_path_rel
    if not p.is_file():
        return None
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    try:
        raw = p.read_bytes()
    except OSError:
        return None
    return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"


def _fmt_dt(value) -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value).replace("T", " ")[:16]


def _attachment_paths_by_eq(db: Session, record_id: int) -> dict[int, list[str]]:
    rows = db.execute(
        select(Attachment).where(
            Attachment.record_id == record_id,
            Attachment.category.in_([
                AttachmentCategory.INSPECTION_ABNORMAL.value,
                AttachmentCategory.ISSUE_BEFORE.value,
            ]),
        )
    ).scalars().all()
    out: dict[int, list[str]] = {}
    for a in rows:
        if a.equipment_id is None:
            continue
        out.setdefault(a.equipment_id, []).append(a.file_path)
    return out


def _render_html(detail: dict, att_paths: dict[int, list[str]]) -> str:
    room = detail["room"]
    inspector = detail["inspector"]
    eq_results = detail["equipment_results"]
    total = len(eq_results)
    normal_n = sum(1 for e in eq_results if e["result"] == "normal")
    abnormal_n = sum(1 for e in eq_results if e["result"] == "abnormal")

    status_zh = STATUS_LABEL_ZH.get(detail["status"], detail["status"])
    source_zh = SOURCE_LABEL_ZH.get(detail["source"], detail["source"])
    has_issue_zh = "是" if detail["has_issue"] else "否"

    meta_rows = [
        ("记录编号", detail["record_no"]),
        ("机房名称", f'{room["name"]}（{room["code"]}）'),
        ("所属区域", room.get("area") or "-"),
        ("巡检人员", inspector["name"]),
        ("巡检来源", source_zh),
        ("巡检时间", _fmt_dt(detail["inspection_time"])),
        ("提交时间", _fmt_dt(detail["submitted_at"])),
        ("当前状态", status_zh),
        ("是否发现问题", has_issue_zh),
    ]
    meta_html = "".join(
        f'<div class="kv"><span class="k">{_e(k)}</span><span class="v">{_e(v)}</span></div>'
        for k, v in meta_rows
    )

    eq_blocks = []
    for eq in eq_results:
        is_abn = eq["result"] == "abnormal"
        badge_cls = "bad" if is_abn else "ok"
        badge_txt = "异常" if is_abn else "正常"

        item_rows = []
        for it in eq["items"]:
            if it["input_type"] == "boolean":
                measured = "异常" if (it["value"] == "abnormal") else "正常"
            else:
                measured = it["value"] or "-"
                if it["input_type"] == "number" and it.get("unit"):
                    measured = f'{measured} {it["unit"]}'
            std = it.get("standard_value") or "-"
            if it.get("unit") and std != "-":
                std = f'{std} {it["unit"]}'
            res_txt = "异常" if it["is_abnormal"] else "正常"
            res_cls = "bad" if it["is_abnormal"] else "ok"
            item_rows.append(
                f"<tr>"
                f'<td>{_e(it["item_name"])}</td>'
                f"<td>{_e(std)}</td>"
                f"<td>{_e(measured)}</td>"
                f'<td class="{res_cls}">{res_txt}</td>'
                f'<td>{_e(it.get("remark") or "")}</td>'
                f"</tr>"
            )
        items_table = (
            "<table class='items'><thead><tr>"
            "<th>检查项</th><th>标准值</th><th>实测值</th><th>结果</th><th>备注</th>"
            "</tr></thead><tbody>" + "".join(item_rows) + "</tbody></table>"
            if item_rows else "<div class='muted'>无检查项记录</div>"
        )

        issue_html = ""
        if eq.get("issue_description"):
            issue_html = f'<div class="issue">异常说明：{_e(eq["issue_description"])}</div>'

        photos_html = ""
        photos = []
        for fp in att_paths.get(eq["equipment_id"], []):
            uri = _img_data_uri(fp)
            if uri:
                photos.append(f'<img class="photo" src="{uri}" alt="现场照片" />')
        if photos:
            photos_html = (
                '<div class="photos-title">现场照片</div>'
                f'<div class="photos">{"".join(photos)}</div>'
            )

        eq_blocks.append(
            f'<section class="eq {badge_cls}">'
            f'<div class="eq-head">'
            f'<span class="badge {badge_cls}">{badge_txt}</span>'
            f'<span class="eq-name">{_e(eq["equipment_name"])}</span>'
            f'<span class="eq-type">{_e(eq["equipment_type_label"])}</span>'
            f'<span class="eq-loc">{_e(eq.get("location") or "")}</span>'
            f'<span class="eq-time">完成于 {_fmt_dt(eq.get("completed_at"))}</span>'
            f"</div>"
            f"{issue_html}{items_table}{photos_html}"
            f"</section>"
        )

    timeline_html = "".join(
        f'<li><span class="t">{_fmt_dt(t["at"])}</span>'
        f'<span class="a">{_e(t.get("text") or t.get("action"))}</span>'
        f'<span class="o">{_e(t.get("operator") or "")}</span></li>'
        for t in detail.get("timeline", [])
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = settings.APP_NAME

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>巡检报告 {_e(detail["record_no"])}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #f4f6fa; color: #1f2937;
    font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; }}
  .page {{ max-width: 920px; margin: 0 auto; padding: 28px; background: #fff; }}
  .rpt-head {{ border-bottom: 2px solid #1e5eff; padding-bottom: 14px; margin-bottom: 18px; }}
  .sys {{ font-size: 13px; color: #6b7280; }}
  .rpt-title {{ font-size: 24px; font-weight: 700; margin: 6px 0 2px; }}
  .rpt-no {{ font-size: 13px; color: #6b7280; }}
  .meta {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px 18px; margin: 16px 0 20px; }}
  .kv {{ display: flex; flex-direction: column; }}
  .kv .k {{ font-size: 12px; color: #9ca3af; }}
  .kv .v {{ font-size: 14px; font-weight: 600; margin-top: 2px; }}
  .summary {{ display: flex; gap: 12px; margin-bottom: 20px; }}
  .sum-card {{ flex: 1; border: 1px solid #eef0f4; border-radius: 8px; padding: 12px 14px; text-align: center; }}
  .sum-card .n {{ font-size: 22px; font-weight: 700; }}
  .sum-card .l {{ font-size: 12px; color: #9ca3af; margin-top: 2px; }}
  .sum-card.ok .n {{ color: #52c41a; }}
  .sum-card.bad .n {{ color: #f5222d; }}
  .section-title {{ font-size: 16px; font-weight: 700; margin: 22px 0 12px; padding-left: 8px;
    border-left: 3px solid #1e5eff; }}
  .eq {{ border: 1px solid #eef0f4; border-left: 3px solid #52c41a; border-radius: 8px;
    padding: 12px 14px; margin-bottom: 14px; }}
  .eq.bad {{ border-left-color: #f5222d; }}
  .eq-head {{ display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }}
  .badge {{ font-size: 11px; padding: 2px 8px; border-radius: 10px; }}
  .badge.ok {{ background: rgba(82,196,26,.12); color: #52c41a; }}
  .badge.bad {{ background: rgba(245,34,45,.12); color: #f5222d; }}
  .eq-name {{ font-size: 15px; font-weight: 700; }}
  .eq-type {{ font-size: 12px; color: #6b7280; background: #f5f7fa; padding: 1px 8px; border-radius: 8px; }}
  .eq-loc {{ font-size: 12px; color: #9ca3af; }}
  .eq-time {{ font-size: 12px; color: #9ca3af; margin-left: auto; }}
  .issue {{ background: rgba(245,34,45,.05); border-left: 3px solid rgba(245,34,45,.4);
    padding: 8px 10px; border-radius: 4px; font-size: 13px; color: #f5222d; margin-bottom: 8px; }}
  table.items {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  table.items th, table.items td {{ border: 1px solid #eef0f4; padding: 6px 8px; text-align: left; }}
  table.items th {{ background: #f8f9fc; color: #6b7280; font-weight: 600; }}
  table.items td.ok {{ color: #52c41a; }}
  table.items td.bad {{ color: #f5222d; font-weight: 600; }}
  .photos-title {{ font-size: 12px; color: #9ca3af; margin: 10px 0 6px; }}
  .photos {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  img.photo {{ width: 150px; height: 150px; object-fit: cover; border: 1px solid #eef0f4; border-radius: 6px; }}
  ul.timeline {{ list-style: none; padding: 0; margin: 0; }}
  ul.timeline li {{ display: flex; gap: 12px; font-size: 13px; padding: 6px 0; border-bottom: 1px dashed #f1f2f5; }}
  ul.timeline .t {{ color: #9ca3af; width: 130px; flex-shrink: 0; }}
  ul.timeline .o {{ color: #9ca3af; margin-left: auto; }}
  .muted {{ color: #9ca3af; font-size: 13px; }}
  .foot {{ margin-top: 24px; padding-top: 12px; border-top: 1px solid #eef0f4;
    font-size: 12px; color: #9ca3af; text-align: center; }}
  @media print {{ body {{ background: #fff; }} .page {{ max-width: none; padding: 0; }} }}
</style>
</head>
<body>
<div class="page">
  <div class="rpt-head">
    <div class="sys">{_e(title)}</div>
    <div class="rpt-title">机房巡检报告</div>
    <div class="rpt-no">报告编号：{_e(detail["record_no"])}</div>
  </div>

  <div class="meta">{meta_html}</div>

  <div class="summary">
    <div class="sum-card"><div class="n">{total}</div><div class="l">设备总数</div></div>
    <div class="sum-card ok"><div class="n">{normal_n}</div><div class="l">正常</div></div>
    <div class="sum-card bad"><div class="n">{abnormal_n}</div><div class="l">异常</div></div>
  </div>

  <div class="section-title">设备巡检结果</div>
  {"".join(eq_blocks) if eq_blocks else "<div class='muted'>无设备结果</div>"}

  <div class="section-title">流程时间线</div>
  <ul class="timeline">{timeline_html or "<li class='muted'>无</li>"}</ul>

  <div class="foot">本报告由系统于 {generated_at} 自动生成</div>
</div>
</body>
</html>"""


def generate_report(db: Session, record_id: int) -> Path | None:
    """(Re)generate and persist the HTML report for a record. Returns the path,
    or None if the record does not exist."""
    detail = inspection_record_service.get_record_detail(db, record_id)
    if detail is None:
        return None
    att_paths = _attachment_paths_by_eq(db, record_id)
    html_text = _render_html(detail, att_paths)
    path = report_path(detail["record_no"])
    path.write_text(html_text, encoding="utf-8")
    logger.info(f"Generated inspection report: {path.name}")
    return path


def ensure_report(db: Session, record_id: int) -> tuple[Path, str] | None:
    """Return (path, record_no), generating the file if it is missing.
    None if the record does not exist."""
    detail = inspection_record_service.get_record_detail(db, record_id)
    if detail is None:
        return None
    path = report_path(detail["record_no"])
    if not path.is_file():
        att_paths = _attachment_paths_by_eq(db, record_id)
        path.write_text(_render_html(detail, att_paths), encoding="utf-8")
        logger.info(f"Lazily generated inspection report: {path.name}")
    return path, detail["record_no"]


def safe_generate(db: Session, record_id: int) -> None:
    """Best-effort generation used on submit; never raises into the request path."""
    try:
        generate_report(db, record_id)
    except Exception as exc:  # noqa: BLE001 - report generation must not break submit
        logger.warning(f"Report generation failed for record {record_id}: {exc}")
