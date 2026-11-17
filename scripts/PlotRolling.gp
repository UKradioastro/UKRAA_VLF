# PlotRolling.gp - generic rolling 24-hour plot of VLF receiver output with
# NOAA GOES primary X-ray flux overlay.
#
# Driven by PlotDataRolling.py, which passes variables with gnuplot -e:
#   required : OutputFile, GraphTitle, GraphSubtitle, StartTime, EndTime
#   optional : AerialFile1, AerialFile2  (yesterday's and today's data)
#              AerialTitle               (legend text for the aerial trace)
#              XrayFile1, XrayFile2      (yesterday's and today's data)
# Optional variables are simply not defined when the data is unavailable;
# the plot adapts (e.g. X-ray only while no aerial data exists yet).
#
# Data formats (comma separated):
#   Aerial : yyyy-mm-dd hh:mm:ss,voltage
#   X-ray  : yyyy-mm-dd hh:mm:ss,satellite,short_flux,0.05-0.4nm,long_flux,0.1-0.8nm

reset

set terminal pngcairo enhanced font "DejaVuSansCondensed,10" rounded size 640,540
set output OutputFile

set datafile separator ","
set xdata time
set timefmt "%Y-%m-%d %H:%M:%S"
set format x "%H:%M" timedate

set grid xtics ytics

set xlabel "Time (UTC)"
set xrange [StartTime:EndTime]
set xtics border out scale 1,0.5 nomirror 7200
set mxtics 2

set key outside above right
set key Right samplen 4 nobox
set key title GraphTitle."\n".GraphSubtitle."\n"

HaveAerial = exists("AerialFile1") + exists("AerialFile2")
HaveXray = exists("XrayFile1") + exists("XrayFile2")

if (HaveAerial) {
    set ylabel "UKRAA VLF receiver output (V)" textcolor rgb "#A020F0"
    set yrange [0:5]
    set format y "%.1f"
    set ytics border out scale 1,0.5 nomirror textcolor rgb "#A020F0"
    set mytics 2
} else {
    set yrange [0:5]
    unset ytics
}

if (HaveXray) {
    set y2label "NOAA GOES primary X-ray Flux (W/m^2)" textcolor rgb "#FF0000"
    set y2range [1e-7:1e-2]
    set logscale y2 10
    set format y2 "10^{%T}"
    set y2tics border out scale 1,0.5 nomirror textcolor rgb "#FF0000"
}

# Build the plot command from whichever data files exist
cmd = ""
sep = ""
AerialKey = 1
if (exists("AerialFile1")) {
    cmd = cmd . sep . sprintf("'%s' using 1:2 with lines lc rgb '#A020F0' lw 1 title '%s'", AerialFile1, AerialTitle)
    sep = ", "
    AerialKey = 0
}
if (exists("AerialFile2")) {
    cmd = cmd . sep . sprintf("'%s' using 1:2 with lines lc rgb '#A020F0' lw 1 title '%s'", AerialFile2, AerialKey ? AerialTitle : "")
    sep = ", "
}
XrayTitle = "NOAA GOES X-ray (0.1-0.8nm)"
XrayKey = 1
if (exists("XrayFile1")) {
    cmd = cmd . sep . sprintf("'%s' using 1:5 axes x1y2 with lines lc rgb '#FF0000' lw 1 title '%s'", XrayFile1, XrayTitle)
    sep = ", "
    XrayKey = 0
}
if (exists("XrayFile2")) {
    cmd = cmd . sep . sprintf("'%s' using 1:5 axes x1y2 with lines lc rgb '#FF0000' lw 1 title '%s'", XrayFile2, XrayKey ? XrayTitle : "")
    sep = ", "
}

if (cmd eq "") {
    print "PlotRolling.gp: no data files supplied - nothing to plot"
    exit
}

eval("plot " . cmd)

set output

# EOF
