import sys
import heapq

f = open(sys.argv[1])
lines = f.readlines()
meta = [l for l in lines if l[0] == '>']
reads = [(len(l), l) for l in lines if l[0] != '>']
combined = zip(meta, reads)
combined.sort(lambda x,y: x[1][0] - y[1][0])
combined.reverse()

out = open(sys.argv[3], 'w')
for data in combined[0:int(sys.argv[2])]:
    out.write(data[0])
    out.write(data[1][1])

  
