#!/usr/bin/env python3
"""Generate charts from benchmark data."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

QUANTS = ["Q4_K_M", "Q5_K_M", "Q8_0"]
COLORS = {"Q4_K_M": "#3b82f6", "Q5_K_M": "#f59e0b", "Q8_0": "#22c55e"}
DISK_SIZES = {"Q4_K_M": 4.4, "Q5_K_M": 5.1, "Q8_0": 7.6}

def load_results():
    data = {}
    for q in QUANTS:
        path = os.path.join(DATA_DIR, f"code_{q.lower()}_results.json")
        if os.path.exists(path):
            with open(path) as f:
                data[q] = json.load(f)
    return data

def gen_html_table(data):
    html = '<table border="1" cellpadding="8" cellspacing="0">\n'
    html += '<tr><th>Quant</th><th>Disk</th><th>Easy</th><th>Medium</th><th>Hard</th><th>Overall</th><th>Avg Time</th></tr>\n'
    for q in QUANTS:
        if q not in data:
            continue
        d = data[q]
        s = d.get("summary", {})
        tiers = s.get("tiers", {})
        overall = s.get("overall", {})
        disk = DISK_SIZES.get(q, "?")
        html += f'<tr><td>{q}</td><td>{disk}GB</td>'
        for t in ["easy", "medium", "hard"]:
            td = tiers.get(t, {})
            rate = td.get("pass_rate", 0)
            html += f'<td>{rate}%</td>'
        html += f'<td><strong>{overall.get("pass_rate", 0)}%</strong></td>'
        times = [tiers[t].get("avg_code_duration_ms", 0) for t in ["easy", "medium", "hard"] if t in tiers]
        avg_time = sum(times) / len(times) / 1000 if times else 0
        html += f'<td>{avg_time:.1f}s</td>'
        html += '</tr>\n'
    html += '</table>\n'
    return html

def gen_chart_data(data):
    labels = QUANTS
    tiers = ["easy", "medium", "hard"]
    datasets = []
    for t in tiers:
        vals = []
        for q in QUANTS:
            if q in data:
                r = data[q].get("summary", {}).get("tiers", {}).get(t, {}).get("pass_rate", 0)
                vals.append(r)
            else:
                vals.append(0)
        datasets.append({"label": t.title(), "data": vals})
    return {"labels": labels, "datasets": datasets}

def gen_disk_chart_data(data):
    labels = QUANTS
    disk_vals = [DISK_SIZES[q] for q in QUANTS]
    pass_vals = []
    for q in QUANTS:
        if q in data:
            r = data[q].get("summary", {}).get("overall", {}).get("pass_rate", 0)
            pass_vals.append(r)
        else:
            pass_vals.append(0)
    return {"labels": labels, "disk": disk_vals, "pass_rate": pass_vals}

def main():
    data = load_results()
    if not data:
        print("No benchmark data found. Run code_quant_study.py first.")
        return

    # Generate summary inside each data file
    from benchmarks.code_quant_study import summarize
    for q in list(data.keys()):
        data[q]["summary"] = summarize(data[q])

    html = '<!DOCTYPE html><html lang="en"><head>'
    html += '<meta charset="UTF-8">'
    html += '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
    html += '<style>body{font-family:sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;}'
    html += 'h1{color:#f8fafc;}h2{color:#94a3b8;margin-top:24px;}'
    html += 'table{width:100%;border-collapse:collapse;margin:12px 0;}'
    html += 'th,td{border:1px solid #334155;padding:10px;text-align:center;}'
    html += 'th{background:#1e293b;color:#94a3b8;}'
    html += '.chart-container{max-width:600px;margin:20px 0;}</style>'
    html += '</head><body>'
    html += '<h1>Code Model — Quant vs Quality Study</h1>'

    html += '<h2>Pass Rate by Quant Level and Difficulty Tier</h2>'
    html += gen_html_table(data)
    html += '</div>'

    chart = gen_chart_data(data)
    html += '<h2>Pass Rate by Quant Level</h2>'
    html += '<div class="chart-container"><canvas id="passChart"></canvas></div>'

    disk_chart = gen_disk_chart_data(data)
    html += '<h2>Pass Rate vs Disk Size</h2>'
    html += '<div class="chart-container"><canvas id="diskChart"></canvas></div>'

    html += '<script>'
    html += f'new Chart(document.getElementById("passChart"),{{type:"bar",data:{{labels:{json.dumps(chart["labels"])},'
    html += f'datasets:{json.dumps(chart["datasets"])}}},'
    html += 'options:{{responsive:true,plugins:{{legend:{{labels:{{color:"#94a3b8"}}}}}},'
    html += 'scales:{{y:{{beginAtZero:true,max:100,ticks:{{color:"#94a3b8",callback:v=>v+"%"}}}}},'
    html += 'x:{{ticks:{{color:"#94a3b8"}}}}}}}});'

    html += f'new Chart(document.getElementById("diskChart"),{{type:"bar",data:{{labels:{json.dumps(disk_chart["labels"])},'
    html += f'datasets:[{{label:"Disk Size (GB)",data:{json.dumps(disk_chart["disk"])},backgroundColor:"#3b82f6",yAxisID:"y"}},'
    html += f'{{label:"Pass Rate (%)",data:{json.dumps(disk_chart["pass_rate"])},backgroundColor:"#22c55e",yAxisID:"y1"}}]}},'
    html += 'options:{{responsive:true,plugins:{{legend:{{labels:{{color:"#94a3b8"}}}}}},'
    html += 'scales:{{y:{{position:"left",ticks:{{color:"#3b82f6"}}}},'
    html += 'y1:{{position:"right",beginAtZero:true,max:100,ticks:{{color:"#22c55e",callback:v=>v+"%"}}}}}}}});'
    html += '</script></body></html>'

    out_path = os.path.join(DATA_DIR, "quant_quality_chart.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Chart saved to {out_path}")
    print(json.dumps({q: data[q].get("summary", {}) for q in data}, indent=2))

if __name__ == "__main__":
    main()
