import psycopg2
from config import host, user, password, db_name
from collections import Counter

empty_table_flag = True


class DataBase:
    statuses_name = ['new', 'assembled', 'shipped', 'delivered']

    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def add_user(self, email, name, phone, password):
        try:
            self.__cur.execute(f"SELECT COUNT(*) as count FROM users WHERE email_address LIKE '{email}'")
            res = self.__cur.fetchone()
            if res[0] > 0:
                print("Пользователь с таким email уже существует")
                return False
            self.__cur.execute("INSERT INTO users ( username, role, phone_number, email_address, password) VALUES(%s,%s,%s,%s,%s)", (name, 'staff', phone, email, password))
            self.__db.commit()
        except:
            print("Ошибка добавления пользователя в БД")
            return False
        return True

    def add_admin(self, email, name, phone, password):
        try:
            self.__cur.execute(f"SELECT COUNT(*) as count FROM users WHERE email_address LIKE '{email}'")
            res = self.__cur.fetchone()
            if res[0] > 0:
                print("Пользователь с таким email уже существует")
                return False
            self.__cur.execute("INSERT INTO users ( username, role, phone_number, email_address, password) VALUES(%s,%s,%s,%s,%s)", (name, 'admin', phone, email, password))
            self.__db.commit()
        except:
            print("Ошибка добавления пользователя в БД")
            return False
        return True

    def get_user(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE user_id = '{user_id}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            return res
        except:
            print("Ошибка получения данных о пользователе")
        return False

    def get_user_by_email(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email_address = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False
            return res
        except:
            print("Ошибка получения данных о пользователе (email)")

        return False

    def update_user_info(self, id, name, email, phone):
        try:
            self.__cur.execute(f"UPDATE users SET username='{name}', phone_number='{phone}', email_address='{email}' WHERE user_id='{id}';")
            self.__db.commit()
            return True
        except Exception as e:
            print("Ошибка обновления информации, ", e)
            return False

    def add_item(self, name, vendor_code, brand, description, material,
                 first_price, selling_price, discount_price, country,
                 category, type, tnvd, weight, packtype, packsize, gender, season):
        # print((name, vendor_code, description, material, first_price, selling_price, discount_price,
        #        country, category, type, tnvd, weight, packtype, packsize, gender, season))
        self.__cur.execute(f"""INSERT INTO goods(name, vendor_code, brand, description, material, first_price,
             selling_price, discount_price, country, category, type, tnvd, weight, packtype,
             packsize, gender, season) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
             (name, vendor_code, brand, description, material, first_price, selling_price, discount_price,
              country, category, type, tnvd, weight, packtype, packsize, gender, season))
        self.__db.commit()
        # for i in image:
        #     self.__cur.execute(f"INSERT INTO photos (vendor_code, photo) VALUES (%s, %s);", (vendor_code, str(i)))
        #     self.__db.commit()

    def get_items_preview(self):
        # self.__cur.execute(f"SELECT DISTINCT ON (goods.vendor_code) photo ,name, goods.vendor_code, first_price FROM goods JOIN photos ON goods.vendor_code=photos.vendor_code ;")
        try:
            self.__cur.execute(f"SELECT  name, vendor_code, discount_price FROM goods order by vendor_code;")
            inf = self.__cur.fetchall()
            res = []
            for row in inf:
                self.__cur.execute(f"SELECT SUM(amount) FROM modifications WHERE vendor_code='{row[1]}';")
                am = self.__cur.fetchone()
                photo = self.get_one_photo(row[1])
                res.append(row + am + photo)
            return res
        except:
            return {}

    def add_item_modif(self, vendor_code, sizes, colors, amount, barcode):
        one = True
        m = 0
        for num, zn in enumerate(sizes):
            if len(str(barcode[num]))>0:
                self.__cur.execute(f"DELETE FROM modifications WHERE vendor_code='{vendor_code}';")
                self.__cur.execute(f"INSERT INTO modifications(vendor_code, barcode, size, color, amount) VALUES (%s,%s,%s,%s,%s);",
                                   (vendor_code, str(barcode[num]), zn, colors[num], amount[num]))
                self.__db.commit()
            else:
                if one:
                    self.__cur.execute(f"SELECT MAX(barcode) FROM modifications;")
                    m = self.__cur.fetchone()
                    # m = m[0]
                    print(m)
                    if m[0] is None:
                        m = 2000000000
                    else:
                        m = m[0]
                    one = False
                m = int(m) + 1
                self.__cur.execute(f"INSERT INTO modifications(vendor_code, barcode, size, color, amount) VALUES (%s,%s,%s,%s,%s);",
                                   (vendor_code, str(m), zn, colors[num], amount[num]))
                self.__db.commit()

        # if len(barcode)>0:
        #     self.__cur.execute(f"DELETE FROM modifications WHERE vendor_code='{vendor_code}';")
        #     for num, zn in enumerate(sizes):
        #         self.__cur.execute(f"INSERT INTO modifications(vendor_code, barcode, size, color, amount) VALUES (%s,%s,%s,%s,%s);",
        #                            (vendor_code, str(barcode[num]), zn, colors[num], amount[num]))
        #         self.__db.commit()
        # else:
        #     self.__cur.execute(f"SELECT MAX(barcode) FROM modifications;")
        #     m = self.__cur.fetchone()
        #     m = int(m[0])
        #     if m is None:
        #         m = '2000000000'
        #     for num, zn in enumerate(sizes):
        #         m = m + 1
        #         self.__cur.execute(f"INSERT INTO modifications(vendor_code, barcode, size, color, amount) VALUES (%s,%s,%s,%s,%s);",
        #                            (vendor_code, str(m), zn, colors[num], amount[num]))
        #         self.__db.commit()

    def add_order(self, barcodes, amount, selling_price, customer):
        self.__cur.execute(f"SELECT cust_id FROM customers WHERE cust_name = '{customer[0]}';")
        cust_id = self.__cur.fetchone()
        #todo запрос сохранения номера нового покупателя
        if cust_id is None:
            self.add_customers(customer[0], "")
            self.__cur.execute(f"SELECT cust_id FROM customers WHERE cust_name = '{customer[0]}';")
            cust_id = self.__cur.fetchone()

        # print(barcodes)
        # colv = Counter(barcodes)
        try:
            self.__cur.execute(f" INSERT INTO orders(status, customer, datetime) VALUES (%s,%s,%s);", ('new', cust_id, 'now' ))
            self.__db.commit()
            self.__cur.execute(f"SELECT MAX(order_number) FROM orders;")
            ord_numb = self.__cur.fetchone()[0]
            for kl,zn in enumerate(barcodes):
            # for bar in colv:
                # int(colv[bar])
                self.__cur.execute(f" INSERT INTO single_order(order_number, barcode, amount, selling_price) VALUES (%s,%s,%s,%s);", (int(ord_numb), str(zn), int(amount[kl]), str(selling_price[kl])))
                # self.__cur.execute(f"UPDATE modifications SET amount = amount - 1 WHERE barcode='{str(bar)}';")
                self.__db.commit()
            return True
        except Exception as e:
            print("Ошибка записи заказов в бд ", e)
            return False

    def get_bc_list(self):
        try:
            self.__cur.execute(f"SELECT barcode FROM modifications;")
            res = self.__cur.fetchall()
            return res
        except:
            return {}

    def get_order_list(self):
        try:
            self.__cur.execute(f"SELECT order_number, datetime, cust_name, status  FROM orders JOIN customers ON orders.customer=customers.cust_id ORDER BY order_number desc;")
            # self.__cur.execute(f"SELECT order_number, datetime, cust_name, modifications.vendor_code FROM orders JOIN customers ON orders.customer=customers.cust_id JOIN modifications ON orders.barcode = modifications.barcode ORDER BY order_number desc ;")
            res = self.__cur.fetchall()
            return res
        except:
            return {}

    def get_order_by_number(self, order_number):
        self.__cur.execute(f"select barcode, amount, selling_price, cust_name, status  from  (SELECT barcode, amount, selling_price, orders.order_number, orders.status, customers.cust_name FROM single_order JOIN orders ON orders.order_number=single_order.order_number JOIN customers ON customers.cust_id=orders.customer) as a WHERE order_number='{order_number}';")
        res = self.__cur.fetchall()
        return res

    def update_orders_statuses(self, new_statuses):
        try:
            self.__cur.execute(f"SELECT MAX(order_number) FROM orders;")
            res = self.__cur.fetchone()[0]
            s = 0
            for i in range(res, res-len(new_statuses), -1):
                a = self.statuses_name[int(new_statuses[s])]
                self.__cur.execute(f"UPDATE orders SET status='{self.statuses_name[int(new_statuses[s])]}' WHERE order_number={i};")
                self.__db.commit()
                s = s + 1
            return True
        except Exception as e:
            print(e)
            return False

    def make_ship(self, order_numb, status, barcodes, amounts, prices, customer, performer):
        if performer == "order":
            self.__cur.execute(f"SELECT cust_id FROM customers WHERE cust_name='{customer}'")
            cust_id = self.__cur.fetchone()
            print(cust_id)
            # создаем отгрузку
            for i in barcodes:
                self.__cur.execute(f"INSERT INTO shipments(barcode, numb_performer, performer) VALUES (%s,%s,%s);", (i, cust_id, performer))
                self.__db.commit()
            # уменьшить остатки
            for num, znach in enumerate(barcodes):
                self.__cur.execute(f"UPDATE modifications SET amount=amount-{int(amounts[num])} WHERE barcode='{znach}';")
                self.__db.commit()
            # изменить заказ
            for num, znach in enumerate(barcodes):
                self.__cur.execute(f"UPDATE single_order SET amount={int(amounts[num])}, selling_price='{prices[num]}' WHERE barcode='{znach}' AND order_number={order_numb};")
                self.__db.commit()
            self.__cur.execute(f"UPDATE orders SET status='{status}' WHERE order_number={order_numb};")
            self.__db.commit()
        elif performer=="reload":
            for num, znach in enumerate(barcodes):
                self.__cur.execute(f"UPDATE single_order SET amount={int(amounts[num])}, selling_price='{prices[num]}' WHERE barcode='{znach}' AND order_number={order_numb};")
                self.__db.commit()
            self.__cur.execute(f"UPDATE orders SET status='{status}' WHERE order_number={order_numb};")
            self.__db.commit()


        # print(order_numb, status, barcodes, amounts, prices, customer, sep="\n", end="\n\n\n")
#         1
# assembled
# ['2000000001']
# ['1']
# ['15990']
# Константин Московский
    def get_one_photo(self, artic):
        self.__cur.execute(f"SELECT photo FROM photos WHERE vendor_code='{artic}' order by photo ;")
        res = self.__cur.fetchone()
        if res is None:
            return ("b0b0b0.jpg",)
        #     https://via.placeholder.com/150/FFFFFF/b0b0b0%20?text=image
        return res

    def delete_photo(self, photo):
        self.__cur.execute(f" DELETE FROM photos WHERE photo='{photo}';")
        self.__db.commit()

    def get_colors_by_art(self, artic):
        self.__cur.execute(f"select distinct colors.color, photos.photo from (select color from modifications where vendor_code='{artic}') as colors left join photos on colors.color=photos.color;")
        res = self.__cur.fetchall()
        return res

    def update_photos_for_art_and_color(self, artic, color, photos):
        try:
            for photo in photos:
                self.__cur.execute(f"""INSERT INTO photos (vendor_code, color, photo) SELECT '{artic}', '{color}', '{photo}' WHERE NOT EXISTS ( SELECT (vendor_code, color, photo) FROM photos WHERE vendor_code = '{artic}' AND color='{color}' AND photo='{photo}');""")
            self.__db.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def has_admin(self):
        self.__cur.execute(f"SELECT COUNT(*) FROM users where role='admin';")
        res = self.__cur.fetchone()
        if res[0] >=1:
            return True
        else:
            return False

    def get_item(self, artic):
        self.__cur.execute(f"""SELECT name, vendor_code, brand, description, material, first_price,
        selling_price, discount_price, country, category, type, tnvd, weight, packtype,
        packsize, gender, season FROM goods WHERE vendor_code='{artic}'""")
        res = self.__cur.fetchall()
        self.__cur.execute(f""" SELECT photo FROM photos WHERE vendor_code='{artic}'""")
        photos = self.__cur.fetchall()
        res.append([i[0] for i in photos])
        print(res)
        return res

    def get_modif(self, artic):
        self.__cur.execute(f"SELECT barcode, size, color, amount FROM modifications WHERE vendor_code='{artic}'")
        res = self.__cur.fetchall()
        return res

    def update_item(self,name, new_vendor_code, vendor_code, brand,  description, material, first_price,
                    selling_price, discount_price, country, category, type, tnvd, weight, packtype,
                    packsize, gender, season):
        try:
            print(brand)
            self.__cur.execute(f"""UPDATE goods SET name='{name}',vendor_code='{new_vendor_code}',brand='{brand}', description='{description}',material='{material}',
                first_price='{first_price}',selling_price='{selling_price}',discount_price='{discount_price}',country='{country}',category='{category}', 
                type='{type}',tnvd='{tnvd}',weight='{weight}',packtype='{packtype}',packsize='{packsize}',gender='{gender}',season='{season}' WHERE vendor_code='{vendor_code}';""")
            self.__db.commit()
            return True
        except:
            return False

    def update_item_modif(self, vendor_code, size, color, amount, barcode):
        try:
            self.__cur.execute(f"SELECT barcode FROM modifications WHERE vendor_code='{vendor_code}';")
            r = self.__cur.fetchall()
            r = [i[0] for i in r]
            if len(r)>0:
                for i, bc in enumerate(color):
                    bcode = str(barcode[i]).strip()
                    if bcode in r and len(bcode)>1:
                        self.__cur.execute(f"UPDATE modifications SET size='{size[i]}', color='{color[i]}', amount='{amount[i]}' WHERE barcode='{bcode}';")
                    elif bcode not in r and len(bcode) > 0:
                        self.__cur.execute(f"UPDATE modifications SET barcode='{bcode}' WHERE size='{size[i]}' AND color='{color[i]}' AND amount='{amount[i]}';")
                    else:
                        # todo удаление дубликатов
                        self.__cur.execute(f"SELECT MAX(barcode) FROM modifications")
                        m = self.__cur.fetchone()
                        m = int(m[0]) + 1
                        self.__cur.execute(f"INSERT INTO modifications(vendor_code, barcode, size, color, amount) VALUES (%s,%s,%s,%s,%s);",
                                           (vendor_code,str(m), size[i], color[i], amount[i]))
                    self.__db.commit()
            else:
                self.add_item_modif(vendor_code, size, color, amount, barcode)

            return True
        except:
            return False

    def add_refund(self, barcodes, customer):
        self.__cur.execute(f"SELECT cust_id FROM customers WHERE cust_name = '{customer[0]}';")
        c_id = self.__cur.fetchone()[0]
        self.__cur.execute(f"INSERT INTO returns(cust_id, datetime) VALUES (%s,%s);", (c_id, 'now'))
        self.__db.commit()
        self.__cur.execute(f"SELECT MAX(return_number) FROM returns;")
        current_return_number = self.__cur.fetchone()[0]
        # for num, barcode in barcodes:
        #     self.__cur.execute(f"INSERT INTO single_return(return_number,barcode,amount) VALUES (%s,%s,%s);", (current_return_number, barcode, am))
        colv = Counter(barcodes)
        try:
            for bar in colv:
                self.__cur.execute(f" INSERT INTO single_return(return_number, barcode, amount) VALUES (%s,%s,%s);",
                                   (current_return_number, str(bar), int(colv[bar])))
                self.__db.commit()
                # пополнение остатков
                self.__cur.execute(f"UPDATE modifications SET amount = amount + {int(colv[bar])} WHERE barcode='{str(bar)}';")
                self.__db.commit()
            return True
        except:
            print("Ошибка записи возвратов в бд")
            return False

    def get_refunds_list(self):
        try:
            # self.__cur.execute(f"""SELECT return_number, datetime, cust_name, modifications.vendor_code FROM returns JOIN customers ON returns.cust_id=customers.cust_id JOIN modifications ON returns.barcode = modifications.barcode ORDER BY return_number desc ;""")
            # res = self.__cur.fetchall()
            self.__cur.execute("""select a.return_number, a.datetime, a.cust_name,am.total_amount, cost.total_cost from
             (select distinct return_number, datetime, c.cust_name from returns 
             join customers c on returns.cust_id = c.cust_id) as a 
             join (select sum(amount) as total, return_number from single_return group by return_number)
             as b on a.return_number=b.return_number 
             join (select a.return_number as ret_n, sum(total_cost) as total_cost from
             (select single_return.return_number, modifications.vendor_code, modifications.barcode,
             goods.selling_price::int*single_return.amount as total_cost  from modifications
             join single_return on modifications.barcode = single_return.barcode  
             join goods on modifications.vendor_code = goods.vendor_code)
             as a group by a.return_number) as cost on cost.ret_n =a.return_number 
             join (select sum(amount) as total_amount, return_number from single_return group by return_number)
             as am on am.return_number=a.return_number order by a.return_number desc ;""")
            res = self.__cur.fetchall()
            # returns number, date, customer, amount, cost
            return res
        except:
            return {}

    def get_one_refund(self, refund_number):
        self.__cur.execute(f"""select goods.name, modifications.vendor_code, modifications.color, modifications.size,
        single_return.amount, selling_price, first_price from modifications join single_return 
        on modifications.barcode = single_return.barcode join goods on modifications.vendor_code = goods.vendor_code
        where return_number={refund_number};""")
        res = self.__cur.fetchall()
    #     returns name, vendor_code, color, size, amount, selling_price, first_price
        return res


    def get_customers(self):
        try:
            self.__cur.execute(f"SELECT cust_name, contact FROM customers order by cust_name;")
            res = self.__cur.fetchall()
            return res
        except:
            return {}

    def add_customers(self,name,contact):
        try:
            self.__cur.execute(f"SELECT count(cust_name) FROM customers WHERE cust_name='{name}';")
            c = self.__cur.fetchone()[0]
            self.__cur.execute(f"SELECT count(contact) FROM customers WHERE contact='{contact}';")
            cont = self.__cur.fetchone()[0]
            if c == 0 and cont == 0:
                self.__cur.execute(f"INSERT INTO customers(cust_name, contact) VALUES (%s,%s);", (name, contact))
            elif c == 1:
                self.__cur.execute(f"UPDATE customers SET contact='{contact}' WHERE cust_name='{name}'")
            elif cont == 1:
                self.__cur.execute(f"UPDATE customers SET cust_name='{name}' WHERE contact='{contact}'")
            self.__db.commit()
            return True
        except:
            return False

    def make_inventory(self, barcodes, user):
        try:
            self.__cur.execute(f"SELECT SUM(amount) FROM modifications;")
            amount_before=self.__cur.fetchone()[0]
            self.__cur.execute(f"UPDATE modifications SET amount='0';")
            self.__db.commit()
            self.__cur.execute(f"SELECT MAX(inventory_number) FROM inventory;")
            num = self.__cur.fetchone()
            if num[0] is None:
                num = 1
            else:
                num = num[0] + 1
            self.__cur.execute(f"INSERT INTO inventory(amount,amount_before, datetime, user_id, inventory_number) VALUES (%s,%s,%s,%s,%s);",
                               ('0',amount_before, 'now', user, num))
            self.__db.commit()
            try:
                for i in barcodes:
                    # [i[0] for i in r]
                    self.__cur.execute(f"UPDATE modifications SET amount=amount + 1 WHERE barcode='{i}';")
                    self.__db.commit()
                    self.__cur.execute(f"INSERT INTO bars_invent(inventory_number, barcode) VALUES ('{num}', '{i}');")
                    self.__db.commit()
            except:
                print("Данный штрихкод остуствует в БД: ", i)
            self.__cur.execute(f"SELECT COUNT(barcode) FROM bars_invent WHERE inventory_number='{num}';")
            amount = self.__cur.fetchone()[0]
            self.__cur.execute(f"UPDATE inventory SET amount='{amount}' WHERE inventory_number='{num}';")
            self.__db.commit()
            return True
        except:
            return False

    def get_invent_preview(self):
        try:
            self.__cur.execute(f"SELECT inventory_number, datetime, username, amount, amount_before FROM inventory join users on inventory.user_id = users.user_id ORDER BY datetime DESC ;")
            res = self.__cur.fetchall()
            return res
        except:
            print("Ошибка получения списка инвентаризаций из БД")
            return []

# connection = None
#
# def run_sql(command):
#     global connection
#     try:
#         # подключение к существующей бд
#         connection = psycopg2.connect(
#             host=host,
#             user=user,
#             password=password,
#             database=db_name)
#
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT version()")
#             print(f"Server version: {cursor.fetchone()}")
#             cursor.close()
#
#     except Exception as _ex:
#         print("[INFO] Error while working with PostgreSQL", _ex)
#     finally:
#         # закрытие соединения
#         if connection:
#             connection.close()
#             print("[INFO] PostgreSQL connection closed")

