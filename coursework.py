import psycopg2
from flask import Flask, render_template, request

app = Flask(__name__)


def getConn():
    pwFile = open("pw.txt", "r")
    pw = pwFile.read();
    pwFile.close()
    connStr = "dbname= 'Coursework' user='postgres' password= " + pw
    conn = psycopg2.connect(connStr)
    return conn


@app.route('/')
def home():
    return render_template('home.html')

#1 - create a new Customer record.
@app.route('/addCustomer', methods=['POST'])
def addEmployee():
    conn = None
    try:
        customerid = request.form['customerid']
        name = request.form['name']
        email = request.form['email']

        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path to coursework')
        cur.execute('INSERT INTO customer VALUES (%s, %s, %s)', [customerid, name, email])
        conn.commit()

        return render_template('home.html', msg='Customer Added')
    except Exception as e:
        return render_template('home.html', msg='Customer NOT Added ', error=e)
    finally:
        if conn:
            conn.close()

#2 - Create a new support ticket for a customer with respect to a given product. 
@app.route('/createTicket', methods=['POST'])
def createTicket():
    conn = None
    try:
        ticketid = request.form['ticketid']
        productid = request.form['productid']
        priority = request.form['priority']
        problem = request.form['problem']
        customerid = request.form['customerid']

        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path to coursework')

        cur.execute("INSERT INTO ticket (ticketid, problem, priority, customerid, productid) \
                    VALUES (%s, %s, %s, %s, %s)", [ticketid, problem, priority, customerid, productid])
        conn.commit()
        cur.execute('SELECT * FROM ticket WHERE ticketid = %s', [ticketid])

        colNames = [desc[0] for desc in cur.description]
        data = cur.fetchall()

        return render_template('tables.html', data=data, colNames=colNames, msg="Ticket Created")
    except Exception as e:
        return render_template('home.html', error=e)
    finally:
        if conn:
            conn.close()

#3 - Add an update to the support ticket from a given staff member.
@app.route('/updateTicket', methods=['POST'])
def updateTicket():
    conn = None
    try:
        ticketupdateid = request.form['ticketupdateid']
        message = request.form['message']
        ticketid = request.form['ticketid']
        staffid = request.form['staffid']
        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path TO coursework')

        cur.execute('INSERT INTO ticketupdate (ticketupdateid, message, ticketid, staffid) \
                    VALUES (%s, %s, %s, %s)', [ticketupdateid, message, ticketid, staffid])
        conn.commit()

        return render_template('home.html', msg='Ticket Updated')
    except Exception as e:
        return render_template('home.html', error=e, msg='Ticket NOT Updated')
    finally:
        if conn:
            conn.close()

#4 - List all outstanding support tickets along with the time of the last update
@app.route('/showOpenTickets', methods=['GET'])
def showOpenTickets():
    conn = None
    try:
        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path TO coursework')

        cur.execute("SELECT ticket.ticketid, status, MAX(updatetime) AS lastupdate FROM ticket \
                    LEFT JOIN ticketupdate ON ticket.ticketid = ticketupdate.ticketid \
                    WHERE status = 'open' GROUP BY ticket.ticketid, status")

        colNames = [desc[0] for desc in cur.description]
        data = cur.fetchall()

        return render_template('tables.html', data=data, colNames=colNames, msg='Open Tickets')
    except Exception as e:
        return render_template('home.html', error=e)
    finally:
        if conn:
            conn.close()

#5 - Set the status of a support ticket to closed.
@app.route('/closeTicket', methods=['POST'])
def closeTicket():
    conn = None
    try:
        ticketid = request.form['ticketid']
        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path TO coursework')

        cur.execute("UPDATE ticket SET status = 'closed' WHERE ticketid = %s", [ticketid])
        conn.commit()

        return render_template('home.html', msg = 'Ticket Closed')
    except Exception as e:
        return render_template('home.html', error=e)
    finally:
        if conn:
            conn.close()

#6 - List the original problem as the question along with all updates in chronological order. 
@app.route('/ticketUpdates', methods=['GET'])
def ticketUpdates():
    conn = None
    try:
        ticketid = request.args['ticketid']
        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path TO coursework')

        cur.execute("SELECT problem AS question, CASE WHEN ticketupdate.staffid IS NULL THEN customer.name \
                    ELSE staff.name END AS author_name, message, updatetime FROM ticketupdate INNER JOIN \
                    ticket ON ticketupdate.ticketid = ticket.ticketid INNER JOIN customer \
                    ON ticket.customerid = customer.customerid \
                    LEFT JOIN staff ON ticketupdate.staffid = staff.staffid \
                    WHERE ticketupdate.ticketid = %s ORDER BY updatetime", [ticketid])

        colNames = [desc[0] for desc in cur.description]
        data = cur.fetchall()

        return render_template('tables.html', data=data, colNames=colNames, msg='Ticket Updates')
    except Exception as e:
        return render_template('home.html', error=e)
    finally:
        if conn:
            conn.close()

#7 - Produce a report showing the status of each closed support ticket.
@app.route('/ticketReport', methods=['GET'])
def ticketReport():
    conn = None
    try:
        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path TO coursework')

        cur.execute("SELECT ticket.ticketid, COUNT(message) AS num_updates, MIN(updatetime - loggedtime) \
                    AS first_update, MAX(updatetime - loggedtime) AS last_update FROM ticket \
                    LEFT JOIN ticketupdate ON ticket.ticketid = ticketupdate.ticketid WHERE status = 'closed' \
                    GROUP BY ticket.ticketid")

        colNames = [desc[0] for desc in cur.description]
        data = cur.fetchall()

        return render_template('tables.html', data=data, colNames=colNames, msg='Closed Tickets Report')
    except Exception as e:
        return render_template('home.html', error=e)
    finally:
        if conn:
            conn.close()

#8 - Permanantly remove the customer’s details.
#    Should not be possible while the customer is associated with any tickets.
@app.route('/removeCustomer', methods=['GET'])
def removeCustomer():
    conn = None
    try:
        customerid = request.args['customerid']
        conn = getConn()
        cur = conn.cursor()
        cur.execute('SET search_path TO coursework')

        cur.execute("DELETE FROM customer WHERE customerid = %s", [customerid])
        conn.commit()

        return render_template('home.html', msg='Customer Removed')
    except Exception as e:
        return render_template('home.html', error=e, msg='Customer NOT Removed')
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(debug=True)
