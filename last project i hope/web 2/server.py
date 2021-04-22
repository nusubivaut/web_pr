import shutil
import sqlite3
import uuid
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import make_response
import json
import io

import hashlib
from datetime import datetime
import json
import random
import string
import base64
import os


app = Flask(__name__)

data = json.load(io.open('data/data.json', 'r', encoding='utf-8-sig'))


def randomword(length):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(length))

def AYE():
	data = json.load(io.open('data/data.json', 'r', encoding='utf-8-sig'))
	for i in os.listdir("static/img/"):
		if i not in data:
			shutil.rmtree("static/img/" + i, ignore_errors=True)

class User():

	def serf():
		ip = str(request.remote_addr)
		session = request.cookies.get("Auth")
		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute(
				"SELECT * FROM users WHERE ip=:ip AND session=:session", {"ip": ip, "session": session})
			data = cursor.fetchall()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}
		if not data:
			return {
				"ok": False,
				"message": "Соединение потеряно!"
			}

		# if abs(int(data[0][6]) - int(datetime.now().timestamp())) > 10:
		# 	return {
		# 		"ok": False,
		# 		"message": "session expired!"
		# 	}

		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute("""UPDATE users 
				SET session_time=:session_time
				WHERE session=:session""",
						   {"session": session, "session_time": int(datetime.now().timestamp())})
			conn.commit()
			cursor.execute(
				"SELECT * FROM users WHERE ip=:ip AND session=:session", {"ip": ip, "session": session})
			data = cursor.fetchall()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}
		return data

	def isAuth():
		r = User.serf()
		return "ok" not in r

	def start_session(login, password, ip):
		if not User.check_user_password(login, password):
			return {
				"ok": False,
				"message": "неправильный пароль"
			}

		session = str(uuid.uuid4())
		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute("""UPDATE users 
				SET session=:session, session_time=:session_time, ip=:ip 
				WHERE login=:login""",
						   {"login": login, "session": session, "ip": ip, "session_time": int(datetime.now().timestamp())})
			conn.commit()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}

		return {
			"ok": True,
			"message": session,
		}

	def check_user_password(login, password):
		password = hashlib.md5(password.encode('utf-8')).hexdigest()
		conn = sqlite3.connect('users.db')
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM users WHERE login=:login AND password=:password",
					   {"login": login, "password": password})
		data = cursor.fetchall()
		conn.close()
		return bool(data)

	def get_user_by_login(login):
		conn = sqlite3.connect('users.db')
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM users WHERE login=:login",
					   {"login": login})
		data = cursor.fetchall()
		conn.close()
		return data

	def get_my_cart():
		data = User.serf()
		if not data:
			return {
				"ok": False,
				"message": "Соединение потеряно!"
			}
		if data[0][2]:
			data = data[0][2].split(",")
		else:
			data = []
		cart = {}
		d = json.load(io.open('data/data.json', 'r', encoding='utf-8-sig'))
		for i in data:
			t = i.split(":")
			if t[0] in d:
				cart[t[0]] = int(t[1])
		return cart

	def delete_from_cart(id):
		data = User.serf()[0]
		session = data[4]
		ip = data[5]
		cart = User.get_my_cart()
		if id not in cart:
			return {
				"ok": True,
				"message": "Элемент удалён"
			}
		cart.pop(id)
		cart = ",".join([f"{i}:{cart[i]}" for i in cart])
		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute("""UPDATE users 
				SET cart=:cart 
				WHERE session=:session AND ip=:ip""",
						   {"session": session, "ip": ip, "cart": cart})
			conn.commit()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}
		return {
			"ok": True,
			"message": "Элемент удалён"
		}

	def add_to_cart(id):
		data = User.serf()[0]
		session = data[4]
		ip = data[5]
		cart = User.get_my_cart()
		if cart.get(id):
			cart[id] += 1
		else:
			cart[id] = 1
		cart = ",".join([f"{i}:{cart[i]}" for i in cart])
		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute("""UPDATE users 
				SET cart=:cart 
				WHERE session=:session AND ip=:ip""",
						   {"session": session, "ip": ip, "cart": cart})
			conn.commit()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}
		return {
			"ok": True,
			"message": "Элемент добавлен!"
		}

	def get_my_products():

		data = User.serf()
		if not data:
			return {
				"ok": False,
				"message": "Соединение потеряно!"
			}
		if not data[0][3]:
			return []
		return [i for i in data[0][3].split(",") if i]


	def add_item(item_id):
		ip = str(request.remote_addr)
		session = request.cookies.get("Auth")
		products = User.get_my_products()
		if type(products) is dict and products.get("ok") == False:
			return {
				"ok": False,
				"message": products.get("message")
				# AYE
			}        
		if item_id in products:
			return {
				"ok": True,
				"message": "Item has been already added!"
			}
		products.append(item_id)
		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute("UPDATE users SET products=:products WHERE ip=:ip AND session=:session;", {
				"ip": ip, "session": session, "products": ",".join(products)})
			conn.commit()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}
		return {
			"ok": True,
			"message": "Item added!"
		}

	def register(login, password):
		if len(password) < 8:
			return {
				"ok": False,
				"message": "Длина пароля должна быть более 8 символов!"
			}

		if User.get_user_by_login(login):
			return {
				"ok": False,
				"message": "Такое имя уже существует!"
			}

		try:
			conn = sqlite3.connect('users.db')
			cursor = conn.cursor()
			cursor.execute("INSERT INTO users (login, password) VALUES (:login, :password);", {
				"login": login, "password": hashlib.md5(password.encode('utf-8')).hexdigest()})
			conn.commit()
			conn.close()
		except Exception as e:
			return {
				"ok": False,
				"message": str(e)
			}
		return {
			"ok": True,
			"message": "Success: Вы зарегистрировались!"
		}


