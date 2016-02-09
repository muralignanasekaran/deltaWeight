import sys
import argparse
from datetime import datetime

# weight file should guarantee first four columns as
# 1) ValueID (numeric)
# 2) PatientID (numeric)
# 3) Date (yyyy-mm-dd)
# 4) Value (raw weight or other value from EHR)
# and should be ordered by PatientID, Date, Value

class Counter():
    def __init__(self):
        self.count = 0

    def add(self):
        self.count += 1
        if not self.count % 10000:
            print "\r" + str(self.count),

class Nothing():
    def __init__(self):
        pass

    def add(self):
        pass

def deltas(dates, weights, m, tp=None, ts=None):
    n = len(dates)
    if n > 1:
        ans = [None for j in range(n)]
        for i in range(n):
            dist = [(dates[j] - dates[i]).days for j in range(n)]
            myw = [weights[j] - weights[i] for j in range(n)]
            dist.pop(i)
            myw.pop(i)
            temp = sorted(zip(dist, myw), key=lambda x: abs(x[0]))
            dd, dw = map(list, zip(*temp))
            if ts is not None:
                dd = [j for j in dd if abs(j) <= ts]
            nr = len(dd)
            if tp is not None and tp < nr:
                nr = tp
            if nr == 0:
                dd = [m]
                dw = [m]
            else:
                dd = [str(j) for j in dd[0:nr]]
                dw = [str(j) for j in dw[0:nr]]
            if tp is not None:
                while len(dw) < tp:
                    dd.append(m)
                    dw.append(m)
            ans[i] = dw + dd
    else:
        if tp is None:
            tp = 1
        ans = [[m for j in range(tp*2)]]
    return ans

def splitData(string, d):
    line = string.split(d)
    myid = line[1]
    mydate = datetime.strptime(line[2], '%Y-%m-%d').date()
    myweight = float(line[3])
    return [myid, mydate, myweight]

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("datafile", help='delimited file with format ValueID,PatientID,Date,Value,ETC')
    parser.add_argument("outputfile")
    parser.add_argument("-t", "--timepoints", help='number of time points to calculate, defaults to all observations', type=int)
    parser.add_argument("-s", "--span", help='measures time points found within number of days', type=int)
    parser.add_argument("-d", "--delimiter", help='file delimiter, defaults to ","', default=',')
    parser.add_argument("-m", "--missing", help='missing value, defaults to "."', default='.')
    parser.add_argument("--nocount", help='turn counter off', action='store_true')
    parser.add_argument("--wide", help='output in wide format; only available when timepoints is set', action='store_true')
    args = parser.parse_args()
    delim = args.delimiter
    missing = args.missing
    wideformat = args.wide
    infile = open(args.datafile)
    outfile = open(args.outputfile, 'w')
    timepoints = args.timepoints
    timespan = args.span
    if timepoints is None:
        wideformat = False
    elif timepoints < 1:
        print 'timepoints must be 1 or greater'
        sys.exit(1)
    if timespan is not None and timespan < 0:
        print 'span must be 0 or greater'
        sys.exit(1)
    if wideformat:
        dw = ["ValueDiff%s" % (i) for i in range(1, timepoints+1)]
        dt = ["DateDiff%s" % (i) for i in range(1, timepoints+1)]
        header = delim.join([infile.readline().rstrip()] + dw + dt)
    else:
        header = delim.join([infile.readline().rstrip()] + ["ValueDiff", "DateDiff", "measurement"])
    outfile.write(header+"\n")
    if args.nocount:
        cnt = Nothing()
    else:
        cnt = Counter()
    curid = None
    d = []
    w = []
    out = []
    line = infile.readline().rstrip()
    while len(line) > 1:
        (uid, date, weight) = splitData(line, delim)
        if curid is not None and curid != uid:
            ans = deltas(d, w, missing, timepoints, timespan)
            for i in range(len(out)):
                if wideformat:
                    outfile.write(delim.join([out[i]] + ans[i]) + "\n")
                else:
                    nr = len(ans[i])/2
                    for j in range(nr):
                        dw = ans[i][j]
                        dt = ans[i][j+nr]
                        outfile.write(delim.join([out[i]] + [dw, dt, str(j+1)]) + "\n")
            d = [date]
            w = [weight]
            out = [line]
        else:
            d.append(date)
            w.append(weight)
            out.append(line)
        curid = uid
        line = infile.readline().rstrip()
        cnt.add()
    if len(out):
        ans = deltas(d, w, missing, timepoints, timespan)
        for i in range(len(out)):
            if wideformat:
                outfile.write(delim.join([out[i]] + ans[i]) + "\n")
            else:
                nr = len(ans[i])/2
                for j in range(nr):
                    dw = ans[i][j]
                    dt = ans[i][j+nr]
                    outfile.write(delim.join([out[i]] + [dw, dt, str(j+1)]) + "\n")
    infile.close()
    outfile.close()
