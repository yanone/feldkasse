import os, plistlib, glob
from ynlib.system import GetChr 
import argparse

parser = argparse.ArgumentParser(description='Feldkasse simple POS system')
parser.add_argument('productsFile', metavar='PLIST', type=str, help='products .plist file')
parser.add_argument('storageFolder', metavar='FOLDER', type=str, help='destination folder for checkout receipts')
args = vars(parser.parse_args())

if not os.path.exists(args['productsFile']):
	raise Exception("Products .plist doesn't exist.")

if not os.path.exists(args['storageFolder']):
	raise Exception("Storage folder doesn't exist.")








class Checkout(object):
	def __init__(self):
		self.cart = {}
		self.actions = {
			'+': self.add,
			'-': self.remove,
		}
		self.action = '+'
	
	def add(self, key):
		if self.cart.has_key(key):
			self.cart[key] += 1
		else:
			self.cart[key] = 1

	def remove(self, key):
		if self.cart.has_key(key):
			self.cart[key] -= 1
			if self.cart[key] == 0:
				del self.cart[key]
		
		if not self.cart:
			self.action = '+'
	
	def screenPrint(self):
		price = 0
		for key in self.cart.keys():
			if self.cart[key]:
				print '%sx %s' % (str(self.cart[key]).rjust(2), products[key].name)
				price += int(self.cart[key]) * products[key].price[currency]
		print self.action
		print '============='
		print price, currency
	
	def checkOut(self):
		if self.cart:
			cart = {}
			cart['products'] = {}
			price = 0

			for key in self.cart.keys():
				if self.cart[key]:
					cart['products'][products[key].name] = self.cart[key]
					price += int(self.cart[key]) * products[key].price[currency]
			cart['price'] = price
			cart['currency'] = currency
		
			filename = str(len(glob.glob(os.path.join(args['storageFolder'], '*.plist'))) + 1) + '.plist'
		
			plistlib.writePlist(cart, os.path.join(args['storageFolder'], filename))
		
		

class Product(object):
	def __init__(self, name, price):
		self.name = name
		self.price = price
	def __repr__(self):
		return '<Product %s, %s>' % (self.name, self.price)



currencies = {
	'/': 'EUR',
	'*': 'HUF',
	}
currency = 'EUR'


products = {}
productsPlist = plistlib.readPlist(args['productsFile'])

for key in productsPlist.keys():
	products[key] = Product(productsPlist[key]['name'], productsPlist[key]['price'])

# Start

os.system('clear')
checkout = Checkout()
checkout.screenPrint()

# Loop


while True:
	keypress = GetChr()
	os.system('clear')

	# Change action
	if checkout.actions.has_key(keypress):
		checkout.action = keypress

	# Change currency
	if currencies.has_key(keypress):
		currency = currencies[keypress]

	# Add/remove product
	if products.has_key(keypress):
		checkout.actions[checkout.action](keypress)
	
	if keypress == '\n':
		checkout.checkOut()
		checkout = Checkout()

	checkout.screenPrint()