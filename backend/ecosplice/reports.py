"""CSV, JSON and printable HTML derived from exactly one stored run and filter."""
import copy
import csv
from html import escape
import io
import json


def select_report(run, scope="all", kind=None, min_score=None, predicted_only=False, query=""):
    report = copy.deepcopy(run)
    candidates = report["analysis"]["candidates"]
    selected = candidates
    if scope == "filtered":
        selected = [site for site in candidates
                    if (kind is None or site["type"] == kind)
                    and (min_score is None or (site["score"] is not None and site["score"] >= min_score))
                    and (not predicted_only or site["predicted"])
                    and query.strip().casefold() in f'{site["id"]} {site["position1"]} {site["motif"]} {site["type"]}'.casefold()]
    report["analysis"]["candidates"] = selected
    report["export"] = {"scope": scope, "type": kind, "min_score": min_score,
                        "predicted_only": predicted_only, "query": query.strip(), "total_candidates": len(candidates),
                        "exported_candidates": len(selected),
                        "measurement_scope": "Original complete computation; filtering does not recompute timings or evaluation."}
    return report


def safe_cell(value):
    # Spreadsheet programs can interpret untrusted names as formulas.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def json_report(report):
    return json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)


def csv_report(report):
    analysis = report["analysis"]
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    # Metadata records also exist for empty results. Settings/measurements are
    # serialized without rounding, so CSV retains the complete provenance.
    fields = ["id", "position1", "type", "motif", "score", "preliminary_score", "threshold",
              "predicted", "route", "scorer", "unavailable_reason"]
    writer.writerow(["record", "field", "value", *fields])
    metadata = {key: value for key, value in report.items() if key != "analysis"}
    metadata.update({"analysis." + key: value for key, value in analysis.items() if key != "candidates"})
    for key, value in metadata.items():
        value = json.dumps(value, ensure_ascii=False, allow_nan=False) if isinstance(value, (dict, list)) else value
        writer.writerow(["metadata", key, safe_cell(value), *("" for _ in fields)])
    for site in analysis["candidates"]:
        writer.writerow(["candidate", "", "", *(safe_cell(site[field]) for field in fields)])
    return output.getvalue()


def html_report(report):
    analysis = report["analysis"]
    fields = ["id", "position1", "type", "motif", "score", "preliminary_score", "threshold", "predicted", "route", "scorer", "unavailable_reason"]
    def display(value):
        return escape("Unavailable" if value is None else str(value))
    rows = "".join("<tr>" + "".join(f"<td>{display('—' if field == 'unavailable_reason' and site[field] is None else site[field])}</td>" for field in fields) + "</tr>"
                   for site in analysis["candidates"])
    # Keep all metadata/settings in print as well, including the input identity.
    metadata = {key: value for key, value in report.items() if key not in ("analysis", "input_sequence")}
    metadata["analysis"] = {key: value for key, value in analysis.items() if key != "candidates"}
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>EcoSplice: {display(report['name'])}</title><style>
body{{font:14px system-ui,sans-serif;color:#183b2c;margin:32px}}h1{{color:#176443}}
table{{border-collapse:collapse;width:100%;font-size:11px}}td,th{{border:1px solid #bdd0c4;padding:5px;text-align:left;overflow-wrap:anywhere}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px}}thead{{display:table-header-group}}
tr{{break-inside:avoid}}@media print{{body{{margin:0}}@page{{size:landscape;margin:12mm}}}}
</style></head><body><h1>EcoSplice: {display(report['name'])}</h1>
<p>{display(analysis['coordinate_convention'])}. {display(analysis['score_meaning'])}.</p>
<p>Export scope: {display(report['export']['scope'])}; {len(analysis['candidates'])} of {report['export']['total_candidates']} candidates.
Timings, work, energy and evaluation describe the original complete run.</p>
<p>Estimated energy: {display(report['energy']['estimated_joules'])} J at assumed {display(report['energy']['assumed_power_watts'])} W.
This is a runtime-based estimate, not a laptop power measurement. Use the browser's Print command to save as PDF.</p>
<table><thead><tr>{''.join('<th>' + display(field) + '</th>' for field in fields)}</tr></thead><tbody>{rows}</tbody></table>
<h2>Run settings and provenance</h2><pre>{escape(json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False))}</pre>
<p>Normalized input DNA is retained in the local saved run and JSON/CSV export; its hash and length identify it here.</p>
</body></html>"""
