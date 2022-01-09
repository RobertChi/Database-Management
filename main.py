from flask import Flask, render_template, jsonify, request, redirect
import cx_Oracle
from datetime import datetime

app = Flask(__name__)

con = cx_Oracle.connect("homeuser", "password", "localhost/xe")

@app.route('/')
@app.route('/clienti')
def clienti():
    info_client = []

    cur = con.cursor()
    cur.execute(
        'select nume_client,card_bancar,adresa,oras,email,clienti.id_client from info_client, clienti '
        'where clienti.id_client=info_client.id_client order by nume_client ')
    for result in cur:
        i = {}
        i['nume'] = result[0]
        i['nr_card'] = result[1]
        i['adresa'] = result[2]
        i['oras'] = result[3]
        i['email'] = result[4]
        i['id_client']=result[5]
        info_client.append(i)
    cur.close()
    return render_template('clienti.html', info_client=info_client)


@app.route('/addclient', methods=['POST', 'GET'])
def add_client():
    if request.method == 'POST':
        cur = con.cursor()

        valuesinfo = []
        nume=request.form['nume']

        cur.execute('INSERT INTO clienti VALUES (null,:s)', [nume])

        cur.execute('SELECT id_client FROM clienti WHERE clienti.nume_client=:s',[nume])
        id=cur.fetchone()

        valuesinfo.append("'"+(str)(id[0])+"'")
        valuesinfo.append("'" + request.form['oras'] + "'")
        valuesinfo.append("'" + request.form['adresa'] + "'")
        valuesinfo.append("'" + request.form['email'] + "'")
        valuesinfo.append("'" + request.form['nr_card'] + "'")

        query = 'INSERT INTO info_client VALUES (%s)' % (', '.join(valuesinfo))
        cur.execute(query)

        cur.execute('commit')

        return redirect('/clienti')
    else:
        return render_template('addclient.html')


@app.route('/getclient', methods=['POST'])
def get_client():
    id_c = request.form['valoare_buton1']
    cur = con.cursor()

    cur.execute('select * from info_client where id_client=:c', c=id_c)
    data = cur.fetchone()
    oras = data[1]
    adresa = data[2]
    email = data[3]
    card_bancar= data[4]

    cur.execute('select nume_client from clienti where id_client=:c', c=id_c)
    data = cur.fetchone()
    nume = data[0]

    cur.close()

    return render_template('editclient.html', id_client=id_c, adresa=adresa, oras=oras, email=email, nume=nume, nr_card=card_bancar)


@app.route('/editclient', methods=['POST'])
def edit_client():
    cur = con.cursor()
    id_c=request.form['id_client']

    nr_card = request.form['nr_card']
    nume = request.form['nume']
    adresa = request.form['adresa']
    oras = request.form['oras']
    email = request.form['email']

    query = 'UPDATE clienti SET nume_client=:t where id_client=:r'
    cur.execute(query, [nume, id_c])

    query = 'UPDATE info_client SET card_bancar=:s, adresa=:t, oras=:r, email=:w where id_client=:x'
    cur.execute(query, [nr_card, adresa, oras, email, id_c])

    cur.execute('commit')

    return redirect('/clienti')


@app.route('/delclient', methods=['POST'])
def del_client():
        id_c = request.form['valoare_buton']
        cur = con.cursor()

        cur.execute('delete from info_client where info_client.id_client=:c', [id_c])
        cur.execute('delete from clienti where clienti.id_client=:c', [id_c])
        cur.execute('commit')

        return redirect('/clienti')


# -----------------------------------------#
@app.route('/comanda')
def comanda():
    comanda = []

    cur = con.cursor()
    cur.execute('SELECT * from comanda ORDER BY data_comanda DESC')
    for result in cur:
        cur2=con.cursor()
        i = {}
        i['nr_comanda'] = result[0]
        cur2.execute('SELECT nume_produs FROM stoc where id_produs=:p',[result[1]])
        data=cur2.fetchone()
        i['nume_produs'] = data[0]
        cur2.execute('SELECT nume_client FROM clienti WHERE id_client=:c', [result[2]])
        data=cur2.fetchone()
        i['nume_client'] = data[0]
        i['nr_produse'] = result[3]
        i['data_comanda'] = datetime.strptime(str(result[4]), '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%y')
        comanda.append(i)

    cur.close()
    return render_template('comanda.html', comanda=comanda)

