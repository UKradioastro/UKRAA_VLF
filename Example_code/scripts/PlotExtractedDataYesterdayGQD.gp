#!/usr/bin/gnuplot -persist
#
#    
#    	G N U P L O T
#    	Version 5.2 patchlevel 6    last modified 2019-01-01 
#    
#    	Copyright (C) 1986-1993, 1998, 2004, 2007-2018
#    	Thomas Williams, Colin Kelley and many others
#    
#    	gnuplot home:     http://www.gnuplot.info
#    	faq, bugs, etc:   type "help FAQ"
#    	immediate help:   type "help"  (plot window: hit 'h')

# Reset gnuplot variables
reset

# Set separator to ","
set datafile separator ","

# Year folder
YFolder = "/".system("date -d yesterday +'%Y'")
#print "YearFolder : ",YFolder

# YearMonth folder
YMFolder = "/".system("date -d yesterday +'%Y-%m'")
#print "YearMonthFolder : ",YMFolder

# YearMonthDay folder
YMDFolder = "/".system("date -d yesterday +'%Y-%m-%d'")
#print "YearMonthDayFolder : ",YMDFolder

# YearMonthDay file
YMDFile = "_".system("date -d yesterday +'%Y-%m-%d'").".txt"
#print "YearMonthDayFile : ",YMDFile

# YearMonthDay plot
YMDPlot = "_".system("date -d yesterday +'%Y-%m-%d'").".png"
#print "YearMonthDayPlot : ",YMDPlot



# Information on where the data is stored on the RPi +++++++++++++++++++++++++++++++++++++++++++++++++
FileNumber   = "/home/pi/VLF/data/EventPlotDataGQD".YFolder.YMFolder.YMDFolder."/NumberOfEvents".YMDFile
#print "FileNumber is : ",FileNumber

# Number of event for yesterday from NumberEvent
textInfoRow = 1
textInfoColumn = 1
set terminal unknown
plot FileNumber every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
NumberOfEvents = textVar
print "Number of events : ", NumberOfEvents

