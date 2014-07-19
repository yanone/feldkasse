# -*- coding: utf-8 -*-


import os, plistlib, glob, time
from ynlib.system import GetChr 
from ynlib.strings import formatPrice
import argparse
from ynlib.files import *

import cups
from xhtml2pdf import pisa


parser = argparse.ArgumentParser(description='Feldkasse simple POS system')
parser.add_argument('productsFile', metavar='PLIST', type=str, help='products .plist file')
parser.add_argument('storageFolder', metavar='FOLDER', type=str, help='destination folder for checkout receipts')
args = vars(parser.parse_args())

if not os.path.exists(args['productsFile']):
	raise Exception("Products .plist doesn't exist.")

if not os.path.exists(args['storageFolder']):
	raise Exception("Storage folder doesn't exist.")


umrechnungskurs = 310.8
mwst = .07


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
		for key in self.cart.keys():
			if self.cart[key]:
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
		filename = os.path.join(os.path.dirname(__file__), 'print.pdf')
		
	
		price = 0
		xhtml = []
		xhtml.append('<p style="font-size: 10pt;">')
		xhtml.append('<b>JUICIE CAF&#x00C9; @ O.Z.O.R.A</b>')
		for key in self.cart.keys():
			if self.cart[key]:
				xhtml.append('%sx %s' % (str(self.cart[key]).rjust(2), products[key].name))
				price += int(self.cart[key]) * products[key].price[currency]
		xhtml.append('<b>' + str(formatPrice(price)) + ' ' + currency + '</b>')
		if currency == 'HUF':
			mwst_summe = price / umrechnungskurs * mwst
		else:
			mwst_summe = price * mwst
		xhtml.append('Incl. 7%% German VAT (%s EUR)' % (formatPrice(mwst_summe)))
		xhtml.append('<br />.')
		xhtml.append('</p>')

		xhtml = '<br />'.join(map(str, xhtml))

       
		pdf = pisa.CreatePDF(xhtml, file(filename, "w"))
		
		#WriteToFile(filename, xhtml)
		
		if not pdf.err:
		#if True:
			# Close PDF file - otherwise we can't read it
			pdf.dest.close()
   
			# print the file using cups
			conn = cups.Connection()
			# Get a list of all printers
			printers = conn.getPrinters()
			#for printer in printers: 
			#	# Print name of printers to stdout (screen)
			#	print printer, printers[printer]["device-uri"]
			# get first printer from printer list
			printer_name = printers.keys()[0]
			conn.printFile(printer_name, filename, "Python_Status_print", {})
		else:
			print "Unable to create pdf file"
		

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
	
	# Delete cart
	if keypress == '0':
		checkout = Checkout()

	# Check out
	if keypress == '\n':
		if checkout.checkOut():
			checkout.printToPrinter()
			checkout = Checkout()
			currency = 'EUR'


	checkout.screenPrint()