@app.route('/addcomanda',methods=['GET','POST'])
def add_comanda():
    if request.method=="POST":
        cur=con.cursor()

        cant_ceruta=request.form['cantitate']
        id_p=request.form['produs']
        cur.execute('SELECT cantitate_stoc from stoc where id_produs=:s',[id_p])
        data=cur.fetchone()
        cantitate_disponibila=data[0]

        if((int)(cantitate_disponibila)<(int)(cant_ceruta)):
            cur = con.cursor()
            cur.execute('SELECT id_client,nume_client from clienti')
            clienti = []
            for i in cur:
                client = {}
                client['id_client'] = i[0]
                client['nume_client'] = i[1]
                clienti.append(client)

            cur.execute('SELECT id_produs, nume_produs from stoc')
            stoc = []
            for j in cur:
                produs = {}
                produs['id_produs'] = j[0]
                produs['nume_produs'] = j[1]
                stoc.append(produs)

            return render_template('addcomanda.html', clienti=clienti, stoc=stoc)

        else:

            values = []

            values.append("'" + request.form['produs'] + "'")
            values.append("'" + request.form['client'] + "'")
            values.append("'" + request.form['cantitate'] + "'")

            query='INSERT INTO comanda VALUES(null, %s, SYSDATE)' %(', '.join(values))
            cur.execute(query)

            cantitate_noua=(int)(cantitate_disponibila)-(int)(cant_ceruta)
            cur.execute('UPDATE stoc SET cantitate_stoc=:s where id_produs=:t ',[cantitate_noua,id_p])
            cur.execute('commit')

            return redirect('/comanda')

    else:
        cur=con.cursor()
        cur.execute('SELECT id_client,nume_client from clienti')
        clienti=[]
        for i in cur:
            client={}
            client['id_client']=i[0]
            client['nume_client']=i[1]
            clienti.append(client)

        cur.execute('SELECT id_produs, nume_produs from stoc')
        stoc=[]
        for j in cur:
            produs={}
            produs['id_produs']=j[0]
            produs['nume_produs']=j[1]
            stoc.append(produs)

        return render_template('addcomanda.html', clienti=clienti, stoc=stoc)


@app.route('/delcomanda',methods=['POST'])
def anulare_comanda():

    cur = con.cursor()
    id_cmd = request.form['valoare_buton']

    cur.execute('select cantitate,id_produs from comanda where nr_comanda=:s',[id_cmd])
    data=cur.fetchone()
    cant_returnat=data[0]
    id_produs=data[1]

    cur.execute('delete from comanda where nr_comanda=:s', [id_cmd])

    cur.execute('SELECT cantitate_stoc from stoc where id_produs=:s',[id_produs])
    data=cur.fetchone()
    cant_disp=data[0]

    cant_noua=cant_returnat+cant_disp
    cur.execute('UPDATE stoc SET cantitate_stoc=:s where id_produs=:t',[cant_noua,id_produs])

    cur.execute('commit')

    return redirect('/stoc')

@app.route('/stoc')
def stoc():
    stoc = []

    cur = con.cursor()
    cur.execute('SELECT id_produs,id_furnizor, nume_produs, pret, cantitate_stoc, detalii_produs from stoc')
    for result in cur:
        i={}
        i['id_produs'] = result[0]
        i['nume_produs'] = result[2]
        i['pret'] = result[3]
        i['cantitate'] = result[4]
        i['descriere_produs']=result[5]
        cur2=con.cursor()
        cur2.execute('SELECT nume_furnizor from furnizori where id_furnizor=:s',[result[1]])
        id_f=cur2.fetchone()
        i['nume_furnizor']=id_f[0]
        stoc.append(i)

    cur.close()
    return render_template('stoc.html', stoc=stoc)

@app.route('/addstoc',methods=['GET','POST'])
def add_stoc():
    if request.method=="POST":
        cur=con.cursor()
        values=[]

        values.append("'" + request.form['furnizor'] + "'")
        values.append("'" + request.form['nume'] + "'")
        values.append("'" + request.form['pret'] + "'")
        values.append("'" + request.form['cantitate'] + "'")
        values.append("'" + request.form['detalii_produs'] + "'")

        query='INSERT INTO stoc VALUES(null, %s)' %(', '.join(values))
        cur.execute(query)

        cur.execute('commit')

        return redirect('/stoc')

    else:
        cur=con.cursor()
        cur.execute('SELECT id_furnizor,nume_furnizor from furnizori')
        furnizori=[]
        for i in cur:

            furnizor={}
            furnizor['id_furnizor']=i[0]
            furnizor['nume_furnizor']=i[1]
            furnizori.append(furnizor)
        return render_template('addstoc.html', furnizori=furnizori)


