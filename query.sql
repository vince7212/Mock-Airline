SELECT flight_id, scheduled_departure, scheduled_arrival, departure_airport, d.city, arrival_airport, a.city, seats_available, seats_booked
FROM flights
JOIN airport as d ON flights.departure_airport = d.airport_code
JOIN airport as a ON flights.arrival_airport = a.airport_code
WHERE lower(d.city) LIKE '%%' AND lower(a.city) LIKE '%%'
ORDER BY flight_id;

SELECT flight_id, scheduled_departure, scheduled_arrival, departure_airport, d.city, arrival_airport, a.city, seats_available, seats_booked
FROM flights
JOIN airport as d ON flights.departure_airport = d.airport_code
JOIN airport as a ON flights.arrival_airport = a.airport_code
WHERE lower(d.city) LIKE '%%' AND lower(a.city) LIKE '%%'
ORDER BY flight_id;

