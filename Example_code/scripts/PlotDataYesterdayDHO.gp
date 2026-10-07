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

# Clear gnuplot terminal
#clear

set terminal pngcairo enhanced font "DejaVuSansCondensed, 10" rounded size 640,540 
set output "/home/pi/VLF/data/WWWupload/VLFplot23400.png"

# Set local
#set locale "en_GB"

# Set up data paths
#
# Aerial data
# pathAerial = /home/pi/VLF/data/Aerial/YYYY/YYYY-mm/YYYY-mm-dd.txt
#
# Sun Rise data
# pathSunRise = /home/pi/VLF/data/SunRise/YYYY/YYYY-mm/YYYY-mm-dd.txt
#
# Sun Set data
# pathSunSet = /home/pi/VLF/data/SunSet/YYYY/YYYY-mm/YYYY-mm-dd.txt
#
# X-ray data
# pathXray = /home/pi/VLF/data/NOAAxrays/primary/YYYY/YYYY-mm/YYYY-mm-dd.txt
#
# Event data
# pathEvent = /home/pi/VLF/data/EventsG16/YYYY/YYYY-mm/YYYY-mm-dd.txt
#
# png plot output
# pathPlot = /home/pi/VLF/data/WWWupload/VLFplot.png
#
pathAerial = "/home/pi/VLF/data/Aerial"
pathSunRise = "/home/pi/VLF/data/SunRise"
pathSunSet = "/home/pi/VLF/data/SunSet"
pathXray = "/home/pi/VLF/data/NOAAxrays/primary"
pathEvent = "/home/pi/VLF/data/NOAAxrayFlares/primary"
#pathPlot = "/home/pi/VLF/data/WWWupload/VLFplot23400.png"

# Year folder
YearFolder = "/".system("date -d yesterday +'%Y'")

# YearMonth folder
YearMonthFolder = "/".system("date -d yesterday +'%Y-%m'")

# YearMonthDay file
YmdFile = "/".system("date -d yesterday +'%Y-%m-%d'").".txt"

# Start of X axis time
StartXaxis = system("date -d yesterday +'%Y-%m-%d'")." 00:00:00"

# DHO38 shutdown time for X axis
DHO38Down = system("date -d yesterday +'%Y-%m-%d'")." 07:00:00"
DHO38Up = system("date -d yesterday +'%Y-%m-%d'")." 08:00:00"
DHO38Label = system("date -d yesterday +'%Y-%m-%d'")." 01:30:00"
DHO38Arrow = system("date -d yesterday +'%Y-%m-%d'")." 07:30:00"
SunRiseLabel = system("date -d yesterday +'%Y-%m-%d'")." 00:00:30"
SunSetLabel = system("date -d yesterday +'%Y-%m-%d'")." 23:59:30"


# End of X axis time
EndXaxis = system("date -d today +'%Y-%m-%d'")." 00:00:00"

# Path to each data file for graphing
FileAerial = pathAerial.YearFolder.YearMonthFolder.YmdFile
FileSunRise = pathSunRise.YearFolder.YearMonthFolder.YmdFile
FileSunSet = pathSunSet.YearFolder.YearMonthFolder.YmdFile
FileXray = pathXray.YearFolder.YearMonthFolder.YmdFile
FileEvents = pathEvent.YearFolder.YearMonthFolder.YmdFile


# Set separator to ","
set datafile separator ","

# Get sun rise time from FileSunRise and save as variable to be used in object 1 rectangle
SunRiseTime = system("head -c 19 ".FileSunRise)

# Get sun set time from FileSunSet and save as variable to be used in object 2 rectangle
SunSetTime = system("head -c 19 ".FileSunSet)

# Get start of event time from FileEvent and save as variable to use in object 3
EventStartTime = system("head -c 19 ".FileEvents)



# Title for graph
GraphTitle = "Ramsloh VLF and NOAA GOES primary X-ray data for ".system("date -d yesterday +'%A %d %B %Y'")."\n Graph is updated every day at 9.30am \n"

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

# Set title of graph
#set title GraphTitle
#set label 10 GraphTitle at screen 0.5,1.0 center front

# Set Legend (Key) above plot
set key outside above right
#set key bmargin center
set key Right
set key samplen 10
set key title GraphTitle
set key nobox

# X-axis tics
set mxtics 2.0
set xtics border out scale 1,0.5 nomirror norotate  autojustify
set xtics norangelimit 7200
set xtics textcolor rgb "#000000"

