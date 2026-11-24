# PlotSIDEvent.gp - plot of a single candidate SID event: VLF receiver
# output around the event with NOAA GOES primary X-ray flux, solar flare
# markers and the estimated SID start/peak/end marked.
#
# Driven by ExtractSIDEvents.py, which passes variables with gnuplot -e:
#   required : OutputFile, GraphTitle, GraphSubtitle, StartTime, EndTime
#              AerialFile, AerialTitle       (the day's VLF data + legend)
#              EventStart, EventPeak         ("yyyy-mm-dd hh:mm:ss")
#   optional : EventEnd                      (absent when the end could
#                                             not be measured)
#              XrayFile                      (the day's X-ray data)
#              FlareFile                     (the day's flare events)
#              ArchiveFile                   (second, archived output)
# Optional variables are simply not defined when the data is unavailable.
#
# Data formats (comma separated):
#   Aerial : yyyy-mm-dd hh:mm:ss,voltage
#   X-ray  : yyyy-mm-dd hh:mm:ss,satellite,short_flux,0.05-0.4nm,long_flux,0.1-0.8nm
#   Flares : begin,satellite,begin_class,max,max_class,max_flux,end,end_class

reset

set terminal pngcairo enhanced font "DejaVuSansCondensed,10" rounded size 720,540
set output OutputFile

set datafile separator ","
set xdata time
set timefmt "%Y-%m-%d %H:%M:%S"
set format x "%H:%M" timedate

set grid xtics ytics

set xlabel "Time (UTC)"
set xrange [StartTime:EndTime]
set xtics border out scale 1,0.5 nomirror 900
set mxtics 3

set key outside above right
set key Right samplen 4 nobox
set key title GraphTitle."\n".GraphSubtitle."\n"

set ylabel "UKRAA VLF receiver output (V)" textcolor rgb "#A020F0"
set yrange [0:5]
set format y "%.1f"
set ytics border out scale 1,0.5 nomirror textcolor rgb "#A020F0"
set mytics 2

HaveXray = exists("XrayFile")
if (HaveXray) {
    set y2label "NOAA GOES primary X-ray Flux (W/m^2)" textcolor rgb "#FF0000"
    set y2range [1e-7:1e-2]
    set logscale y2 10
    set format y2 "10^{%T}"
    set y2tics border out scale 1,0.5 nomirror textcolor rgb "#FF0000"
}

# Estimated SID start / peak / end markers
set arrow 1 from first EventStart, graph 0 to first EventStart, graph 1 nohead lc rgb "#0000FF" lw 1 dt 2
set label 1 "start ".substr(EventStart, 12, 16) at first EventStart, graph 0.08 rotate by 90 offset char 1,0 font "sans,8" textcolor rgb "#0000FF" front
set arrow 2 from first EventPeak, graph 0 to first EventPeak, graph 1 nohead lc rgb "#008000" lw 1 dt 2
set label 2 "peak ".substr(EventPeak, 12, 16) at first EventPeak, graph 0.08 rotate by 90 offset char 1,0 font "sans,8" textcolor rgb "#008000" front
if (exists("EventEnd")) {
    set arrow 3 from first EventEnd, graph 0 to first EventEnd, graph 1 nohead lc rgb "#0000FF" lw 1 dt 2
    set label 3 "end ".substr(EventEnd, 12, 16) at first EventEnd, graph 0.08 rotate by 90 offset char 1,0 font "sans,8" textcolor rgb "#0000FF" front
} else {
    set label 3 "end not measured" at first EndTime, graph 0.08 rotate by 90 offset char 1,0 font "sans,8" textcolor rgb "#0000FF" front
}

# Build the plot command from whichever data files exist
cmd = sprintf("'%s' using 1:2 with lines lc rgb '#A020F0' lw 1 title '%s'", AerialFile, AerialTitle)
if (HaveXray) {
    cmd = cmd . sprintf(", '%s' using 1:5 axes x1y2 with lines lc rgb '#FF0000' lw 1 title 'NOAA GOES X-ray (0.1-0.8nm)'", XrayFile)
}
# Flare markers sit on the X-ray (y2) axis, so need the X-ray axis configured.
if (exists("FlareFile") && HaveXray) {
    cmd = cmd . sprintf(", '%s' using 1:($6/5):(0):($6*5-$6/5) axes x1y2 with vectors nohead dt 3 lw 1 lc rgb '#FF8C00' title 'Solar flare start/end with class'", FlareFile)
    cmd = cmd . sprintf(", '%s' using 7:($6/5):(0):($6*5-$6/5) axes x1y2 with vectors nohead dt 3 lw 1 lc rgb '#FF8C00' notitle", FlareFile)
    cmd = cmd . sprintf(", '%s' using 1:($6*5):5 axes x1y2 with labels font 'sans,7' textcolor rgb '#FF8C00' offset 0,0.6 notitle", FlareFile)
}

if (HaveXray) {
    set label 99 "Data: NOAA SWPC" at screen 0.99, screen 0.012 right font "sans,7" textcolor rgb "#606060" front
}

eval("plot " . cmd)

# Second, archived copy
if (exists("ArchiveFile")) {
    set output ArchiveFile
    replot
}

set output

# EOF
