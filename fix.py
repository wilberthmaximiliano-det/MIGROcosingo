import pathlib, re
path = pathlib.Path('app.py')
text = path.read_text(encoding='utf-8')

nuevo_index = """@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        r = Reporte(
            fecha=request.form.get('fecha'),
            lugar=request.form.get('lugar'),
            personal=request.form.get('personal'),
            actividad=request.form.get('actividad'),
            turno=request.form.get('turno'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(r)
        db.session.commit()
        return redirect('/')

    # FECHAS AUTOMATICAS MEXICO LUNES A DOMINGO
    from zoneinfo import ZoneInfo
    from datetime import datetime, timedelta
    tz_mexico = ZoneInfo('America/Mexico_City')
    hoy = datetime.now(tz_mexico).date()
    lunes = hoy - timedelta(days=hoy.weekday())
    fechas = []
    for i in range(7):
        d = lunes + timedelta(days=i)
        fechas.append(d.strftime('%d/%m/%Y'))
    return render_template('index.html', fechas=fechas)
"""

# reemplaza la funcion index
text = re.sub(r"@app\.route\('/', methods=\['GET', 'POST'\]\).*?def index\(\):.*?return render_template\('index\.html'.*?\)", nuevo_index, text, flags=re.DOTALL)

# asegura import ZoneInfo arriba
if 'ZoneInfo' not in text.split('def index')[0]:
    text = text.replace('from flask', 'from zoneinfo import ZoneInfo\nfrom flask', 1)

path.write_text(text, encoding='utf-8')
print('LISTO - app.py arreglado')