# start of do loop - goes all to bottom
do for [k=1:NumberOfEvents] {
#print k
EventNo = k
#print "Event number being plotted : ",EventNo

# Reset gnuplot variables
reset

# Set separator to ","
set datafile separator ","

# Information on where the data is stored on the RPi +++++++++++++++++++++++++++++++++++++++++++++++++
FileVLF      = "/home/pi/VLF/data/EventPlotDataGQD".YFolder.YMFolder.YMDFolder."/VLF_Event_".EventNo.YMDFile
#print "FileVLF is  : ",FileVLF
FileXray     = "/home/pi/VLF/data/EventPlotDataGQD".YFolder.YMFolder.YMDFolder."/Xray_Event_".EventNo.YMDFile
#print "FileXray is : ",FileXray
FileData     = "/home/pi/VLF/data/EventPlotDataGQD".YFolder.YMFolder.YMDFolder."/Data_Event_".EventNo.YMDFile
#print "FileData is : ",FileData

# Start of event from Data_Event_(no.)
textInfoRow = 1
textInfoColumn = 1
set terminal unknown
plot FileData every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
StartEvent = textVar
#print "Start of event : ", StartEvent

# Peak of event from Data_Event_(no.)
textInfoRow = 1
textInfoColumn = 2
set terminal unknown
plot FileData every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
PeakEvent = textVar
#print "Peak of event : ", PeakEvent

# End of event from Data_Event_(no.)
textInfoRow = 1
textInfoColumn = 3
set terminal unknown
plot FileData every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
EndEvent = textVar
#print "End of event : ", EndEvent

# Class of event from Data_Event_(no.)
textInfoRow = 1
textInfoColumn = 4
set terminal unknown
plot FileData every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
ClassEvent = textVar
#print "Class of event : ", ClassEvent

# Start of X axis time
textInfoRow = 1
textInfoColumn = 1

set terminal unknown
plot FileVLF every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
StartXaxis = textVar
#print "X axis start time : ",StartXaxis

# End of X axis time
stats FileVLF using 1
#print "Number of records in file :",STATS_records
textInfoRow = STATS_records
#print "textInfoRow changed to : ",textInfoRow

set terminal unknown
plot FileVLF every ::textInfoRow-1::textInfoRow-1 using (textVar=stringcolumn(textInfoColumn),0)
#print textVar
EndXaxis = textVar
#print "X axis end time : ",EndXaxis

# Set data types
set xdata time

# Set format types
set format x "%H:%M" timedate
set format y "%.1f" 
set format y2 "10^{%T}" 
set timefmt "%Y-%m-%d %H:%M:%S"

# Set grid format
set grid xtics nomxtics ytics nomytics noztics nomztics nortics nomrtics \
 nox2tics nomx2tics noy2tics nomy2tics nocbtics nomcbtics
set grid layerdefault linetype 0 linecolor 0 linewidth 0.500 dashtype solid,  linetype 0 linecolor 0 linewidth 0.500 dashtype solid

# Set title of graph (not used) ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#set title GraphTitle
#set label 10 GraphTitle at screen 0.5,1.0 center front

# Title for graph - variable
GraphTitle = "Graph of class ".ClassEvent." SID event from ".system("date -d yesterday +'%A %d %B %Y'"). \
 "\n Starting at : ".StartEvent."UTC, peaking at : ".PeakEvent."UTC and ending at : ".EndEvent."UTC \n"

# Set Legend (Key) above plot ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
set key outside above right
#set key bmargin center
set key Right
set key samplen 10
set key title GraphTitle
set key nobox

# X AXIS set functions +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# X-axis tics
set xtics border out scale 1,0.5 nomirror norotate autojustify
set xtics norangelimit 900
set xtics textcolor rgb "#000000"
set mxtics 3

# X-axis label and ranges
set xlabel "Time (UTC)" 
set xlabel textcolor rgb "#000000" norotate
set xrange [StartXaxis:EndXaxis] noreverse writeback

# Y1 AXIS set functions ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Y-axis tics
set mytics 2.0
set ytics border out scale 1,0.5 nomirror norotate  autojustify
set ytics norangelimit autofreq
set ytics textcolor rgb "#A020F0"

# Y-axis labels and ranges
set ylabel "UKRAA Anthorn [GQD] VLF (19.58kHz) Receiver signal output (V)"         # axis lable and units
set ylabel textcolor rgb "#A020F0" rotate                 # axis text colour
set yrange [ 0.00000 : 5.00000 ] noreverse writeback      # axis range 0.0 to 5.0 volts

# Y2 AXIS set functions ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Y2-axis tics
set my2tics default
set y2tics border out scale 1,0.5 nomirror norotate  autojustify
set y2tics norangelimit logscale autofreq
set y2tics textcolor rgb "#FF0000"

# Y2-axis label and ranges
set y2label "NOAA GOES-16 X-ray Flux (W/m^2)" 			# axis lable and units 
set y2label textcolor rgb "#FF0000" rotate			# axis text colour
set y2range [ 1.00000e-07 : 0.0100000 ] noreverse writeback	# axis range 

# Y2-axis scale power of 10 - so log scale
set logscale y2 10						# set to log scale

# set gnuplot terminal
set terminal pngcairo enhanced font "DejaVuSansCondensed, 10" rounded size 640,540

# set gnuplot output
OutFile = "/home/pi/VLF/data/EventPlotDataGQD".YFolder.YMFolder.YMDFolder."/SIDplot".EventNo.YMDPlot
#print"Output file is : ",OutFile
set output OutFile

# Plot command +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#
plot FileVLF    using 1:2 linetype 1 linewidth 1 linecolor rgb "#A020F0" title \
		"Anthorn [GQD] VLF (19.58kHz)" with lines,\
     FileXray   using 1:2 linetype 7 linewidth 1 axes x1y2 title \
		"NOAA GOES-16 Xray (long = 0.1nm to 0.8nm)" with lines, \
     FileData   using 6:(4):5 with labels font "sans,8" offset -1, char 0 rotate by 90 notitle,\
     FileData   using 6:(0):(0):(5) with vectors linetype 0 linewidth 1 linecolor rgb "#0000FF" nohead notitle,\
     FileData   using 8:(4):7 with labels font "sans,8" offset 0, char 0 rotate by 90 notitle,\
     FileData   using 8:(0):(0):(5) with vectors linetype 0 linewidth 1 linecolor rgb "#0000FF" nohead notitle,\
     FileData   using 10:(4):9 with labels font "sans,8" offset 1, char 0 rotate by 90 notitle,\
     FileData   using 10:(0):(0):(5) with vectors linetype 0 linewidth 1 linecolor rgb "#0000FF" nohead notitle,\
     
# This is important because it closes our output file.
set output

#end of loop
print k
}

# EOF