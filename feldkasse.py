#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os, plistlib, glob, time
from ynlib.system import GetChr 
from ynlib.strings import *
import argparse
from ynlib.files import *



parser = argparse.ArgumentParser(description='Feldkasse simple POS system')
parser.add_argument('productsFile', metavar='PLIST', type=str, help='products .plist file')
parser.add_argument('storageFolder', metavar='FOLDER', type=str, help='destination folder for checkout receipts')
parser.add_argument('printerIP', metavar='PRINTERIP', type=str, help='IP address of POS with receipt printer. "localhost" for self.')
args = vars(parser.parse_args())

if not os.path.exists(args['productsFile']):
	raise Exception("Products .plist doesn't exist.")

if not os.path.exists(args['storageFolder']):
	raise Exception("Storage folder doesn't exist.")


umrechnungskurs = 310.8
mwst = .07






################################### Printing ##########################

printerServerThread = None
if args['printerIP'] == 'localhost':

	# connect to USB thermal printer
	from escpos import *
	Epson = printer.Usb(0x04b8,0x0e02)

	# TCP server
	import SocketServer

	class MyTCPHandler(SocketServer.BaseRequestHandler):
		"""
		The RequestHandler class for our server.

		It is instantiated once per connection to the server, and must
		override the handle() method to implement communication to the
		client.
		"""

		def handle(self):
			# self.request is the TCP socket connected to the client
			self.data = self.request.recv(1024).strip()
			Epson.text(self.data)
			Epson.cut()
		
			# just send back the same data, but upper-cased
			self.request.sendall(self.data.upper())



	HOST, PORT = "", 9999

	# Create the server, binding to localhost on port 9999
	server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

	# Run server in separate thread
	import threading
	class PrinterServer(threading.Thread): 
		def __init__(self): 
			threading.Thread.__init__(self) 
 
		def run(self):
		
			server.serve_forever()
			

		def stop(self):
			self._Thread__stop()
	printerServerThread = PrinterServer()
	printerServerThread.start()



def networkPrint(data):
	
	import socket
	import sys

	# Create a socket (SOCK_STREAM means a TCP socket)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		# Connect to server and send data
		sock.connect((args['printerIP'], 9999))
		sock.sendall(data + "\n")

		# Receive data from the server and shut down
		received = sock.recv(1024)
	finally:
		sock.close()	


def storagePlistFiles():
	return glob.glob(os.path.join(args['storageFolder'], '*.plist'))


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
		else:
			self.cart[key] = -1
			#if self.cart[key] == 0:
			#	del self.cart[key]
		
		#if not self.cart:
		#	self.action = '+'
	
	def screenPrint(self):
		price = 0
		for key in productsPlist['productsOrder'].split(","):
			if self.cart.has_key(key) and self.cart[key] > 0:
				print '%sx %s' % (str(self.cart[key]).rjust(2), products[key].name)
				price += int(self.cart[key]) * products[key].price[currency]
		print self.action
		print '============='
		print formatPrice(price), currency
	
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
			cart['time'] = time.time()
		
			# Journal
			lastFileName = os.path.join(args['storageFolder'], str(len(storagePlistFiles())) + '.plist')
			
			for c in currencies.keys():
				journal_currency = currencies[c]
				cart['journal_' + journal_currency] = 0
		
				if os.path.exists(lastFileName):
					lastFile = plistlib.readPlist(lastFileName)
					# take over old currency
					if lastFile.has_key('journal_' + journal_currency):
						cart['journal_' + journal_currency] = lastFile['journal_' + journal_currency]
			# add current amount
			cart['journal_' + currency] += price


			filename = str(len(storagePlistFiles()) + 1) + '.plist'
		
			plistlib.writePlist(cart, os.path.join(args['storageFolder'], filename))
			
			return True
			
			

			

	def printToPrinter(self):
		# Filename for temp file
		filename = os.path.join(os.path.dirname(__file__), 'print.txt')
		
	
		price = 0
		string = []
		string.append('JUICIE CAFE @ O.Z.O.R.A')
		for key in productsPlist['productsOrder'].split(","):
			if self.cart.has_key(key) and self.cart[key] > 0:
				productPrintString = '%sx %s à %s %s' % (str(self.cart[key]).rjust(2), products[key].name, formatPrice(products[key].price[currency]), currency)
				price += int(self.cart[key]) * products[key].price[currency]
				string.append(productPrintString)
		string.append('' + str(formatPrice(price)) + ' ' + currency + '')
		if currency == 'HUF':
			mwst_summe = price / umrechnungskurs * mwst
		else:
			mwst_summe = price * mwst
		string.append('Incl. 7%% German VAT (%s EUR)' % (formatPrice(mwst_summe)))

		networkPrint('\n'.join(map(str, string)))

		

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

for key in productsPlist['products'].keys():
	products[key] = Product(productsPlist['products'][key]['name'], productsPlist['products'][key]['price'])

# Start


os.system('clear')
checkout = Checkout()


# Loop

keyPressHistory = ''

try:
	while True:
		os.system('clear')
		print (time.strftime("%A, ") + str(int(time.strftime("%I"))) + time.strftime(":%M") + time.strftime("%p").lower()).rjust(int(os.popen('stty size', 'r').read().split()[1]))
		print
		
				
		checkout.screenPrint()


		keypress = GetChr(60) # wait max. 60 seconds
		keyPressHistory += str(keypress)
	
		# Change action
		if checkout.actions.has_key(keypress):
			checkout.action = keypress

		# Change currency
		if currencies.has_key(keypress):
			currency = currencies[keypress]

		# Add/remove product
		if products.has_key(keypress):
			checkout.actions[checkout.action](keypress)
	
		# Delete cart
		if keypress == '0':
			checkout = Checkout()

		# Check out
		if keypress == '\n':
			if checkout.checkOut():
				checkout.printToPrinter()
				checkout = Checkout()
				currency = 'EUR'

		if keypress == '.':
			if printerServerThread:
				printerServerThread.stop()
			exit()

		

		checkout.screenPrint()
		

except:
	print "Error in loop"
	if printerServerThread:
		printerServerThread.stop()