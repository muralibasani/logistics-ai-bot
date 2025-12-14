---------------------------------------------------------
-- 1. CUSTOMERS (25)
---------------------------------------------------------
INSERT INTO LG_Customers (customer_id, name, email) VALUES
(1, 'Oliver Müller', 'oliver.mueller@example.com'),
(2, 'Emma Schmidt', 'emma.schmidt@example.com'),
(3, 'Liam Johansson', 'liam.johansson@example.com'),
(4, 'Sophia Dubois', 'sophia.dubois@example.com'),
(5, 'Lucas Rossi', 'lucas.rossi@example.com'),
(6, 'Mia Fischer', 'mia.fischer@example.com'),
(7, 'Noah Weber', 'noah.weber@example.com'),
(8, 'Amelia Martin', 'amelia.martin@example.com'),
(9, 'Ethan Bauer', 'ethan.bauer@example.com'),
(10, 'Ava Wagner', 'ava.wagner@example.com'),
(11, 'Leo Schneider', 'leo.schneider@example.com'),
(12, 'Chloe Bernard', 'chloe.bernard@example.com'),
(13, 'Ben Marino', 'ben.marino@example.com'),
(14, 'Ella Vogel', 'ella.vogel@example.com'),
(15, 'Oscar Hansen', 'oscar.hansen@example.com'),
(16, 'Sofia Eriksen', 'sofia.eriksen@example.com'),
(17, 'Theo Moretti', 'theo.moretti@example.com'),
(18, 'Hanna Keller', 'hanna.keller@example.com'),
(19, 'Mateo Ferrari', 'mateo.ferrari@example.com'),
(20, 'Julia Steiner', 'julia.steiner@example.com'),
(21, 'Aron Lindholm', 'aron.lindholm@example.com'),
(22, 'Nina Petrova', 'nina.petrova@example.com'),
(23, 'Victor Novak', 'victor.novak@example.com'),
(24, 'Elena Costa', 'elena.costa@example.com'),
(25, 'Jonas Berg', 'jonas.berg@example.com');

---------------------------------------------------------
-- 2. CUSTOMER ACCOUNT INFO (25)
---------------------------------------------------------
INSERT INTO LG_Customer_Account_Info 
(account_id, customer_id, phone_number, address_line1, address_line2, city, state, pincode, country, address_type, is_default)
VALUES
(1, 1, '+49 170 1111111', 'Hauptstrasse 12', '', 'Berlin', 'Berlin', '10115', 'Germany', 'shipping', true),
(2, 2, '+49 170 1111112', 'Bayernstrasse 5', '', 'Munich', 'Bavaria', '80331', 'Germany', 'shipping', true),
(3, 3, '+46 70 1111113', 'Sveavägen 45', '', 'Stockholm', '', '11157', 'Sweden', 'shipping', true),
(4, 4, '+33 6 11 11 11 14', 'Rue de Lyon 22', '', 'Paris', 'Île-de-France', '75012', 'France', 'shipping', true),
(5, 5, '+39 331 1111115', 'Via Roma 18', '', 'Milan', 'Lombardy', '20100', 'Italy', 'shipping', true),
(6, 6, '+49 170 1111116', 'Berliner Allee 8', '', 'Düsseldorf', 'NRW', '40210', 'Germany', 'shipping', true),
(7, 7, '+49 170 1111117', 'Marktstrasse 19', '', 'Hamburg', 'Hamburg', '20095', 'Germany', 'shipping', true),
(8, 8, '+33 6 11 11 11 18', 'Rue Victor Hugo 4', '', 'Lyon', 'Auvergne-Rhône-Alpes', '69002', 'France', 'shipping', true),
(9, 9, '+41 79 111 11 19', 'Bahnhofstrasse 50', '', 'Zurich', '', '8001', 'Switzerland', 'shipping', true),
(10, 10, '+34 611 111 120', 'Calle Mayor 10', '', 'Madrid', '', '28013', 'Spain', 'shipping', true),
(11, 11, '+43 660 1111111', 'Ringstrasse 7', '', 'Vienna', '', '1010', 'Austria', 'shipping', true),
(12, 12, '+33 6 11 11 11 22', 'Boulevard Saint-Germain', '', 'Paris', 'Île-de-France', '75006', 'France', 'shipping', true),
(13, 13, '+39 331 1111123', 'Via Garibaldi 3', '', 'Turin', 'Piedmont', '10100', 'Italy', 'shipping', true),
(14, 14, '+49 170 1111124', 'Köpenicker Strasse 9', '', 'Berlin', 'Berlin', '10997', 'Germany', 'shipping', true),
(15, 15, '+47 901 11 125', 'Karl Johans gate 20', '', 'Oslo', '', '0159', 'Norway', 'shipping', true),
(16, 16, '+46 70 1111126', 'Drottninggatan 30', '', 'Gothenburg', '', '41114', 'Sweden', 'shipping', true),
(17, 17, '+39 331 1111127', 'Piazza Navona 12', '', 'Rome', 'Lazio', '00186', 'Italy', 'shipping', true),
(18, 18, '+41 79 111 11 128', 'Freiestrasse 16', '', 'Basel', '', '4051', 'Switzerland', 'shipping', true),
(19, 19, '+39 331 1111129', 'Via Dante 9', '', 'Florence', 'Tuscany', '50122', 'Italy', 'shipping', true),
(20, 20, '+43 660 1111130', 'Mariahilfer Strasse 44', '', 'Vienna', '', '1060', 'Austria', 'shipping', true),
(21, 21, '+46 70 1111131', 'Stora Gatan 5', '', 'Uppsala', '', '75310', 'Sweden', 'shipping', true),
(22, 22, '+34 611 111 132', 'Avinguda Diagonal 100', '', 'Barcelona', '', '08019', 'Spain', 'shipping', true),
(23, 23, '+420 601 111 133', 'Vaclavske Namesti 40', '', 'Prague', '', '11000', 'Czech Republic', 'shipping', true),
(24, 24, '+39 331 1111134', 'Via Toledo 60', '', 'Naples', '', '80134', 'Italy', 'shipping', true),
(25, 25, '+47 901 11 135', 'Bryggen 5', '', 'Bergen', '', '5003', 'Norway', 'shipping', true);

