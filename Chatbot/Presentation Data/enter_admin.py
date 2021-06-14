import sqlite3 

def add(name,email,password,bot_name):
    cur=sqlite3.connect('Data/admin.db')
    c=cur.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        bot_name TEXT
    )
    """)
    sql = """INSERT INTO admin(name, email,password,bot_name) VALUES ("{}","{}","{}","{}");""".format(name,email,password,bot_name)
    c.execute(sql)
    cur.commit()
    cur.close()	

    print("Successfully added admin",name,"for",bot_name)
    print('Please change the password after first use')


if __name__=="__main__":
    print('Enter Bot Name : ',end="")
    bot_name=input()
    print("Enter Admin Name : ",end="")
    name=input()
    print("Enter email : ",end="")
    email=input()
    print("Enter password : ",end="")
    password=input()
    add(name,email,password,bot_name)
    