# Y-axis tics
set mytics 2.0
set ytics border out scale 1,0.5 nomirror norotate  autojustify
set ytics norangelimit autofreq
set ytics textcolor rgb "#A020F0"

# Y2-axis tics
set my2tics default
set y2tics border out scale 1,0.5 nomirror norotate  autojustify
set y2tics norangelimit logscale autofreq
set y2tics textcolor rgb "#FF0000"

# X-axis label and ranges
set xlabel "Time (UTC)" 
set xlabel textcolor rgb "#000000" norotate
set xrange [ StartXaxis : EndXaxis ] noreverse writeback

# Y-axis labels and ranges
set ylabel "UKRAA VLF (23.4kHz) Receiver signal output (V)" 
set ylabel textcolor rgb "#A020F0" rotate
set yrange [ 0.00000 : 5.00000 ] noreverse writeback

# Y2-axis label and ranges
set y2label "NOAA GOES primary X-ray Flux (W/m^2)" 
set y2label textcolor rgb "#FF0000" rotate
set y2range [ 1.00000e-07 : 0.0100000 ] noreverse writeback

# Y2-axis scale power of 10 - so log scale
set logscale y2 10

# errorbar settings
set errorbars 0.0 linetype 0 linewidth 1 linecolor rgb "#0000FF"

# Set textbox style
set style textbox opaque margins  3.0,3.0 fillcolor rgb "#FFFFFF" border rgb "#000000" linewidth  3.0

# object 1 rectangle for start of x-axis up to Sun Rise time
set object 1 rectangle from first StartXaxis,graph 0 to first SunRiseTime,graph 1 behind
set object 1 rectangle fillcolor rgb "#BEBEBE" fillstyle solid 1.0 noborder
set label 1 "No solar flares\ndetectable\nuntil sunrise" at SunRiseLabel,4.7 center font "sans,8" front boxed
set arrow 1 from StartXaxis,4.5 to SunRiseTime,4.5 linewidth 3 empty size screen 0.025,40,20

# object 2 rectangle for Sun Set time to end of x-axis
set object 2 rectangle from first SunSetTime,graph 0 to first EndXaxis,graph 1 behind
set object 2 rectangle fillcolor rgb "#BEBEBE" fillstyle solid 1.0 noborder
set label 2 "No solar flares\ndetectable\nafter sunset" at SunSetLabel,4.7 center font "sans,8" front boxed
set arrow 2 from EndXaxis,4.5 to SunSetTime,4.5 linewidth 3 empty size screen 0.025,40,20


# Show when transmitter is off air daily
# Off-air daily from 7:00 to 8:00 UTC
set arrow 3 from DHO38Down,1.0 to DHO38Up,1.0 heads size screen 0.005,90 linestyle -1 linewidth 2
set label 3 "Ramsloh [DHO38] VLF\noff-air daily\nfrom 7:00 to 8:00 UTC" at DHO38Label,3.65 center font "sans,8" front boxed
set arrow 4 from DHO38Label,3.75 to DHO38Arrow,1.1 size 0.3,90 linestyle -1 linewidth 2

# Add line for X-ray Solar flare levels
#
# classification | Flux range
#       A        |    < 10^-7
#       B        |    10^-7 to 10^-6
#       C        |    10^-6 to 10^-5
#       M        |    10^-5 to 10^-4
#       X        |    > 10^-4
#
# Draw a line from the right end of the graph to the left end of the graph at
# the y2 values from table above
# The line should not have an arrowhead
# Linewidth = 1
# Linecolor = black
# It should be in front of anything else drawn
#set arrow 5 from graph 0.95,second 1E-2 to graph 0.95, second 1E-4 heads dashtype 2 linewidth 2 linecolor rgb "#000000" empty size screen 0.025,40,20 front
#set arrow 6 from graph 0.95,second 1E-4 to graph 0.95, second 1E-5 heads dashtype 3 linewidth 2 linecolor rgb "#000000" empty size screen 0.025,40,20 front
#set arrow 7 from graph 0.95,second 1E-5 to graph 0.95, second 1E-6 heads dashtype 4 linewidth 2 linecolor rgb "#000000" empty size screen 0.025,40,20 front
#set arrow 8 from graph 0.95,second 1E-6 to graph 0.95, second 1E-7 heads dashtype 5 linewidth 2 linecolor rgb "#000000" empty size screen 0.025,40,20 front
#set arrow 9 from graph 0.95,second 1E-7 to graph 0.95, second 1E-9 heads dashtype 5 linewidth 2 linecolor rgb "#000000" empty size screen 0.025,40,20 front

