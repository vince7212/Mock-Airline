from flask import Flask, g, render_template, request, jsonify, redirect, url_for, session
# from wtforms import BooleanField
# from wtforms.validators import DataRequired

import werkzeug, os
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2 import pool
import json

# Read username and password from password.txt file
with open('password.txt') as f:
    lines = [line.rstrip() for line in f]
    
username = lines[0]
pg_password = lines[1]

qsqlfile = open("query.sql", "w")
tsqlfile = open("transaction.sql", "w")


# Generates 6 digit id for book_ref
def GenerateBookRef(id):
    book_ref = str(id)
    book_ref = book_ref.zfill(6)
    return book_ref

# Generates 13 digit id for ticket_no
def GenerateTicketNum(id):
    ticket_no = str(id)
    ticket_no = ticket_no.zfill(13)
    return ticket_no

# Sql query statement to insert book_refs into bookings table
def InsertBookingsTable(book_ref, cost):
    query = "INSERT INTO bookings\n"
    query += "VALUES ('" + book_ref + "', current_timestamp," + cost + ");\n"
    return query

# Sql query statement to check whether flight is valid
# Count will be larger than 0 if flight exists otherwise it will equal to 0 and return false
def CheckValidFlightID(flight_id, cursor, sqlfile):
    query = "SELECT COUNT(*)\nFROM flights\nWHERE flight_id = " + flight_id + ";\n" 
    sqlfile.write(query + "\n")
    cursor.execute(query)
    result = cursor.fetchone()[0]
    if result > 0:
        return 1
    else:
        return 0

# Checks whether flight has avaiable seats
# Selects remaining seats available in flight, if remaining seats is larger than 0 returns true, otherwise returns false
def CheckAvailableFlight(flight_id, cursor, sqlfile):
    query = "SELECT seats_available\nFROM flights\nWHERE flight_id = " + flight_id + ";\n"
    sqlfile.write(query + "\n")
    cursor.execute(query)
    result = cursor.fetchone()[0]
    if result > 0:
        return 1
    else:
        return 0

# Sql query statement for inserting book_ref, ticket_no, and passenger_id into ticket table
def InsertTicketTable(book_ref, ticket_no, passenger_id):
    query = "INSERT INTO ticket\n"
    query += "VALUES ('" + ticket_no + "', '" + book_ref + "', '" + passenger_id + "', 'PASSENGER NAME', NULL, NULL);\n"
    return query

# Sql query statement for inserting ticket_no, and flight_id into ticketflights table
def InsertTicketFlightsTable(ticket_no, flight_id, cost):
    query = "INSERT INTO ticket_flights\n"
    if int(cost) == 200:
        fare_cond = "Economy"
    elif int(cost) == 300:
        fare_cond = "Business"
    else:
        fare_cond = "First Class"
    query += "VALUES ('" + ticket_no + "', '" + flight_id + "', '" + fare_cond + "', " + cost + ");\n"
    return query

# Sql query statement for updating the flights table and incrementing seats booked and decrementing seats available
def UpdateFlightsTable(flight_id):
    query = "UPDATE flights\n"
    query += "SET seats_available = seats_available - 1, seats_booked = seats_booked + 1\nWHERE flight_id = " + flight_id + ";\n"
    return query


