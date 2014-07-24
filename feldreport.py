# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os, plistlib, glob, time
from ynlib.system import GetChr, Execute
from ynlib.strings import formatPrice
from ynlib.calendars import *
from ynlib.histogram import *
import argparse

parser = argparse.ArgumentParser(description='Feldkasse simple POS system')
parser.add_argument('storageFolder', metavar='FOLDER', type=str, help='source folder for checkout receipts')
parser.add_argument('IPs', metavar='IPS', type=str, help='comma-delimited list of IP-addresses of POS clients to collect data from')
args = vars(parser.parse_args())

if not os.path.exists(args['storageFolder']):
	raise Exception("Storage folder doesn't exist.")


	
umrechnungsKurs = 310
	

width_products = 20
width_days = 11

while True:	

	days = {}
	products = {}
	currencies = {}
	histogram = Histogram()
	letzteStunde = {}
	letzteStunde = 0


	histograms = {}


	IPs = {}

	for IP in args['IPs'].split(','):
		foldername = os.path.basename(args['storageFolder'])
		IPfolder = os.path.join(args['storageFolder'], IP)
		if not IPfolder.endswith('/'):
			IPfolder += '/'

		if os.system("ping -c 1 %s" % IP) == 0:
			IPs[IP] = 'online'
			a = Execute('ssh-copy-id -i /home/pos/.ssh/id_rsa.pub %s' % IP)
			a = Execute('mkdir -p %s' % IPfolder)
			p = 'rsync -avze ssh pos@%s:/home/pos/feldkasse/%s/ %s' % (IP, foldername, IPfolder)
			Execute(p)
		else:
			IPs[IP] = 'offline'


		for f in glob.glob(os.path.join(IPfolder, '*.plist')):
			plist = plistlib.readPlist(f)
			day = Day(time.localtime(plist['time'])[0], time.localtime(plist['time'])[1], time.localtime(plist['time'])[2], locale = 'de')
			dayname = day.weekday

			# init
			if not days.has_key(dayname):
				days[dayname] = {}
				days[dayname]['currencies'] = {}
				days[dayname]['products'] = {}

			# products
			for product in plist['products']:
				if '//' in product:
					productName, productCategory = product.split('//')
				else:
					productName = product
					productCategory = 'undefined'
				if not days[dayname]['products'].has_key(productName):
					days[dayname]['products'][productName] = 0
				days[dayname]['products'][productName] += plist['products'][product]
				#total
				if not products.has_key(product):
					products[product] = 0
				products[product] += plist['products'][product]
				
				if not histograms.has_key(productCategory):
					histograms[productCategory] = Histogram()
				histograms[productCategory].addValue(int(time.localtime(plist['time'])[3]), plist['products'][product])

			# price
			if not days[dayname]['currencies'].has_key(plist['currency']):
				days[dayname]['currencies'][plist['currency']] = 0
			days[dayname]['currencies'][plist['currency']] += plist['price']
			#total
			if not currencies.has_key(plist['currency']):
				currencies[plist['currency']] = 0
			currencies[plist['currency']] += plist['price']
			
			# letzte Stunde:
			if plist['time'] > time.time() - 3600:
				if plist['currency'] == 'HUF':
					letzteStunde += plist['price'] / float(umrechnungsKurs)
				else:
					letzteStunde += plist['price']
				
	os.system('clear')
	
	
	# sync files here


	# first line
	string = ' ' * width_products
	for day in days.keys():
		string += ('' + day.upper() + '').rjust(width_days)
	string += ('Summe').rjust(width_days)
	print string

	# products	
	for product in products.keys():
		string = product[:width_products].rjust(width_products)
	
		for day in days.keys():
			if days[day]['products'].has_key(product):
				string += str(days[day]['products'][product]).rjust(width_days)
			else:
				string += '---'.rjust(width_days)

		string += str(products[product]).rjust(width_days)

		print string

	for currency in currencies.keys():
		string = currency.rjust(width_products)

		for day in days.keys():
			if days[day]['currencies'].has_key(currency):
				string += str(formatPrice(days[day]['currencies'][currency]).rjust(width_days))
			else:
				string += '---'.rjust(width_days)

		string += formatPrice(str(currencies[currency])).rjust(width_days)

		print string
	
	for IP in IPs.keys():
		print 'Maschine %s %s' % (IP, IPs[IP])
	print 'Umsatz letzte Stunde: %sEUR' % formatPrice(letzteStunde)

	
	for key in histograms.keys():
		if key != 'undefined' and key != 'Pfand':
			print
			h = histograms[key]
			print 'Stückzahlen: %s (max: %s)' % (key, h.yMax)
			print h.outputMatrix(0, 24, 0, 7)
			print '0 2 4 6 8 10121416182022' 
	
	time.sleep(60)
