# PlotRolling.gp - generic rolling 24-hour plot of VLF receiver output with
# NOAA GOES primary X-ray flux overlay.
#
# Driven by PlotDataRolling.py, which passes variables with gnuplot -e:
#   required : OutputFile, GraphTitle, GraphSubtitle, StartTime, EndTime
#   optional : AerialFile1, AerialFile2  (yesterday's and today's data)
#              AerialTitle               (legend text for the aerial trace)
#              XrayFile1, XrayFile2      (yesterday's and today's data)
#              FlareFile1, FlareFile2    (yesterday's and today's flare events)
#              NightCount + Night<i>Start/Night<i>End
#                                        (night shading, clipped to window)
#              SunMarkCount + SunMark<i>Time/SunMark<i>Label
#                                        (sunrise/sunset lines in window)
#              OffAirCount + OffAir<i>Start/OffAir<i>End/OffAir<i>Mid,
#              OffAirLabel               (transmitter off-air windows)
# Optional variables are simply not defined when the data is unavailable;
# the plot adapts (e.g. X-ray only while no aerial data exists yet).
#
# Data formats (comma separated):
#   Aerial : yyyy-mm-dd hh:mm:ss,voltage
#   X-ray  : yyyy-mm-dd hh:mm:ss,satellite,short_flux,0.05-0.4nm,long_flux,0.1-0.8nm
#   Flares : begin,satellite,begin_class,max,max_class,max_flux,end,end_class

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

FMT = "%Y-%m-%d %H:%M:%S"

set style textbox opaque margins 3.0,3.0 fillcolor rgb "#FFFFFF" border rgb "#000000" linewidth 1.0

# Grey night shading (clipped to the 24-hour window) with a compact label
# in regions wide enough to hold one
if (exists("NightCount")) {
    do for [i=1:NightCount] {
        ns = value(sprintf("Night%dStart", i))
        ne = value(sprintf("Night%dEnd", i))
        set object 10+i rectangle from first ns, graph 0 to first ne, graph 1 behind fillcolor rgb "#BEBEBE" fillstyle solid 1.0 noborder
        if (strptime(FMT, ne) - strptime(FMT, ns) >= 10800) {
            nm = strftime(FMT, (strptime(FMT, ns) + strptime(FMT, ne)) / 2)
            set label 10+i "No solar flares\ndetectable" at first nm, graph 0.90 center font "sans,7" front boxed
        }
    }
}

# Sunrise/sunset vertical lines with rotated labels
if (exists("SunMarkCount")) {
    do for [i=1:SunMarkCount] {
        st = value(sprintf("SunMark%dTime", i))
        set arrow 10+i from first st, graph 0 to first st, graph 1 nohead lc rgb "#CD853F" lw 2
        set label 30+i value(sprintf("SunMark%dLabel", i)) at first st, graph 0.30 rotate by 90 offset char 1,0 font "sans,8" front
    }
}

# Transmitter daily off-air window annotations (can occur twice in 24 hours)
if (exists("OffAirCount")) {
    do for [i=1:OffAirCount] {
        os = value(sprintf("OffAir%dStart", i))
        oe = value(sprintf("OffAir%dEnd", i))
        om = value(sprintf("OffAir%dMid", i))
        set arrow 40+i from first os, 1.0 to first oe, 1.0 heads size screen 0.008,90 lw 2 front
        set label 50+i OffAirLabel at first om, graph 0.70 center font "sans,7" front boxed
        set arrow 60+i from first om, graph 0.66 to first om, 1.15 lw 1 front
    }
}

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
# Flare markers sit on the X-ray (y2) axis: dotted vertical bars at the
# flare begin and end times with the maximum class labelled above
FlareTitle = "Solar flare start/end with class"
if (HaveXray) {
    do for [i=1:2] {
        if (exists(sprintf("FlareFile%d", i))) {
            ff = value(sprintf("FlareFile%d", i))
            cmd = cmd . sep . sprintf("'%s' using 1:($6/5):(0):($6*5-$6/5) axes x1y2 with vectors nohead dt 3 lw 1 lc rgb '#0000FF' title '%s'", ff, FlareTitle)
            sep = ", "
            FlareTitle = ""
            cmd = cmd . sep . sprintf("'%s' using 7:($6/5):(0):($6*5-$6/5) axes x1y2 with vectors nohead dt 3 lw 1 lc rgb '#0000FF' notitle", ff)
            sep = ", "
            cmd = cmd . sep . sprintf("'%s' using 1:($6*5):5 axes x1y2 with labels font 'sans,7' textcolor rgb '#0000FF' offset 0,0.6 notitle", ff)
            sep = ", "
        }
    }
}

if (cmd eq "") {
    print "PlotRolling.gp: no data files supplied - nothing to plot"
    exit
}

eval("plot " . cmd)

set output

# EOF