def create_app():
    app = Flask(__name__)

    app.config['postgreSQL_pool'] = psycopg2.pool.SimpleConnectionPool(1, 20,
        user = username,
        password = pg_password,
        host = "code.cs.uh.edu",
        port = "5432",
        database = "COSC3380")

    def get_db():
        print ('GETTING CONN')
        if 'db' not in g:
            g.db = app.config['postgreSQL_pool'].getconn()
        return g.db

    @app.teardown_appcontext
    def close_conn(e):
        print('CLOSING CONN')
        db = g.pop('db', None)
        if db is not None:
            app.config['postgreSQL_pool'].putconn(db)

    @app.route("/", methods=["POST", "GET"])
    def home():
        if request.method == "POST":
            departure_city = request.form["dc"]
            arrival_city = request.form["ac"]
            dic = {
                'd' : departure_city,
                'a': arrival_city
            }
            session['places'] = dic
            return redirect(url_for('selectflights'))
        else:
            return render_template("index.html")

    @app.route("/<name>")
    def user(name):
        return f"Hello {name}!"
 
    @app.route("/availableflights", methods=["POST", "GET"])
    def selectflights():
        dic = session.get('places', "")
        d = dic['d']
        a = dic['a']
        db = get_db()
        cursor = db.cursor()
        query = "SELECT flight_id, scheduled_departure, scheduled_arrival, departure_airport, d.city, arrival_airport, a.city, seats_available, seats_booked\n"
        query += "FROM flights\nJOIN airport as d ON flights.departure_airport = d.airport_code\nJOIN airport as a ON flights.arrival_airport = a.airport_code\n"
        query += "WHERE lower(d.city) LIKE '%" + d.lower() + "%' AND lower(a.city) LIKE '%"+ a.lower() + "%'\n"
        query += "ORDER BY flight_id;\n\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchall()
        if request.method == "POST":
            return redirect("http://127.0.0.1:5000/list", code=302)        
        else:
            return render_template("availableflights.html", data=data)
    
    @app.route("/flights", methods=["POST", "GET"])
    def displayflights():
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM flights ORDER BY flight_id;\n\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchall()
        return render_template("flights.html", data=data)

    @app.route("/bookings", methods=["POST", "GET"])
    def displaybookings():
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM bookings;\n\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchall()
        return render_template("bookings.html", data=data)

    @app.route("/boarding_passes", methods=["POST", "GET"])
    def displayboardingpasses():
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM boarding_passes;\n\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchall()
        return render_template("boardingpass.html", data=data)

    @app.route("/seats", methods=["POST", "GET"])
    def displayseats():
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM seats;\n\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchall()
        return render_template("seats.html", data=data)

    @app.route("/tickets", methods=["POST", "GET", "DELETE"])
    def displaytickets():
        db = get_db()
        cursor = db.cursor()
        query = "SELECT * FROM ticket;\n\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchall()
        if request.method == "DELETE":
            d = request.get_json()
            ticket_no = d["ticket_no"]
            query = "SELECT flight_id FROM ticket_flights\nWHERE ticket_no = '" + ticket_no + "';\n\n"
            qsqlfile.write(query)
            cursor.execute(query)
            flight_id = cursor.fetchone()[0]
            
            query = "SELECT seat_no FROM boarding_passes\nWHERE ticket_no = '" + ticket_no + "';\n\n"
            qsqlfile.write(query)
            cursor.execute(query)
            seat_no = cursor.fetchone()[0]
            
            query = "START TRANSACTION;"
            query += "DELETE FROM boarding_passes\nWHERE seat_no = '" + seat_no + "';\n\n"
            query += "DELETE FROM ticket_flights\nWHERE ticket_no = '" + ticket_no + "';\n\n"
            query += "DELETE FROM ticket\nWHERE ticket_no = '" + ticket_no + "';\n\n"
            query += "DELETE FROM seats\nWHERE seat_no = '" + seat_no + "';\n\n"
            
            query += "UPDATE flights\n"
            query += "SET seats_available = seats_available + 1, seats_booked = seats_booked - 1\nWHERE flight_id = '" + str(flight_id) + "';\n"
            query += "COMMIT;"
            qsqlfile.write(query)
            tsqlfile.write(query)
            cursor.execute(query)
        return render_template("tickets.html", data=data)
    

    @app.route("/list", methods =["POST", "GET"] )
    def printlist():
        l = request.get_json()
        session['info'] = l
        return "none"

    @app.route("/ticket", methods =["POST", "GET"])
    def create_ticket():
        information = session.get('info', "")
        passnum = int(information['passnum'])
        flight_id = (information['flight_id'])
        cost = information['cost']
        x = range(passnum)
        
        if request.method == "POST":
            fname_list = request.form.getlist('fname')
            lname_list = request.form.getlist('lname')
            contact_list = request.form.getlist('contact')
            phone_list = request.form.getlist('phone')

            dictionary = {
                'fname': fname_list,
                'lname': lname_list,
                'contact':contact_list,
                'phone': phone_list
            }
            session['pass_info'] = dictionary

            return redirect("http://127.0.0.1:5000/checkout", code=302)
        return render_template("ticket.html", passnum = x)
    

    @app.route("/checkout", methods = ["POST", "GET"])
    def pricing():
        global seat_l
        passenger_info = session.get('pass_info', "")
        information = session.get('info', "")
        passnum = int(information['passnum'])
        total = int(information['total'])
        cost = information['cost']
        flight_id = information['flight_id']
        fare_cond = information['fare_cond']
        fname_list = passenger_info['fname']
        lname_list = passenger_info['lname']
        contact_list = passenger_info['contact']
        phone_list = passenger_info['phone']
        seat_list = []
        db = get_db()
        cursor = db.cursor()

        for i in range(passnum):
            
            query = "SELECT count_id FROM variables;"
            qsqlfile.write(query)
            cursor.execute(query)
            count = cursor.fetchone()[0]
            
            query = "SELECT char_letter FROM variables;"
            qsqlfile.write(query)
            cursor.execute(query)
            seat_l = cursor.fetchone()[0]
            if (count % 6 == 0 and count != 0):
                seat_l = chr(ord(seat_l)+ 1) 
                query = "UPDATE variables SET char_letter = '" + seat_l + "';"
                qsqlfile.write(query)
                tsqlfile.write(query)
                cursor.execute(query)
            seat_n = count % 6
            seat = seat_l + str(seat_n)
            seat_list.append(seat)
            query = "SELECT aircraft_code FROM flights WHERE flight_id = " + flight_id + ";"
            qsqlfile.write(query)
            cursor.execute(query)
            aircraft_code = cursor.fetchone()[0]
            ticket_no = GenerateTicketNum(count)
            book_ref = GenerateBookRef(count)
            boarding_id = book_ref
            passenger_id = GenerateBookRef(count)
            
            s = "START TRANSACTION;\n\n"
            s += InsertBookingsTable(book_ref, cost) + "\n"
            s += "INSERT INTO ticket\n"
            s += "VALUES ('" + ticket_no + "', '" + book_ref + "', '" + passenger_id + "', '"+ fname_list[i] + " " + lname_list[i] + "','" + contact_list[i] +"', '"+ phone_list[i] +"');\n\n"
            s += InsertTicketFlightsTable(ticket_no, flight_id, cost) + "\n"
            s += UpdateFlightsTable(flight_id) + "\n"
            s += "INSERT INTO boarding_passes\nVALUES ('" + ticket_no + "', '" + flight_id + "', '" + boarding_id + "', '" + seat + "');\n" 
            s += "COMMIT;\n\n"
            s += "INSERT INTO seats\nVALUES ('" + aircraft_code + "', '" + seat + "', '" + fare_cond + "');\n" 
            s += "COMMIT;\n\n"
            qsqlfile.write(s)
            tsqlfile.write(s)
            cursor.execute(s)
            query = "UPDATE variables SET count_id = count_id + 1"
            cursor.execute(query)

        query = "SELECT flight_id, scheduled_departure, scheduled_arrival, departure_airport, d.city, arrival_airport, a.city\n"
        query += "FROM flights\nJOIN airport as d ON flights.departure_airport = d.airport_code\nJOIN airport as a ON flights.arrival_airport = a.airport_code\n"
        query += "WHERE flight_id = '" + flight_id + "'\n"
        qsqlfile.write(query)
        cursor.execute(query)
        data = cursor.fetchone()
        
        # if request.method == "GET":
        #     return redirect(url_for('thankyou'))
        return render_template("checkout.html", data = data, total = total, passnum = passnum, fare_cond = fare_cond, seat_list = seat_list)
    
    @app.route("/thankyou", methods=["POST", "GET"])
    def thankyou():
        return render_template("thankyou.html")
    
    @app.route("/contact", methods=["POST", "GET"])
    def contact():
        return render_template("contact.html")

    @app.route('/updateDB/', methods=['POST'])    
    def updateDB():
        data = request.get_json()        # retrieve data from ajax
        db = get_db()                # connect to db
        cursor = db.cursor()

        # do something 
        # (e.g. cursor.execute("select * from flights;))

        cursor.close()

        return jsonify(data)

    return app

if __name__ == '__main__':
    app = create_app()
    app.secret_key = os.urandom(24)
    app.run(debug=True)
    qsqlfile.close()
    tsqlfile.close()