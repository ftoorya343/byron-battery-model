import csv
import datetime as dt
from bokeh.plotting import figure, output_file, show
import numpy as np


from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, TextInput
from bokeh.plotting import figure
from bokeh.models.widgets import Button






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
	


def calculateBatteryRevenue(lines, MWh, priceThreshold, solarCapacityMW):
	batteryRevenue = 0
	allRevenue = 0
	optimalRevenue = 0


	# Pure solar NEM revenue
	for line in lines:
		line['pure-solar-revenue-all'] = line['All'] * solarCapacityMW * line['Price']
		line['pure-solar-revenue-optimal'] = line['Optimal'] * solarCapacityMW * line['Price']
		allRevenue  +=line['pure-solar-revenue-all']
		optimalRevenue  +=line['pure-solar-revenue-optimal']
		


	print "Calculating Battery Revenue"
	# Luke and Naomi's Awesome Dispatch Strategy
	priceThreshold = priceThreshold
	battery = Battery(MWh)
	for dataPoint in lines:
		# If under threshold......
		if(dataPoint['Price'] < priceThreshold):
			# Charge the battery, get whatever is left over. 
			remainingMWh = battery.charge(dataPoint['Optimal'] * solarCapacityMW)
			# Sell the remaining energy
			dataPoint['battery-revenue'] = remainingMWh * dataPoint['Price']
		else:
			# Sell whatever we can from the battery and the solar system.
			dataPoint['battery-revenue'] = dataPoint['Price'] * (dataPoint['Optimal'] * solarCapacityMW + battery.discharge())
		batteryRevenue  +=dataPoint['battery-revenue']
			
	print "Finished Calculating Battery Revenue"
	return (battery.getNumCycles(), allRevenue, optimalRevenue, batteryRevenue)



def generateChartingDict(lines):

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


	source = dict(
		timePeriod=timePeriod, 
		cumulativeSolarRevenueAll=cumulativeSolarRevenueAll, 
		cumulativeSolarRevenueOptimal=cumulativeSolarRevenueOptimal,
		cumulativeBatteryOptimal=cumulativeBatteryOptimal)
	
	return source


(numCycles, allRevenue, optimalRevenue, batteryRevenue) = calculateBatteryRevenue(lines=lines, MWh=0.099, priceThreshold=80, solarCapacityMW = 0.099)

source = ColumnDataSource(data=generateChartingDict(lines))



# for line in lines:
# 	x.append()

# output to static HTML file
output_file("lines.html")



# Set up the plot
plot = figure(title="Cumulative Revenue Over Time    --    Cycles: "+str("%.2f" %numCycles)+" Solar Revenue: $"+str("%.2f" %allRevenue)+" Optimal Solar Revenue: $"+str("%.2f" %optimalRevenue)+" Battery Revenue: $"+str("%.2f"%batteryRevenue), 
	x_axis_label='Hour of Year', 
	y_axis_label='Revenue ($AUD)', 
	width=1200)
# plot.line(timePeriod, optimal,legend="Optimal.", line_width=1)
# plot.line(timePeriod, all,legend="Optimal.", line_width=1)
plot.line('timePeriod', 'cumulativeSolarRevenueAll',source=source, legend="Cumulative Solar Revenue - All", line_width=1)
plot.line('timePeriod', 'cumulativeSolarRevenueOptimal',source=source, legend="Cumulative Solar Revenue - Optimal", line_width=1, line_color="pink")
plot.line('timePeriod', 'cumulativeBatteryOptimal',source=source, legend="Cumulative Battery Revenue - Optimal", line_width=1, line_color="green")

plot.legend[0].orientation = "horizontal"
# Set up widgets

batterySizeMWh = Slider(title="Battery Capacity (MWh)", value=0.099, start=0, end=1.0, step=0.001)
solarSizeMWh = Slider(title="Solar Capacity (MW)", value=0.099, start=0, end=2.0, step=0.001)
priceThreshold = Slider(title="Battery Dispatch Price Threshold ($/MWh)", value=80.0, start=80.0, end=1000.0)

def update_data():
	# Get the current slider values
	solarCap = solarSizeMWh.value
	batteryCap = batterySizeMWh.value
	priceThresh = priceThreshold.value

	(numCycles, allRevenue, optimalRevenue, batteryRevenue) = calculateBatteryRevenue(lines=lines, MWh=batteryCap, priceThreshold=priceThresh, solarCapacityMW = solarCap)
	source.data = generateChartingDict(lines)
	plot.title.text = "Cumulative Revenue Over Time    --    Cycles: "+str("%.2f" %numCycles)+" Solar Revenue: $"+str("%.2f" %allRevenue)+" Optimal Solar Revenue: $"+str("%.2f" %optimalRevenue)+" Battery Revenue: $"+str("%.2f"%batteryRevenue)

# for w in [batterySizeMWh, solarSizeMWh, priceThreshold]:
# 	w.on_change('value', update_data)



button = Button(label="Re-Calculate", button_type="success")

button.on_click(update_data)


inputs = widgetbox(batterySizeMWh, solarSizeMWh, priceThreshold, button)

curdoc().add_root(row(inputs, plot, width=800))
curdoc().title = "Solar and Battery Simulator"
