# PlotYesterday.gp - generic full-day plot of VLF receiver output with
# NOAA GOES primary X-ray flux, sunrise/sunset shading and solar flare events.
#
# Driven by PlotDataYesterday.py, which passes variables with gnuplot -e:
#   required : OutputFile, GraphTitle, GraphSubtitle, StartTime, EndTime
#   optional : AerialFile, AerialTitle        (the day's VLF data + legend)
#              XrayFile                       (the day's X-ray data)
#              FlareFile                      (the day's flare events)
#              FlareMinFlux                   (W/m2; skip flares peaking
#                                             below this, default 0 = all)
#              SunriseTime, SunsetTime        ("yyyy-mm-dd hh:mm:ss")
#              OffAirStart, OffAirEnd, OffAirLabel (transmitter off-air window)
#              ArchiveFile                    (second, date-stamped output)
# Optional variables are simply not defined when the data is unavailable;
# the plot adapts (e.g. X-ray only while no aerial data exists yet).
#
# Data formats (comma separated):
#   Aerial : yyyy-mm-dd hh:mm:ss,voltage
#   X-ray  : yyyy-mm-dd hh:mm:ss,satellite,short_flux,0.05-0.4nm,long_flux,0.1-0.8nm
#   Flares : begin,satellite,begin_class,max,max_class,max_flux,end,end_class

reset

set terminal pngcairo enhanced font "DejaVuSansCondensed,10" rounded size 960,540
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

set style textbox opaque margins 3.0,3.0 fillcolor rgb "#FFFFFF" border rgb "#000000" linewidth 1.0

FMT = "%Y-%m-%d %H:%M:%S"

HaveAerial = exists("AerialFile")
HaveXray = exists("XrayFile")

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

# Grey shading outside daylight - no SIDs detectable before sunrise/after sunset
if (exists("SunriseTime")) {
    set object 1 rectangle from first StartTime, graph 0 to first SunriseTime, graph 1 behind fillcolor rgb "#BEBEBE" fillstyle solid 1.0 noborder
    set arrow 1 from first SunriseTime, graph 0 to first SunriseTime, graph 1 nohead lc rgb "#CD853F" lw 2
    set label 1 "Sunrise ".substr(SunriseTime, 12, 16)." UTC" at first SunriseTime, graph 0.30 rotate by 90 offset char 1,0 font "sans,8" front
    PreMid = strftime(FMT, (strptime(FMT, StartTime) + strptime(FMT, SunriseTime)) / 2)
    set label 4 "No solar flares\ndetectable\nuntil sunrise" at first PreMid, graph 0.90 center font "sans,8" front boxed
    set arrow 4 from first StartTime, graph 0.80 to first SunriseTime, graph 0.80 empty size screen 0.02,40,20 lw 2 front
}
if (exists("SunsetTime")) {
    set object 2 rectangle from first SunsetTime, graph 0 to first EndTime, graph 1 behind fillcolor rgb "#BEBEBE" fillstyle solid 1.0 noborder
    set arrow 2 from first SunsetTime, graph 0 to first SunsetTime, graph 1 nohead lc rgb "#CD853F" lw 2
    set label 2 "Sunset ".substr(SunsetTime, 12, 16)." UTC" at first SunsetTime, graph 0.30 rotate by 90 offset char -0.5,0 font "sans,8" front
    PostMid = strftime(FMT, (strptime(FMT, SunsetTime) + strptime(FMT, EndTime)) / 2)
    set label 5 "No solar flares\ndetectable\nafter sunset" at first PostMid, graph 0.90 center font "sans,8" front boxed
    set arrow 5 from first EndTime, graph 0.80 to first SunsetTime, graph 0.80 empty size screen 0.02,40,20 lw 2 front
}

# Transmitter daily off-air window annotation
if (exists("OffAirStart")) {
    set arrow 3 from first OffAirStart, 1.0 to first OffAirEnd, 1.0 heads size screen 0.008,90 lw 2 front
    set label 3 OffAirLabel at first OffAirMid, graph 0.70 center font "sans,8" front boxed
    set arrow 6 from first OffAirMid, graph 0.66 to first OffAirMid, 1.15 lw 1 front
}

# Build the plot command from whichever data files exist
cmd = ""
sep = ""
if (HaveAerial) {
    cmd = cmd . sep . sprintf("'%s' using 1:2 with lines lc rgb '#A020F0' lw 1 title '%s'", AerialFile, AerialTitle)
    sep = ", "
}
if (HaveXray) {
    cmd = cmd . sep . sprintf("'%s' using 1:5 axes x1y2 with lines lc rgb '#FF0000' lw 1 title 'NOAA GOES X-ray (0.1-0.8nm)'", XrayFile)
    sep = ", "
}
# Flare markers sit on the X-ray (y2) axis, so need the X-ray axis configured.
# Dotted vertical bars at the flare begin and end times with the maximum
# class labelled above the begin time. Flares whose peak flux (column 6)
# is below FlareMinFlux are skipped by mapping their y value to 1/0
# (gnuplot discards invalid points).
if (!exists("FlareMinFlux")) { FlareMinFlux = 0 }
if (exists("FlareFile") && HaveXray) {
    cmd = cmd . sep . sprintf("'%s' using 1:($6>=FlareMinFlux ? $6/5 : 1/0):(0):($6*5-$6/5) axes x1y2 with vectors nohead dt 3 lw 1 lc rgb '#0000FF' title 'Solar flare start/end with class'", FlareFile)
    sep = ", "
    cmd = cmd . sep . sprintf("'%s' using 7:($6>=FlareMinFlux ? $6/5 : 1/0):(0):($6*5-$6/5) axes x1y2 with vectors nohead dt 3 lw 1 lc rgb '#0000FF' notitle", FlareFile)
    sep = ", "
    cmd = cmd . sep . sprintf("'%s' using 1:($6>=FlareMinFlux ? $6*5 : 1/0):5 axes x1y2 with labels font 'sans,7' textcolor rgb '#0000FF' offset 0,0.6 notitle", FlareFile)
    sep = ", "
}

if (cmd eq "") {
    print "PlotYesterday.gp: no data files supplied - nothing to plot"
    exit
}

# Data credits - NOAA SWPC courtesy credit; sunrise-sunset.org attribution
# is required by that API's terms of use
Credits = ""
if (HaveXray) {
    Credits = "Data: NOAA SWPC"
}
if (exists("SunriseTime") || exists("SunsetTime")) {
    Credits = Credits . (Credits eq "" ? "Data: " : " | ") . "sunrise-sunset.org"
}
if (Credits ne "") {
    set label 99 Credits at screen 0.99, screen 0.012 right font "sans,7" textcolor rgb "#606060" front
}

eval("plot " . cmd)

# Second, date-stamped copy for the archive
if (exists("ArchiveFile")) {
    set output ArchiveFile
    replot
}

set output

# EOF