@app.route('/getstoc',methods=['POST'])
def get_stoc():
    id_p = request.form['valoare_buton1']
    cur = con.cursor()

    cur.execute('select * from stoc where id_produs=:c', c=id_p)
    data = cur.fetchone()
    id_furnizor_selectat = data[1]
    nume = data[2]
    pret = data[3]
    cantitate = data[4]
    detalii=data[5]

    cur.execute('SELECT nume_furnizor from furnizori where id_furnizor=:s', [id_furnizor_selectat])
    f=cur.fetchone()
    nume_furnizor_selectat=f[0]

    cur.execute('SELECT id_furnizor,nume_furnizor from furnizori where id_furnizor<>:s',[id_furnizor_selectat])
    furnizori = []
    for i in cur:
        furnizor = {}
        furnizor['id_furnizor'] = i[0]
        furnizor['nume_furnizor'] = i[1]
        furnizori.append(furnizor)

    cur.close()

    return render_template('editstoc.html', id_produs=id_p, furnizori=furnizori, nume_furnizor_selectat=nume_furnizor_selectat, id_furnizor_selectat=id_furnizor_selectat, nume=nume, pret=pret, cantitate=cantitate, detalii_produs=detalii)


@app.route('/editstoc',methods=['POST'])
def edit_stoc():
    cur = con.cursor()

    id_p = request.form['id_produs']
    nume = request.form['nume']
    id_furnizor=request.form['furnizor']
    pret=request.form['pret']
    cantitate=request.form['cantitate']
    detalii=request.form['detalii_produs']

    query = 'UPDATE stoc SET id_furnizor=:a, nume_produs=:b, pret=:c, cantitate_stoc=:d, detalii_produs=:e where id_produs=:f'
    cur.execute(query, [id_furnizor,nume,pret,cantitate,detalii, id_p])

    cur.execute('commit')

    return redirect('/stoc')

@app.route('/delstoc', methods=['POST'])
def del_stoc():
    cur=con.cursor()
    id_p=request.form['valoare_buton']

    cur.execute('delete from stoc where id_produs=:s', [id_p])
    cur.execute('commit')

    return redirect('/stoc')


@app.route('/furnizori')
def furnizori():
    furnizori = []

    cur = con.cursor()
    cur.execute('SELECT * from furnizori ORDER BY nume_furnizor')
    for result in cur:
        i = {}
        i['id_furnizor'] = result[0]
        i['nume_furnizor'] = result[1]
        furnizori.append(i)

    cur.close()
    return render_template('furnizori.html', furnizori=furnizori)

@app.route('/addfurnizor',methods=['POST', 'GET'])
def add_furnizor():
    if request.method == 'POST':
        cur = con.cursor()
        nume=request.form['nume']

        cur.execute('INSERT INTO furnizori VALUES (null,:s)', [nume])
        cur.execute('commit')

        return redirect('/furnizori')
    else:
        return render_template('addfurnizor.html')


@app.route('/getfurnizor',methods=['POST'])
def get_furnizor():
    id_f = request.form['valoare_buton1']
    cur = con.cursor()
    cur.execute('select nume_furnizor from furnizori where id_furnizor=:c', c=id_f)
    data = cur.fetchone()
    nume = data[0]

    cur.close()

    return render_template('editfurnizor.html', id_furnizor=id_f, nume=nume)


@app.route('/editfurnizor',methods=['POST'])
def edit_furnizor():
    cur = con.cursor()

    id_f = request.form['id_furnizor']
    nume = request.form['nume']

    query = 'UPDATE furnizori SET nume_furnizor=:t where id_furnizor=:r'
    cur.execute(query, [nume, id_f])

    cur.execute('commit')

    return redirect('/furnizori')

@app.route('/delfurnizor',methods=['POST'])
def del_furnizor():
    cur=con.cursor()
    id_f=request.form['valoare_buton']

    cur.execute('delete from furnizori where id_furnizor=:f', [id_f])
    cur.execute('commit')

    return redirect('/furnizori')


# main
if __name__ == '__main__':
    app.run(debug=True)
    con.close()
