from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, send_file, session, url_for
from datetime import datetime, timedelta
import json, os, uuid, collections
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from functools import wraps

app = Flask(__name__)
app.secret_key = "migr-ocosingo-2025-secreto"
MODO_PRUEBA = False
ADMIN_PASSWORD = "MIGR2026"
ARCHIVO = "reportes.json"
ORDEN_ASIGN = ["Lider","Anciano","Diacono","Discipulo"]

def get_semana_vigente():
    hoy = datetime.now(); lunes = hoy - timedelta(days=hoy.weekday()); return [lunes + timedelta(days=i) for i in range(7)]
def get_semana_str(dt): return [d.strftime("%d/%m/%Y") for d in dt]
def cargar():
    if not os.path.exists(ARCHIVO): return []
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f: return json.load(f)
    except: return []
def guardar(d):
    with open(ARCHIVO, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)
def formulario_abierto():
    if MODO_PRUEBA: return True
    ahora = datetime.now()
    return ahora.weekday() == 6 and 8 <= ahora.hour < 21
def es_admin():
    return session.get('is_admin') == True
def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not es_admin():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return dec
def dibujar_reporte(c, rep, y_top, w, h):
    MARGEN = 15; TABLE_W = w - (MARGEN*2); COL0 = 80; COL_REST = (TABLE_W - COL0) / 7; COLS = [COL0] + [COL_REST]*7; ROW_H = 20
    c.setFillColor(colors.HexColor("#e8eaf6")); c.rect(0, y_top-65, w, 65, fill=1, stroke=0)
    if os.path.exists("static/logo.png"):
        try: c.drawImage("static/logo.png", MARGEN, y_top-56, width=50, height=40, preserveAspectRatio=True, mask='auto')
        except: pass
    c.setFillColor(colors.HexColor("#1e293b")); c.setFont("Helvetica-Bold", 14); c.drawCentredString(w/2, y_top-35, "Reporte de Vida Espiritual"); c.setFont("Helvetica", 7); c.drawRightString(w-MARGEN, y_top-35, "MIGR Ocosingo")
    y = y_top - 80; c.setFillColor(colors.HexColor("#e2e8f0")); c.roundRect(MARGEN, y-2, 85, 18, 5, fill=1, stroke=0); c.setFillColor(colors.HexColor("#334155")); c.setFont("Helvetica-Bold", 9); c.drawString(MARGEN+10, y+2, rep.get('asignacion','Diacono')); y-=20
    c.setFillColor(colors.black); c.setFont("Helvetica", 10); c.drawString(MARGEN, y, f"{rep.get('nombre','')} {rep.get('apellido','')}"); y-=15
    fechas = rep.get('semana',[]);
    if isinstance(fechas,str):
        try: fechas=eval(fechas)
        except: fechas=get_semana_str(get_semana_vigente())
    x = MARGEN; c.setFillColor(colors.HexColor("#f1f5f9")); c.rect(x, y-ROW_H, TABLE_W, ROW_H, fill=1, stroke=0); c.setStrokeColor(colors.HexColor("#94a3b8")); c.setLineWidth(0.8); cx=x
    for cw in COLS: c.rect(cx, y-ROW_H, cw, ROW_H, fill=0, stroke=1); cx+=cw
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 8); cx=x+COLS[0]
    for f in fechas: c.drawCentredString(cx+COL_REST/2, y-ROW_H+7, f); cx+=COL_REST
    y-=ROW_H
    conceptos=['Oracion','Ayuno','Lectura','Visita','Diezmo','Ofrenda','Predica','Libro']; keys=['oracion','ayuno','lectura','visita','diezmo','ofrenda','predica','libro']
    for idx,conc in enumerate(conceptos):
        c.setFillColor(colors.white if idx%2==0 else colors.HexColor("#f8fafc")); c.rect(x, y-ROW_H, TABLE_W, ROW_H, fill=1, stroke=0); c.setFillColor(colors.HexColor("#f1f5f9")); c.rect(x, y-ROW_H, COLS[0], ROW_H, fill=1, stroke=0); cx=x
        for cw in COLS: c.rect(cx, y-ROW_H, cw, ROW_H, fill=0, stroke=1); cx+=cw
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 9); c.drawString(x+5, y-ROW_H+7, conc); c.setFont("Helvetica", 10); cx=x+COLS[0]; kb=keys[idx]
        for i in range(7): v=rep.get(f"{kb}_{i}",""); c.drawCentredString(cx+COL_REST/2, y-ROW_H+7, str(v)); cx+=COL_REST
        y-=ROW_H
    y-=10; pred=rep.get('detalle_predica','').strip(); libro=rep.get('detalle_libro','').strip()
    c.setFont("Helvetica-Bold", 9); c.drawString(MARGEN, y, "Predica:"); c.setFont("Helvetica", 9); c.drawString(MARGEN+45, y, pred[:140]); y-=13
    c.setFont("Helvetica-Bold", 9); c.drawString(MARGEN, y, "Libro:"); c.setFont("Helvetica", 9); c.drawString(MARGEN+40, y, libro[:140]); y-=10
    return y
