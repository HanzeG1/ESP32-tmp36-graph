from flask import Flask, render_template, Markup
from threading import Thread
import socket

import sqlite3
import time
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def run_time():
    """Really does nothing but
    makes you able to actually
    exit the app.
    Couldn't find a different easy
    way and this works.

    Is it probably bad code? Yes.
    """
    # Wait a split second because the other 2 also
    # output some lines
    time.sleep(0.1)
    # wait for input of some kind
    while True:
        input()

app = Flask(__name__)

def get_temperature():
    """An edited version of shoutingserver.py
    that also inserts its data into a database.
    """

######################################
    HOST = "192.168.178.10" # Jouw IP
######################################
    PORT = 4000
    ALLOK = "OK"
    ALARM = "LIGHT_ON"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        print("Binding done, waiting for client")
        s.listen()
        conn, addr = s.accept()
        with conn:
            print("Connected by", addr)
            while True:
                data = conn.recv(1024)
                message = data.decode("utf-8")
                print("Received data: ", message)
                if not data:
                    break

                # Input the data into the database
                db = sqlite3.connect("temp.db", detect_types=sqlite3.PARSE_DECLTYPES)
                cursor_db = db.cursor()
                cursor_db.execute(f"INSERT INTO data VALUES ('{time.ctime()}', {int(message)});")
                db.commit()
                db.close()

                if int(data) <= 21:
                    conn.send(ALLOK.encode("utf-8"))
                    print(ALLOK, "sent")
                else:
                    conn.send(ALARM.encode("utf-8"))
                    print(ALARM, "sent")
                

@app.route('/', methods=['GET', 'POST'])
def index():
    """Renders the chart and table
    """
    # Define variables
    graphdata = []
    labels = []
    temp_list = []

    # Get the input from the database
    db = sqlite3.connect("temp.db", detect_types=sqlite3.PARSE_DECLTYPES)
    cursor_db = db.cursor()
    search_action = cursor_db.execute('SELECT date, temp FROM data')
    for row in search_action:
        temp_list.append(row)
        if row[0][:10] == time.ctime()[:10]:
            labels.append(row[0][11:-8])
            graphdata.append(row[1])
    db.close()

    labels = Markup(labels)
    currtemp = temp_list[-1][1]

    # render template
    return render_template('index.html',
        temp_list=temp_list,
        currtemp=currtemp,
        graphdata=graphdata,
        labels=labels
        )

if __name__ == "__main__":
    # Main thread
    main = Thread(target=run_time)

    # Starts getting input
    record = Thread(target=get_temperature)
    record.setDaemon(True)

    # Start the webpage
    web = Thread(target=app.run)
    web.setDaemon(True)

    # Start the threads
    main.start()
    record.start()
    web.start()