---------------------------------------------------------
-- 3. ORDERS (each customer gets 1–3 orders)
---------------------------------------------------------
INSERT INTO LG_Orders (order_id, customer_id, order_status, total_amount) VALUES
(1,1,'Delivered',120.50),(2,1,'Cancelled',89.99),
(3,2,'Delivered',45.00),(4,2,'Refunded',60.00),
(5,3,'Shipped',150.00),
(6,4,'Delivered',220.00),(7,4,'Delivered',89.00),
(8,5,'Cancelled',55.00),(9,5,'Delivered',130.00),
(10,6,'Delivered',99.99),
(11,7,'Refunded',75.50),(12,7,'Delivered',180.00),
(13,8,'Shipped',110.00),
(14,9,'Delivered',200.00),
(15,10,'Cancelled',49.99),(16,10,'Delivered',140.00),
(17,11,'Delivered',175.00),
(18,12,'Refunded',66.00),
(19,13,'Delivered',205.00),
(20,14,'Shipped',118.00),
(21,15,'Delivered',90.00),(22,15,'Delivered',100.50),
(23,16,'Cancelled',75.00),
(24,17,'Delivered',300.00),
(25,18,'Refunded',40.00),
(26,19,'Delivered',215.00),
(27,20,'Delivered',87.00),
(28,21,'Delivered',66.00),
(29,22,'Cancelled',59.00),(30,22,'Delivered',112.00),
(31,23,'Delivered',250.00),
(32,24,'Shipped',102.00),
(33,25,'Delivered',199.00);

---------------------------------------------------------
-- 4. ORDER TRACKING (1–3 per order)
---------------------------------------------------------
INSERT INTO LG_Order_Tracking (order_id, status, location) VALUES
(1,'Delivered','Berlin'),
(2,'Cancelled','Berlin'),
(3,'Out for Delivery','Munich'),(3,'Delivered','Munich'),
(4,'Refunded','Munich'),
(5,'In Transit','Stockholm'),
(6,'Delivered','Paris'),(7,'Delivered','Paris'),
(8,'Cancelled','Milan'),(9,'Delivered','Milan'),
(10,'Delivered','Düsseldorf'),
(11,'Refunded','Hamburg'),
(12,'Delivered','Hamburg'),
(13,'Shipped','Lyon'),
(14,'Delivered','Zurich'),
(15,'Cancelled','Madrid'),(16,'Delivered','Madrid'),
(17,'Delivered','Vienna'),
(18,'Refunded','Paris'),
(19,'Delivered','Turin'),
(20,'Shipped','Berlin'),
(21,'Delivered','Oslo'),(22,'Delivered','Oslo'),
(23,'Cancelled','Gothenburg'),
(24,'Delivered','Rome'),
(25,'Refunded','Basel'),
(26,'Delivered','Florence'),
(27,'Delivered','Vienna'),
(28,'Delivered','Uppsala'),
(29,'Cancelled','Barcelona'),(30,'Delivered','Barcelona'),
(31,'Delivered','Prague'),
(32,'Shipped','Naples'),
(33,'Delivered','Bergen');

---------------------------------------------------------
-- 5. REFUNDS
---------------------------------------------------------
INSERT INTO LG_Refunds (order_id, refund_amount, refund_status) VALUES
(4,60.00,'Completed'),
(11,75.50,'Completed'),
(18,66.00,'Completed'),
(25,40.00,'Completed');

---------------------------------------------------------
-- 6. ORDER CANCELLATION
---------------------------------------------------------
INSERT INTO LG_Order_Cancellation (order_id, reason, cancelled_by) VALUES
(2,'Customer changed mind','customer'),
(8,'Out of stock','system'),
(15,'Customer request','customer'),
(23,'Card payment failed','system'),
(29,'Customer changed mind','customer');

---------------------------------------------------------
-- 7. DELIVERED ORDERS (only orders marked Delivered)
---------------------------------------------------------
INSERT INTO LG_Delivered_Orders (order_id, delivered_date, delivery_person, comments) VALUES
(1,'2025-01-10','Markus','Left at door'),
(3,'2025-01-11','Anna','Signed by customer'),
(6,'2025-01-12','Pierre','Delivered safely'),
(7,'2025-01-13','Pierre',''),
(9,'2025-01-14','Giovanni',''),
(10,'2025-01-15','Stefan',''),
(12,'2025-01-16','Hans',''),
(14,'2025-01-17','Lukas',''),
(16,'2025-01-18','Carlos',''),
(17,'2025-01-19','Martin',''),
(19,'2025-01-20','Paolo',''),
(21,'2025-01-21','Ola',''),
(22,'2025-01-22','Ola',''),
(24,'2025-01-23','Marco',''),
(26,'2025-01-24','Alessandro',''),
(27,'2025-01-25','Johann',''),
(28,'2025-01-26','Erik',''),
(30,'2025-01-27','Miguel',''),
(31,'2025-01-28','Karel',''),
(33,'2025-01-29','Henrik','');