class GetPage():

	def success(message="У вас получилось!<br>Поздравляю!", isAuth=None):
		if not isAuth:
			isAuth = User.isAuth()
		resp = make_response(render_template(
			'success.html', message=message, isAuth=isAuth))
		return resp

	def error(e="Что-то пошло не так.."):
		resp = make_response(render_template(
			'error.html', e=e, isAuth=User.isAuth()))
		return resp

	def index():
		with open("data/data.json", "rb") as d:
			data = json.load(d)
		resp = make_response(render_template(
			'index.html', data=data, isAuth=User.isAuth()))
		return resp

	def about():
		resp = make_response(render_template(
			'about.html', isAuth=User.isAuth()))
		return resp

	def ofProduct(id):
		isAuth = User.isAuth()
		isOwner = isAuth and id in User.get_my_products()
		with open("data/data.json", "rb") as d:
			data = json.load(d)
		if id in data:
			resp = make_response(render_template(
				'item.html', id=id, data=data, isAuth=User.isAuth(), isOwner=isOwner))
		else:
			resp = GetPage.error("Страница не существует!")
		return resp

	def confrim_edit(id):
		return GetPage.add_item(id)
		# name = str(request.form.get('name'))
		# descr = str(request.form.get('descr'))
		# cpu = str(request.form.get('cpu'))
		# ram = str(request.form.get('ram'))
		# screen = str(request.form.get('screen'))
		# battery = str(request.form.get('battery'))
		# price = str(request.form.get('price'))
		# imgs = [request.form.get('img0')]
		# imgs = [i for i in imgs if i != "DELETED"]
		# i = 1
		# while(request.form.get('img' + str(i))):
		# 	imgs.append(request.form.get('img' + str(i)))

	def edit_product(id):

		data = json.load(io.open('data/data.json', 'r', encoding='utf-8-sig'))
		if id not in data:
			return GetPage.error("Страница не существует!")
		name = data[id]["name"]
		descr = data[id]['descr']
		cpu = data[id]['characteristics']['cpu']
		ram = data[id]['characteristics']['ram']
		screen = data[id]['characteristics']['screen']
		battery = data[id]['characteristics']['battery']
		price = data[id]['prices']['rub']
		imgs = data[id]['photos']['all']
		return render_template("edit_item.html", imgs=imgs, name=name, descr=descr, cpu=cpu, ram=ram, screen=screen, battery=battery, price=price)

	def add_item(ident=""):
		name = str(request.form.get('name'))
		descr = str(request.form.get('descr'))
		cpu = str(request.form.get('cpu'))
		ram = str(request.form.get('ram'))
		screen = str(request.form.get('screen'))
		battery = str(request.form.get('battery'))
		price = str(request.form.get('price'))
		if not ident:
			ident = randomword(5)
		else:
			if os.path.exists("static/img/" + ident):
				shutil.rmtree("static/img/" + ident, ignore_errors=True)

		if battery.isdigit():
			battery += "mAh"
		imgs = [request.form.get('img0')]
		i = 1
		while(request.form.get('img' + str(i))):
			imgs.append(request.form.get('img' + str(i)))
			i += 1
		imgs = [i for i in imgs if i and i != "DELETED"]
		if not os.path.exists("static/img/" + ident):
			os.mkdir("static/img/" + ident)
		img_urls = []

		if imgs:
			for i in range(len(imgs)):
				with open("static/img/" + ident + "/img" + str(i) + ".jpg", "wb") as fh:
					fh.write(base64.b64decode("".join(imgs[i].split(",")[1:])))
				img_urls.append("/static/img/" + ident +
								"/img" + str(i) + ".jpg")
		else:
			img_urls.append(
				"https://www.emsmedyk.pl/cache/a2dcaa0661dd93c5b7faca9c90d572ab185098fc720x720_f.png")
		added = User.add_item(ident)
		if added["ok"]:
			with open("data/data.json", "rb") as d:
				data = json.load(d)
			data[ident] = {
				"name": name,
				"descr": descr,
				"characteristics": {
					"cpu": cpu,
					"ram": ram,
					"screen": screen,
					"battery": battery
				},
				"prices": {
					"rub": price
				},
				"photos": {
					"all": img_urls,
					"main": img_urls[0]
				}
			}
			with open("data/data.json", "w") as d:
				json.dump(data, d)

			return GetPage.success("Страница обновлена!")
		else:
			return GetPage.error(added["message"])

	def cart():
		data = json.load(io.open('data/data.json', 'r', encoding='utf-8-sig'))
		return render_template("cart.html", cart=User.get_my_cart(), data=data, isAuth=1)

	def register():

		login = request.form.get('login')
		password = request.form.get('password')
		reg = User.register(login, password)
		if reg["ok"]:
			session = User.start_session(
				login, password, str(request.remote_addr))
			if session["ok"]:
				resp = GetPage.success("Поздравляю, теперь ты официально алхимик!", isAuth=1)
				resp.set_cookie("Auth", session["message"])
				return resp
			return GetPage.error(session["message"])
		return GetPage.error(reg["message"])

	def auth():
		login = request.form.get('login')
		password = request.form.get('password')

		session = User.start_session(
			login, password, str(request.remote_addr))
		if session["ok"]:
			resp = GetPage.success("Ура! Личность установлена, проходи, мой друг!", isAuth=1)
			resp.set_cookie("Auth", session["message"])
			return resp
		return GetPage.error(session["message"])


