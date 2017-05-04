# The input file here is kWh / kWp

import csv

solarData = open("solar.csv", "r")

lines = []
for line in solarData:
	line = line.strip()
	variables = line.split(',')
	lines.append(variables)

outputData = []

header = lines.pop(0)


# Halve all values and make dates ints (because we are making it half-hourly)
for line in lines:
	
	line[0] = int(line[0])
	line[1] = int(line[1])
	line[2] = int(line[2])
	line[3] = int(line[3])
	line[4] = int(line[4])
	line[5] = float(line[5])/2.0
	line[6] = float(line[6])/2.0


# Insert the averages
for i in range(len(lines)-1):
	currentLine = lines[i]
	nextLine = lines[i+1]
	# Write the current line to the output data. 
	
	# Copy current line to new line, add 30 mins and average the values.
	newLine = currentLine[:]
	newLine[4] = 30
	newLine[5] = (float(currentLine[5]) + float(nextLine[5]) )/ 2.0
	newLine[6] = (float(currentLine[6]) + float(nextLine[6]) )/ 2.0
	# Append current line and the new (half hourly) line to the output data.
	outputData.append(currentLine)
	outputData.append(newLine)






myfile = open('solar-half-hourly.csv', 'wb')
wr = csv.writer(myfile)

print header
wr.writerow(header)
for line in outputData:
	print line
	wr.writerow(line)




