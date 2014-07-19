# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os, plistlib, glob, time
from ynlib.system import GetChr 
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


	
	
	

width_products = 20
width_days = 11

while True:	

	days = {}
	products = {}
	currencies = {}
	histogram = Histogram()


	histograms = (
		[Histogram(), 'O-Saft', 'Orange Juice 0,2L', 'Orange Juice 0,4L'],
		[Histogram(), 'Caffè', 'einf. Espresso', 'dopp. Espresso', 'einf. Cappuccino', 'dopp. Cappuccino'],
		[Histogram(), 'Chai/Hot Chocolate', 'Hot Chocolate', 'Chai Latte'],
		)

	for IP in args['IPs'].split(','):
		foldername = os.path.basename(args['storageFolder'])
		IPfolder = os.path.join(args['storageFolder'], IP)
		if not IPfolder.endswith('/'):
			IPfolder += '/'
		os.system('mkdir %s' % IPfolder)
		p = 'rsync -avze ssh pos@%s:/home/pos/feldkasse/%s/ %s' % (IP, foldername, IPfolder)
		print p
#		os.system(p)


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
				if not days[dayname]['products'].has_key(product):
					days[dayname]['products'][product] = 0
				days[dayname]['products'][product] += plist['products'][product]
				#total
				if not products.has_key(product):
					products[product] = 0
				products[product] += plist['products'][product]
			
			
				for i in range(len(histograms)):
					if product in histograms[i]:
						histograms[i][0].addValue(int(time.localtime(plist['time'])[3]), plist['products'][product])

			# price
			if not days[dayname]['currencies'].has_key(plist['currency']):
				days[dayname]['currencies'][plist['currency']] = 0
			days[dayname]['currencies'][plist['currency']] += plist['price']
			#total
			if not currencies.has_key(plist['currency']):
				currencies[plist['currency']] = 0
			currencies[plist['currency']] += plist['price']

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
	

	
	for i in histograms:
		print
		h = i.pop(0)
		desc = i.pop(0)
		print 'Stückzahlen: %s (max: %s)' % (desc, h.yMax)
		print h.outputMatrix(0, 24, 0, 7)
		print '0 2 4 6 8 10121416182022' 
	
	time.sleep(60)