@app.route('/')
def index():
	AYE()
	return GetPage.index()


@app.route('/as')
def aas():
	return str(User.get_my_cart())


@app.route('/about')
def about():
	return GetPage.about()


@app.route('/cart', methods=["GET", "POST"])
def cart():
	if User.isAuth():
		if request.method == "GET":
			return GetPage.cart()
		else:
			User.delete_from_cart(request.form.get('id'))
			resp = redirect("/cart")
			return resp
	else:
		return GetPage.error("Сначала авторизируйся!")


@app.route('/add_item', methods=['POST', 'GET'])
def add_item():
	if not User.isAuth():
		return GetPage.error("Сначала авторизируйся!")
	if request.method == "GET":
		return make_response(render_template("add_item.html", isAuth=User.isAuth()))
	else:
		return GetPage.add_item()


@app.route('/item/<id>/', methods=['POST', 'GET'])
def item(id):
	if request.method == "GET":
		return GetPage.ofProduct(id)

	else:
		if User.isAuth():
			User.add_to_cart(id)
			resp = redirect("/item/"+id)
			return resp
		else:
			return GetPage.error("Сначала авторизируйся!")


@app.route('/item/<id>/edit', methods=["GET", "POST"])
def edit_item(id):
	isOwner = User.isAuth() and id in User.get_my_products()
	if not isOwner:
		return GetPage.error("Нет доступа! Проклятый, выйди и зайди нормально!")

	if request.method == 'GET':
		return GetPage.edit_product(id)

	elif request.method == 'POST':
		resp = GetPage.confrim_edit(id)
		return resp

	return GetPage.edit_product(id)


def item(id):
	return GetPage.edit_product(id)


@app.errorhandler(404)
def page_not_found(error):
	return GetPage.error("Страница не существует!")


@app.route('/reg', methods=['POST', 'GET'])
def register():
	if User.isAuth():
		resp = redirect("/", code=302)
		return resp
	if request.method == 'GET':
		resp = make_response(render_template(
			"register.html", isAuth=User.isAuth()))
		return resp

	elif request.method == 'POST':
		isreg = bool(int(request.form.get('isreg')))
		if isreg:
			resp = GetPage.register()
		else:
			resp = GetPage.auth()
		return resp


@app.route('/c')
def cookie():
	resp = redirect("/", code=302)
	resp.set_cookie("Auth", "")
	return resp


if __name__ == '__main__':
	app.run(port=8080, host='127.0.0.1')
