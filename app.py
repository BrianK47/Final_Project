import mysql

#importing flask and mysql.connector
from flask import Flask, render_template, request, redirect, url_for, make_response
import mysql.connector

#import datetime and calendar
from datetime import datetime
import calendar

# instantiate the app
app = Flask(__name__)

# Connect to the database
mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='CAS!2345',
    database='last_resort'
)


# set up routes

@app.route('/')
def home():
    current_date = datetime.now().strftime("%B %d, %Y")
    return render_template(
        'index.html',
        current_date=current_date)

@app.route('/customers')
def customers():
    current_date = datetime.now().strftime("%B %d, %Y")

    cursor = mydb.cursor()
    query = ("""SELECT customer.customerId, customer.customerName, SUM(bill.amount) AS totalSpent FROM customer
                JOIN reservation  
                ON customer.customerId = reservation.customerId 
                JOIN bill 
                ON reservation.reservationId = bill.reservationId 
                GROUP BY customer.customerId
                ORDER BY totalSpent DESC LIMIT 5;
                """)

    cursor.execute(query)
    customers = cursor.fetchall()
    return render_template('customers.html',
                           current_date=current_date, customers=customers)

@app.route('/revenue')
def revenue():
    current_date = datetime.now().strftime("%B %d, %Y")

    cursor = mydb.cursor()
    query = ("""SELECT chainName, SUM(bill.amount) AS chainRevenue
                FROM bill
                JOIN reservation
                ON bill.reservationId = reservation.reservationId
                JOIN hotel
                ON reservation.hotelId = hotel.hotelId
                JOIN chain 
                On hotel.chainId = chain.chainId
                WHERE reservation.endDate BETWEEN '2024-01-01' AND '2024-12-31' 
                GROUP BY chain.chainId
                ORDER BY chainRevenue DESC LIMIT 3
                ; """)

    cursor.execute(query)
    top_hotels = cursor.fetchall()

    return render_template('revenue.html',
                           current_date=current_date, top_hotels=top_hotels)

@app.route('/services')
def services():
    current_date = datetime.now().strftime("%B %d, %Y")

    cursor = mydb.cursor()
    query="""SELECT service.serviceDescription, COUNT(service.serviceCode) AS serviceCount
             FROM service
             JOIN bill_detail
             ON service.serviceCode = bill_detail.serviceCode
             WHERE bill_detail.date BETWEEN '2024-01-01' AND '2024-12-31'
             GROUP BY service.serviceCode, service.serviceDescription
             ORDER BY COUNT(service.serviceCode) DESC LIMIT 5;
             """
    cursor.execute(query)
    services_raw = cursor.fetchall()
    top_services = []
    for service in services_raw:
        serviceDescription = service[0].capitalize()
        top_services.append((serviceDescription, service[1]))

    return render_template('services.html',
                           current_date=current_date, top_services=top_services)

"""
@app.route('/month', methods=['GET','POST'])
def month():
    current_date = datetime.now().strftime("%B %d, %Y")

    cursor = mydb.cursor()
    query = SELECT MONTH(reservation.startDate) AS month, SUM(bill.amount) AS totalSpending
                FROM bill
                JOIN reservation
                ON bill.reservationId = reservation.reservationId
                GROUP BY MONTH (reservation.startDate)
                ORDER BY totalSpending LIMIT 1;
         

    cursor.execute(query)

    #extract the month number
    query_result = cursor.fetchone()
    month_number = query_result[0]
    month_name = calendar.month_name[month_number]

    return render_template('month.html',
                           current_date=current_date, query_result = query_result, month_name = month_name)
"""

@app.route('/month', methods=['GET','POST'])
def month():
    current_date = datetime.now().strftime("%B %d, %Y")
    cursor = mydb.cursor()

    hotel_query = "SELECT hotelName, hotelId FROM hotel;"
    cursor.execute(hotel_query)
    hotels = cursor.fetchall()

    years = ['2024','2023','2022']


    hotel_info = None
    selected_hotel = None
    selected_year = None
    selected_hotel_name = None

    if request.method == 'POST':
        selected_hotel = int(request.form.get('hotel'))
        selected_hotel_name = next((hotel[0] for hotel in hotels if hotel[1] == selected_hotel),None)
        selected_year = request.form.get('year')

        if selected_hotel and selected_year:
            start_date = f"{selected_year}-01-01"
            end_date = f"{selected_year}-12-31"

            query = """
                            SELECT MONTH(reservation.startDate) AS month, SUM(bill.amount) AS totalSpending
                            FROM bill
                            JOIN reservation
                            ON bill.reservationId = reservation.reservationId
                            WHERE reservation.startDate BETWEEN %s AND %s
                            AND reservation.hotelId = %s
                            GROUP BY MONTH(reservation.startDate)
                            ORDER BY totalSpending ASC
                            LIMIT 1;
                        """
            cursor.execute(query, (start_date, end_date, selected_hotel))
            hotel_info = cursor.fetchone()

    return render_template(
        'month.html',
        current_date = current_date,
        hotels=hotels,
        years=years,
        selected_hotel=selected_hotel,
        selected_year=selected_year,
        hotel_info=hotel_info,
        selected_hotel_name = selected_hotel_name
    )




@app.route('/occupancy', methods=['GET', 'POST'])
def occupancy():
    current_date = datetime.now().strftime("%B %d, %Y")
    cursor = mydb.cursor()

    # Fetch all hotels for the dropdown menu
    query = "SELECT hotelName, hotelId FROM hotel;"
    cursor.execute(query)
    hotels = cursor.fetchall()

    hotel_info = None  # Default state for no selected hotel
    selected_hotel = None  # Track the selected hotel

    if request.method == 'POST':  # Handle form submission
        selected_hotel = int(request.form.get('hotel')) # Get the selected hotel ID

        if selected_hotel:  # Fetch occupancy rate for the selected hotel
            query = """SELECT hotel.hotelName, 
                              (SUM(DATEDIFF(LEAST(reservation.endDate, '2024-12-31'), 
                              GREATEST(reservation.startDate, '2024-01-01')) + 1) 
                              / (COUNT(DISTINCT room.roomId) * 366.0)) * 100 AS occupancyRate
                       FROM reservation
                       JOIN room_reservation_assignment
                       ON reservation.reservationId = room_reservation_assignment.reservationId
                       JOIN room
                       ON room_reservation_assignment.roomId = room.roomId
                       JOIN hotel
                       ON reservation.hotelId = hotel.hotelId
                       WHERE reservation.startDate <= '2024-12-31' 
                         AND reservation.endDate >= '2024-01-01'
                         AND hotel.hotelId = %s
                       GROUP BY hotel.hotelName
                       LIMIT 1;
            """
            cursor.execute(query, (selected_hotel,))
            hotel_info = cursor.fetchone()  # Fetch the occupancy rate

    # Pass all necessary data to the template
    return render_template(
        'occupancy.html',
        current_date=current_date,
        hotels=hotels,
        hotel_info=hotel_info,
        selected_hotel=selected_hotel
    )



@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e)

if __name__ == '__main__':
    app.run(debug=True)