# Put a label -3db at 80% the width of the graph and y = -2 (it will be just above the line drawn)
#set label 5 "Solar Flare\nclassification X\nFlux > 10^{-4} W/m^{2}" at graph 0.89, second 5.5E-4 center font "sans,8" front boxed
#set label 6 "Solar Flare\nclassification M\nFlux 10^{-5} to 10^{-4} W/m^{2}" at graph 0.86, second 5.5E-5 center font "sans,8" front boxed
#set label 7 "Solar Flare\nclassification C\nFlux 10^{-6} to 10^{-5} W/m^{2}" at graph 0.86, second 5.5E-6 center font "sans,8" front boxed
#set label 8 "Solar Flare\nclassification B\nFlux 10^{-7} to 10^{-6} W/m^{2}" at graph 0.86, second 5.5E-7 center font "sans,8" front boxed
#set label 9 "Solar Flare\nclassification A\nFlux < 10^{-7} W/m^{2}" at graph 0.89, second 2E-8 center font "sans,8" front boxed

# Plot command
plot FileAerial using 1:2 linetype 1 linewidth 1 linecolor rgb "#A020F0" title "Ramsloh [DHO38] VLF (23.4kHz)" with lines,\
     FileSunRise using 1:(0):(0):(5) with vectors linewidth 3 linecolor rgb "#CD853F" nohead notitle,\
     FileSunRise using 1:(1.2):2 with labels font "sans,8" offset 1, char 0 rotate by 90 notitle,\
     FileSunSet using 1:(0):(0):(5) with vectors linewidth 3 linecolor rgb "#CD853F" nohead notitle,\
     FileSunSet using 1:(1.2):2 with labels font "sans,8" offset -1, char 0 rotate by 90 notitle,\
     FileXray using 1:5 linetype 7 linewidth 1 axes x1y2 title "NOAA GOES Xray (long = 0.1nm to 0.8nm)" with lines,\
     FileEvents using 3:2:($2*5):($2/5) axes x1y2 pointsize 0 with yerrorbars title "Solar flares start and end times with Class",\
     FileEvents using 4:2:($2*5):($2/5) axes x1y2 pointsize 0 with yerrorbars notitle,\
     FileEvents using 1:($2*5):5 every 2::0 axes x1y2 with labels font "sans,6" textcolor rgb "#0000FF" offset 0.0,+1.0 notitle,\
     FileEvents using 1:($2*5):5 every 2::1 axes x1y2 with labels font "sans,6" textcolor rgb "#0000FF" offset 0.0,+2.0 notitle
#     FileEvents using 1:2:5 axes x1y2 with labels font "sans,8" offset 0.0,3.0 notitle
#     FileEvents using 1:2:3:4 axes x1y2 pointsize 0 linetype 0 with yerrorbars notitle,\
#     FileEvents using 1:2:5 axes x1y2 with labels font "sans,8" offset 0,2 notitle
#     FileXray using 1:2 linetype 6 linecolor rgb "#0000FF" linewidth 1 axes x1y2 title "NOAA GOES-16 Xray (short = 0.05nm to 0.4nm)" with lines

# MODIFIED 20/12/21 to add replot with data tag and save in different folder
# Plots folder = /home/pi/VLF/data/Plots

# Replot to terminal and create .png image with data tag for future upload to web page
set terminal pngcairo enhanced font "DejaVuSansCondensed, 10" rounded size 640,540 

# setting output path to include data stamp

# Path to directory to store file
pathPlot = "/home/pi/VLF/data/Plots/VLFplot23400"

# Output YearMonthDay stamp
OutYmdFile = system("date -d yesterday +'%Y%m%d'")

# set output path to Plot folder
set output pathPlot."-".OutYmdFile.".png"

# replot graph to Plot folder with added date tag
replot
# end replot

# print info to log file
set print "/home/pi/VLF/LogFiles/GNUplotDHO.log" append
PlotCompleted = system("date -d today +'%Y-%m-%d %H:%M:%S'")
PlotYesterday = system("date -d yesterday +'%Y-%m-%d'")
print "Yesterdays plot of DHO @ 23.4kHz for ", PlotYesterday, " was completed at " , PlotCompleted
set print

# This is important because it closes our output file.
set output

# EOF