def get_key_semana(rep):
    sem=rep.get('semana',[])
    if not sem: return "Sin semana"
    if isinstance(sem,str):
        try: sem=eval(sem)
        except: pass
    return f"{sem[0]} - {sem[-1]}" if len(sem)>=2 else str(sem[0])
def parse_fecha_key(key):
    try:
        primera = key.split(" - ")[0]
        return datetime.strptime(primera, "%d/%m/%Y")
    except: return datetime.min
MESES_ES = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]

@app.route("/")
def caratula(): return render_template("caratula.html")

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    error=None
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD:
            session['is_admin']=True
            return redirect(url_for('admin'))
        else:
            error="Contraseña incorrecta"
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'><style>
    body{{margin:0;background:#0f172a;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Inter,Arial}}
   .box{{background:white;padding:32px;border-radius:16px;width:100%;max-width:360px;box-shadow:0 10px 40px rgba(0,0,0,0.3);text-align:center}}
    input{{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:12px;box-sizing:border-box}}
    button{{width:100%;margin-top:14px;padding:12px;background:#0f172a;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer}}
   .err{{color:#dc2626;font-size:13px;margin-top:10px}}
    </style></head><body><div class='box'><h2 style='margin:0'>🔐 Admin MIGR</h2><p style='color:#64748b;font-size:13px'>Ingresa la contraseña</p>
    <form method='POST'><input type='password' name='password' placeholder='Contraseña' required autofocus>
    <button>Entrar</button></form>
    {f"<div class='err'>{error}</div>" if error else ""}
    <br><a href='/' style='font-size:12px;color:#64748b;text-decoration:none'>Volver al inicio</a></div></body></html>
    """

@app.route("/admin/logout")
def admin_logout():
    session.pop('is_admin',None)
    return redirect("/")

@app.route("/formulario", methods=["GET","POST"])
def formulario():
    if not formulario_abierto() and not es_admin():
        return render_template("cerrado.html")
    fechas_str=get_semana_str(get_semana_vigente())
    if request.method=="POST":
        datos=cargar()
        nuevo={"id":str(uuid.uuid4())[:8],"creado":datetime.now().isoformat(),"semana":fechas_str}
        for k in request.form: nuevo[k]=request.form.get(k)
        datos.append(nuevo); guardar(datos)
        return redirect(f"/gracias/{nuevo['id']}")
    return render_template("index.html", fechas=fechas_str, is_admin=es_admin())

@app.route("/gracias/<id>")
def gracias(id): return """<html><head><meta name='viewport' content='width=device-width'><style>body{font-family:Arial;display:flex;justify-content:center;align-items:center;height:100vh;background:#f8fafc;margin:0}.box{background:white;padding:40px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,0.08);text-align:center}.icon{width:80px;height:80px;background:#22c55e;border-radius:50%;display:flex;justify-content:center;align-items:center;margin:0 auto 20px;font-size:45px;color:white}h2{color:#1e293b}</style></head><body><div class='box'><div class='icon'>✓</div><h2>¡Reporte Guardado!</h2><p>Gracias por tu fidelidad.</p><br><a href='/' style='background:#f1f5f9;padding:10px 20px;border-radius:8px;text-decoration:none;color:#334155'>Volver al inicio</a></div></body></html>"""

@app.route("/dashboard")
@login_required
def dashboard():
    datos=cargar()
    if not datos:
        return "<h2 style='font-family:Arial;padding:40px'>Aun no hay reportes</h2><a href='/admin'>Volver</a>"
    personas_dict = {}
    for r in datos:
        key = f"{r.get('nombre','').strip()} {r.get('apellido','').strip()}".strip()
        if key and key not in personas_dict: personas_dict[key] = r.get('asignacion','')
    personas = sorted(personas_dict.keys())
    semanas_raw = list(set([get_key_semana(r) for r in datos]))
    semanas_sorted = sorted(semanas_raw, key=parse_fecha_key)
    semanas_info = []
    for s in semanas_sorted:
        dt = parse_fecha_key(s)
        mes = MESES_ES[dt.month-1] if dt!= datetime.min else "??"
        label_mes = f"{mes} {dt.strftime('%y')}" if dt!= datetime.min else "??"
        semanas_info.append({"key":s,"dt":dt,"mes":label_mes})
    grupos_mes = []
    if semanas_info:
        cur_mes = semanas_info[0]["mes"]
        count = 1
        for i in range(1,len(semanas_info)):
            if semanas_info[i]["mes"]==cur_mes: count+=1
            else: grupos_mes.append((cur_mes,count)); cur_mes=semanas_info[i]["mes"]; count=1
        grupos_mes.append((cur_mes,count))
    entregas = {p: {s: False for s in semanas_sorted} for p in personas}
    primera_semana = {}
    fecha_primera = {}
    for p in personas:
        primera_semana[p]=None
        fecha_primera[p]=None
    for r in datos:
        p = f"{r.get('nombre','').strip()} {r.get('apellido','').strip()}".strip()
        s = get_key_semana(r)
        if p in entregas and s in entregas[p]: entregas[p][s] = True
    for p in personas:
        for idx, s in enumerate(semanas_sorted):
            if entregas[p][s]:
                primera_semana[p]=idx
                fecha_primera[p]=parse_fecha_key(s)
                break
    total_posibles = len(personas) * len(semanas_sorted) if personas and semanas_sorted else 0
    total_entregados = sum([1 for p in personas for s in semanas_sorted if entregas[p][s]])
    total_omitidos = total_posibles - total_entregados
    cumplimiento = round(total_entregados/total_posibles*100,1) if total_posibles else 0
    entregas_por_semana = []
    for s in semanas_sorted:
        cnt = sum([1 for p in personas if entregas[p][s]])
        entregas_por_semana.append((s,cnt))
    crit = min(entregas_por_semana, key=lambda x: x[1]) if entregas_por_semana else ("-",0)
    desempeno = []
    for p in personas:
        cnt = sum([1 for s in semanas_sorted if entregas[p][s]])
        perc = round(cnt/len(semanas_sorted)*100,1) if semanas_sorted else 0
        if perc >= 85: est="Excelente"; cls="exc"
        elif perc >= 70: est="Bueno"; cls="bueno"
        elif perc >= 60: est="Regular"; cls="reg"
        elif perc >= 50: est="Bajo"; cls="bajo"
        else: est="Critico"; cls="crit"
        desempeno.append((p, perc, est, cls, cnt))
    desempeno.sort(key=lambda x: x[1], reverse=True)
    hoy = datetime.now()
    es_nuevo_dict = {}
    for p in personas:
        if fecha_primera[p] and (hoy - fecha_primera[p]).days <= 45:
            es_nuevo_dict[p]=True
        else:
            es_nuevo_dict[p]=False
    html = f"""
<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>
<style>
body{{margin:0;background:#0f172a;color:#e2e8f0;font-family:Inter,Arial}}
.top4{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;padding:15px}}
@media(max-width:900px){{.top4{{grid-template-columns:1fr 1fr}}}}
@media(max-width:500px){{.top4{{grid-template-columns:1fr}}}}
.kpi{{border-radius:12px;padding:16px;border:1px solid #1e293b}}
.k1{{background:linear-gradient(135deg,#0ea5e9,#2563eb)}}.k2{{background:#1e293b}}.k3{{background:#1e293b}}.k4{{background:#1e293b}}
.kpi small{{display:block;font-size:11px;opacity:0.8;text-transform:uppercase;letter-spacing:0.5px}}
.big{{font-size:32px;font-weight:800;margin:4px 0}}.sub{{font-size:11px;color:#94a3b8}}
.main{{display:grid;grid-template-columns:340px 1fr;gap:12px;padding:0 15px 15px}}
@media(max-width:1100px){{.main{{grid-template-columns:1fr}}}}
.panel{{background:#1e293b;border-radius:12px;padding:14px;border:1px solid #334155}}
.panel h3{{margin:0 0 10px;font-size:14px;display:flex;justify-content:space-between}}
.tbl{{width:100%;border-collapse:collapse;font-size:12px}}
.tbl th{{text-align:left;color:#94a3b8;font-size:11px;padding:6px 4px;border-bottom:1px solid #334155}}
.tbl td{{padding:6px 4px;border-bottom:1px solid #1e293b}}
.badge{{padding:2px 8px;border-radius:12px;font-size:10px;font-weight:bold}}
.exc{{background:#064e3b;color:#6ee7b7}}.bueno{{background:#1e3a8a;color:#93c5fd}}.reg{{background:#422006;color:#fde68a}}.bajo{{background:#431407;color:#fb923c}}.crit{{background:#450a0a;color:#fca5a5}}
.matriz{{overflow:auto;max-height:85vh}}
.mat{{border-collapse:collapse;font-size:11px}}
.mat th{{background:#1e293b;color:#94a3b8;padding:4px 6px;white-space:nowrap;font-size:10px;border:1px solid #0f172a}}
.mat th.month{{background:#0f172a;color:#38bdf8;font-size:11px;font-weight:bold;border-bottom:2px solid #38bdf8;text-align:center}}
.mat th:first-child,.mat td:first-child{{position:sticky;left:0;background:#1e293b;z-index:2;min-width:140px}}
.mat td{{padding:0;text-align:center;min-width:28px;height:28px;border:1px solid #0f172a}}
.ok{{background:#0f5a3a;color:#4ade80}}.no{{background:#7f1d1d;color:#f87171}}.ini{{background:#1e40af;color:#bfdbfe;font-size:9px;font-weight:bold}}
.leg{{display:flex;gap:12px;font-size:11px;margin-bottom:8px}}.dot{{width:8px;height:8px;border-radius:50%;display:inline-block}}
a{{color:#60a5fa;text-decoration:none}}
</style></head><body>
<div style='padding:10px 15px'><a href='/admin'>← Volver a Admin</a> <a href='/admin/logout' style='float:right;color:#f87171'>Cerrar sesión</a> <span style='color:#64748b;font-size:12px'> | MIGR Ocosingo - Admin activo</span></div>
<div class='top4'>
<div class='kpi k1'><small>Cumplimiento Global</small><div class='big'>{cumplimiento}%</div><div class='sub'>{total_entregados} de {total_posibles}</div></div>
<div class='kpi k2'><small>Entregados</small><div class='big'>{total_entregados}</div><div class='sub'>Verde</div></div>
<div class='kpi k3'><small>Omitidos</small><div class='big'>{total_omitidos}</div><div class='sub'>Rojo</div></div>
<div class='kpi k4'><small>Semana Más Crítica</small><div class='big' style='font-size:18px'>{crit[0][:20]}</div><div class='sub'>Solo {crit[1]}/{len(personas)} ({round(crit[1]/len(personas)*100) if personas else 0}%)</div></div>
</div>
<div class='main'>
<div class='panel'><h3>Desempeño Individual <span style='color:#94a3b8;font-weight:normal'>{len(personas)} Personas</span></h3>
<table class='tbl'><tr><th>Nombre</th><th>%</th><th>Estatus</th><th></th></tr>
"""
    for p,perc,est,cls,cnt in desempeno:
        nuevo_tag = "<span style='background:#1e40af;color:#bfdbfe;font-size:8px;padding:2px 5px;border-radius:8px;margin-left:4px'>NUEVO</span>" if es_nuevo_dict[p] else ""
        html+=f"<tr><td>{p} {nuevo_tag}</td><td><b>{perc}%</b></td><td><span class='badge {cls}'>{est}</span></td><td style='font-size:10px;color:#64748b'>{fecha_primera[p].strftime('%d/%m/%y') if fecha_primera[p] else ''}</td></tr>"
    html+="</table></div><div class='panel'><h3>Matriz - Mes arriba + INICIO solo nuevos (45 días)</h3><div class='leg'><span><span class='dot' style='background:#4ade80'></span> Entregado</span><span><span class='dot' style='background:#f87171'></span> Omitido</span><span><span class='dot' style='background:#60a5fa'></span> INICIO (solo nuevos)</span></div><div class='matriz'><table class='mat'><tr><th>Nombre</th>"
    for mes_label, cnt in grupos_mes:
        html+=f"<th class='month' colspan='{cnt}'>{mes_label}</th>"
    html+="</tr><tr><th></th>"
    for idx in range(len(semanas_sorted)):
        html+=f"<th>W{idx+1}</th>"
    html+="</tr>"
    for p in [x[0] for x in desempeno]:
        html+=f"<tr><td style='text-align:left;padding-left:6px'>{p}</td>"
        for idx,s in enumerate(semanas_sorted):
            es_primera = (primera_semana[p]==idx)
            if es_primera and es_nuevo_dict[p] and entregas[p][s]:
                html+=f"<td class='ini' title='{s} - NUEVO'>INICIO</td>"
            elif entregas[p][s]:
                html+=f"<td class='ok' title='{s}'>✓</td>"
            else:
                html+=f"<td class='no' title='{s}'>X</td>"
        html+="</tr>"
    html+="</table></div></div></div></body></html>"
    return html

@app.route("/pdf/<id>")
def pdf_one(id):
    datos=cargar(); rep=next((r for r in datos if r["id"]==id), None)
    if not rep: return "No",404
    path=f"reporte_{id}.pdf"; c=canvas.Canvas(path,pagesize=letter); w,h=letter
    dibujar_reporte(c,rep,h-15,w,h); c.save(); return send_file(path,as_attachment=False)

@app.route("/pdf_todos")
@login_required
def pdf_todos():
    semana=request.args.get('semana'); asign=request.args.get('asign')
    datos=cargar()
    if semana: datos=[r for r in datos if get_key_semana(r)==semana]
    if asign: datos=[r for r in datos if r.get('asignacion','').lower()==asign.lower()]
    datos=sorted(datos, key=lambda r: (ORDEN_ASIGN.index(r.get('asignacion','')) if r.get('asignacion','') in ORDEN_ASIGN else 99, r.get('nombre','')))
    if not datos: return "No hay reportes"
    path="reportes_2_centrado_grande.pdf"
    c=canvas.Canvas(path,pagesize=letter); w,h=letter
    y=h-15; count=0
    for rep in datos:
        if count%2==0 and count!=0: c.showPage(); y=h-15
        y=dibujar_reporte(c,rep,y,w,h); y-=25; count+=1
        if y < 150: c.showPage(); y=h-15; count=0
    c.save(); return send_file(path,as_attachment=False)

@app.route("/admin")
def admin():
    if not es_admin():
        return redirect(url_for("admin_login"))
    datos = cargar()
    fechas = get_semana_vigente()
    fechas_str = get_semana_str(fechas)
    return render_template("admin.html", reportes=datos, fechas=fechas_str, is_admin=es_admin())


if __name__=="__main__": app.run(debug=True)
