import csv
import datetime as dt
from bokeh.plotting import figure, output_file, show


class Battery():
	def __init__(self, capacity):
		self.capacityMWh = capacity
		self.currentCharge = 0.0
		self.maxHalfHourlyDischarge = 0.5
		self.numCycles = 0
	
	def charge(self, MWh):
		amountToCharge = min(self.capacityMWh - self.currentCharge, MWh)
		self.currentCharge = self.currentCharge + amountToCharge
		return MWh - amountToCharge

	def discharge(self):
		cycleFraction = self.chargeFraction()

		amountToDischarge = min(self.currentCharge, self.maxHalfHourlyDischarge)
		self.currentCharge = self.currentCharge - amountToDischarge
		
		cycleFraction -= self.chargeFraction()
		self.numCycles += cycleFraction

		return amountToDischarge
	
	def chargeFraction (self):
		return self.currentCharge / self.capacityMWh
	
	def getNumCycles(self):
		return self.numCycles




solarFile = open('solar-nem-half-hourly.csv')

# Input data is normalised to kWh/kWp or MWh / MWp (equivalent)
lines = csv.DictReader(solarFile)
lines = list(lines)

# Convert types from strings to floats/ ints
for line in lines:
	line['All'] = float(line['All'])
	line['Optimal'] = float(line['Optimal'])
	line['Price'] = float(line['Price'])
	


# Pure solar NEM revenue
for line in lines:
	line['pure-solar-revenue-all'] = line['All'] * line['Price']
	line['pure-solar-revenue-optimal'] = line['Optimal'] * line['Price']


# Luke and Naomi's Awesome Dispatch Strategy
priceThreshold = 80
battery = Battery(1)
for dataPoint in lines:
	# If under threshold......
	if(dataPoint['Price'] < priceThreshold):
		# Charge the battery, get whatever is left over. 
		remainingMWh = battery.charge(dataPoint['Optimal'])
		# Sell the remaining energy
		dataPoint['battery-revenue'] = remainingMWh * dataPoint['Price']
	else:
		dataPoint['battery-revenue'] = dataPoint['Price'] * (dataPoint['Optimal'] + battery.discharge())






# Graphing Below 

# prepare some data
all = []
optimal = []
timePeriod = []
cumulativeSolarRevenueAll = []
cumulativeSolarRevenueOptimal = []
cumulativeBatteryOptimal = []

hourNum = 0.0
cumulativeAll = 0
cumulativeOptimal = 0
cumulativeBattery = 0
for line in lines:
	all.append(line['All'])
	optimal.append(line['Optimal'])
	cumulativeAll += line['pure-solar-revenue-all']
	cumulativeOptimal += line['pure-solar-revenue-optimal']
	cumulativeBattery += line['battery-revenue']
	cumulativeSolarRevenueAll.append(cumulativeAll)
	cumulativeSolarRevenueOptimal.append(cumulativeOptimal)
	cumulativeBatteryOptimal.append(cumulativeBattery)


	timePeriod.append(hourNum)
	hourNum += 0.5


# for line in lines:
# 	x.append()

# output to static HTML file
output_file("lines.html")

# create a new plot with a title and axis labels
p = figure(title="Cumulative Revenue - Battery vs Solar ("+str(battery.getNumCycles())+" Cycles)", x_axis_label='x', y_axis_label='y', width=1200)

# add a line renderer with legend and line thickness
# p.line(timePeriod, optimal,legend="Optimal.", line_width=1)
# p.line(timePeriod, all,legend="Optimal.", line_width=1)
p.line(timePeriod, cumulativeSolarRevenueAll,legend="Cumulative Solar Revenue - All", line_width=1)
p.line(timePeriod, cumulativeSolarRevenueOptimal,legend="Cumulative Solar Revenue - Optimal", line_width=1, line_color="pink")
p.line(timePeriod, cumulativeBatteryOptimal,legend="Cumulative Battery Revenue - Optimal", line_width=1, line_color="green")

# show the results
show(p)
