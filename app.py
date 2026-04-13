from flask import Flask, render_template
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Conexión a base de datos
engine = create_engine(r'mssql+pyodbc://DellRodrigoEG\SQLEXPRESS01/AplicacionSistemaBibliometrico?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes')

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Flask ya sabe que debe buscar en la carpeta /templates
    return render_template('html/index.html')


@app.route('/publicaciones')
def ver_publicaciones():
    with engine.connect() as conn:
        # El cerebro busca en la base de datos
        query = text("SELECT TOP 20 Titulo, Anio, Citas FROM Publicaciones ORDER BY Anio DESC")
        datos = conn.execute(query).fetchall()
    
    # El cerebro manda los datos al archivo HTML en /templates
    return render_template('lista.html', lista_publicaciones=datos)

if __name__ == '__main__':
    app.run(debug=True)