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

set terminal pngcairo enhanced font "DejaVuSansCondensed, 10" rounded size 640,540 
set output "/home/pi/VLF/data/WWWupload/VLFplot21750.png"

# Set up data paths
#
# Aerial data
# pathAerial = /home/pi/VLF/data/Aerial19600/YYYY/YYYY-mm/YYYY-mm-dd.txt
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
# pathEvent = /home/pi/VLF/data/NOAAxrayFlares/primaryYYYY/YYYY-mm/YYYY-mm-dd.txt
#
# png plot output
# pathPlot = /home/pi/VLF/data/WWWupload/VLFplot21750.png
#
pathAerial = "/home/pi/VLF/data/Aerial19600"
pathSunRise = "/home/pi/VLF/data/SunRise"
pathSunSet = "/home/pi/VLF/data/SunSet"
pathXray = "/home/pi/VLF/data/NOAAxrays/primary"
pathEvent = "/home/pi/VLF/data/NOAAxrayFlares/primary"
#pathPlot = "/home/pi/VLF/data/WWWupload/VLFplot21750.png"

# Year folder
YearFolder = "/".system("date -d yesterday +'%Y'")

# YearMonth folder
YearMonthFolder = "/".system("date -d yesterday +'%Y-%m'")

# YearMonthDay file
YmdFile = "/".system("date -d yesterday +'%Y-%m-%d'").".txt"

# Start of X axis time
StartXaxis = system("date -d yesterday +'%Y-%m-%d'")." 00:00:00"

# Label positions along X axis (time)
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
GraphTitle = "Anthorn VLF and NOAA GOES primary X-ray data for ".system("date -d yesterday +'%A %d %B %Y'")."\n Graph is updated every day at 9.30am \n"

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
set ylabel "UKRAA VLF (19.58kHz) Receiver signal output (V)" 
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

# Plot command
plot FileAerial  using 1:2 linetype 1 linewidth 1 linecolor rgb "#A020F0" title "Anthorn [GQD] VLF (19.58kHz)" with lines,\
     FileSunRise using 1:(0):(0):(5) with vectors linewidth 3 linecolor rgb "#CD853F" nohead notitle,\
     FileSunRise using 1:(1.2):2 with labels font "sans,8" offset 1, char 0 rotate by 90 notitle,\
     FileSunSet  using 1:(0):(0):(5) with vectors linewidth 3 linecolor rgb "#CD853F" nohead notitle,\
     FileSunSet  using 1:(1.2):2 with labels font "sans,8" offset -1, char 0 rotate by 90 notitle,\
     FileXray    using 1:5 linetype 7 linewidth 1 axes x1y2 title "NOAA GOES Xray (long = 0.1nm to 0.8nm)" with lines,\
     FileEvents  using 3:2:($2*5):($2/5) axes x1y2 pointsize 0 with yerrorbars title "Solar flares start and end times with Class",\
     FileEvents  using 4:2:($2*5):($2/5) axes x1y2 pointsize 0 with yerrorbars notitle,\
     FileEvents  using 1:($2*5):5 every 2::0 axes x1y2 with labels font "sans,6" textcolor rgb "#0000FF" offset 0.0,+1.0 notitle,\
     FileEvents  using 1:($2*5):5 every 2::1 axes x1y2 with labels font "sans,6" textcolor rgb "#0000FF" offset 0.0,+2.0 notitle

# Replot to terminal and create .png image with data tag for future upload to web page
set terminal pngcairo enhanced font "DejaVuSansCondensed, 10" rounded size 640,540 

# setting output path to include data stamp

# Path to directory to store file
pathPlot = "/home/pi/VLF/data/Plots/VLFplot21750"

# Output YearMonthDay stamp
OutYmdFile = system("date -d yesterday +'%Y%m%d'")

# set output path to Plot folder
set output pathPlot."-".OutYmdFile.".png"

# replot graph to Plot folder with added date tag
replot
# end replot

# print info to log file
set print "/home/pi/VLF/LogFiles/GNUplotGQD.log" append
PlotCompleted = system("date -d today +'%Y-%m-%d %H:%M:%S'")
PlotYesterday = system("date -d yesterday +'%Y-%m-%d'")
print "Yesterdays plot of GQD @ 19.6kHz for ", PlotYesterday, " was completed at " , PlotCompleted
set print

# This is important because it closes our output file.
set output

# EOF