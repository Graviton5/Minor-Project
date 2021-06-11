from flask import Flask,url_for,session,render_template,request,redirect,flash
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "Asdvbh273vwuy723"

def verify(email,password):
    cur = sqlite3.connect('Data/admin.db')
    c=cur.cursor()
    sql="SELECT count(name) FROM sqlite_master WHERE type='table' AND name='admin' "
    c.execute(sql)
    if c.fetchone()[0]==1:
        sql="""SELECT * FROM admin WHERE email="{}";""".format(email)
        c.execute(sql)
        rows=c.fetchall()
        cur.commit()
        cur.close()
        if len(rows)==0:
            return [False]
        row=rows[0]
        if password==row[3]:
            return [True,row[0],row[1],row[2],row[4]]
        else:
            return [False]
    cur.commit()
    cur.close()
    return [False]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/',methods=['POST',"GET"])
def login():
    if request.method=="POST":
        email=request.form['email']
        password=request.form['pwd']
        check=verify(email,password)
        if check[0]:
            session['user']=True
            session['uname']=check[2]
            session['email']=check[3]
            session['bot_name']=check[4]
            session['uid']=check[1]
            return redirect(url_for('main'))
        else:
            flash("Incorrect email or password...!")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/main/')
def main():
    if session['user']:
        list1=[]
        list2=[]
        list3=[]
        with open('Data/intent_queries_Botto.json') as f:
            data = json.load(f)
            for i in data['intents']:
                list1.append(i)
            for i in data['Queries']['QueryNames']:
                list2.append(i)
            for i in data['Queries']['QueryTypes']:
                list3.append(i)
        cur=sqlite3.connect('Data/SelfLearn.db')
        c=cur.cursor()
        sql="SELECT count(name) FROM sqlite_master WHERE type='table' AND name='selfLearn' "
        c.execute(sql)
        rows=[]
        if c.fetchone()[0]==1:
            sql="""SELECT num,query,response FROM selfLearn;"""
            c.execute(sql)
            rows=c.fetchall()
        cur.commit()
        cur.close()
        return render_template('main.html',entries=rows,len_entries=len(rows),intents=list1,queryNames=list2,queryTypes=list3)
    else:
        return redirect(url_for('index'))

@app.route('/updated/',methods=['POST',"GET"])
def updated():
    if request.method=="POST":
        list1=[]
        list2=[]
        list3=[]
        with open('Data/intent_queries_Botto.json') as f:
            data = json.load(f)
            for i in data['intents']:
                list1.append(i)
            for i in data['Queries']['QueryNames']:
                list2.append(i)
            for i in data['Queries']['QueryTypes']:
                list3.append(i)
        de=[]
        acc=[]
        for name in request.form:
            if name[:3]=="set":
                if request.form[name]=='1':
                    de.append(int(name[3:]))
                if request.form[name]=='2':
                    acc.append(int(name[3:]))
        cur=sqlite3.connect('Data/SelfLearn.db')
        c=cur.cursor()
        sql="SELECT count(name) FROM sqlite_master WHERE type='table' AND name='selfLearn' "
        c.execute(sql)
        rows=[]
        if c.fetchone()[0]==1:
            sql="""SELECT num,query,response FROM selfLearn;"""
            c.execute(sql)
            rows=c.fetchall()
            sql_data={}
            for a in rows:
                sql_data[a[0]]=a
            for i in acc:
                if request.form['intent'+str(i)][0]=='1':
                    if request.form['intent'+str(i)]=='1intents_other':
                        data['intents'][request.form['other'+str(i)]]={
                            "text":[sql_data[i][1]],
                            "responses":[sql_data[i][2]]
                        }
                    else:
                        data['intents'][request.form['intent'+str(i)][1:]]['text'].append(sql_data[i][1])
                        data['intents'][request.form['intent'+str(i)][1:]]['responses'].append(sql_data[i][2])
                elif request.form['intent'+str(i)][0]=='2':
                    if request.form['intent'+str(i)]=='2queryNames_other':
                        data['Queries']['QueryNames'][request.form['other'+str(i)]]={
                            "text":[sql_data[i][1]],
                            "responses":[sql_data[i][2]]
                        }
                    else:
                        print(sql_data[i],data['Queries']['QueryNames'][request.form['intent'+str(i)][1:]])
                        data['Queries']['QueryNames'][request.form['intent'+str(i)][1:]].append(sql_data[i][1])
                        #data['Queries']['QueryNames'][request.form['intent'+str(i)][1:]]['responses'].append(sql_data[i][2])
                elif request.form['intent'+str(i)][0]=='3':
                    if request.form['intent'+str(i)]=='3queryTypes_other':
                        data['Queries']['QueryTypes'][request.form['other'+str(i)]]={
                            "text":[sql_data[i][1]],
                            "responses":[sql_data[i][2]]
                        }
                    else:
                        data['Queries']['QueryTypes'][request.form['intent'+str(i)][1:]].append(sql_data[i][1])
                        #data['Queries']['QueryTypes'][request.form['intent'+str(i)][1:]]['responses'].append(sql_data[i][2])
            with open("Data/intent_queries_Botto.json", "w") as outfile:
                outfile.write(json.dumps(data,indent=4))
            #with open("Data/intent_queries_ANN_Botto.json", "w") as outfile:
            #    outfile.write(json.dumps(data,indent=4))
            n=len(acc)
            for i in range(n):
                acc[i]=str(acc[i])
            n=len(de)
            for i in range(n):
                acc.append(str(de[i]))
            query = "DELETE FROM selfLearn WHERE num IN ({})".format(", ".join(acc))
            c.execute(query)
            cur.commit()
            cur.close()
    return redirect(url_for('main'))
    


@app.route('/change_pass_page/')
def change_pass_page():
    if session['user']:
        return render_template('change_password.html')
    else:
        return redirect(url_for('index'))

@app.route('/change_pass_request/',methods=['POST',"GET"])
def change_password():
    if request.method=="POST":
        opwd=request.form['opwd']
        pwd=request.form['pwd']
        cpwd=request.form['cpwd']
        if cpwd==pwd:
            cur=sqlite3.connect('Data/admin.db')
            c=cur.cursor()
            sql="""SELECT password FROM admin WHERE id="{}";""".format(session['uid'])
            c.execute(sql)
            row=c.fetchall()[0]
            if row[0]==opwd:
                sql="""UPDATE admin SET password="{}" WHERE id="{}";""".format(pwd,session['uid'])
                c.execute(sql)
            else:
                cur.commit()
                cur.close()
                return redirect(url_for('change_pass_page'))
            cur.commit()
            cur.close()
            return redirect(url_for('main'))
        else:
            return redirect(url_for('change_pass_page'))
    else:
        return redirect(url_for('index'))

@app.route('/logout/')
def logout():
    if session['user']:
        session['user']=False 
        session.pop('uname')
        session.pop('bot_name')
        session.pop('uid')
        session.pop('email')
    return redirect(url_for('index'))

if __name__=="__main__":
    app.run(port="5001",debug=True)