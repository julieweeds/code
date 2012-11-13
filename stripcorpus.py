'''
Created on Nov 13, 2012
combination of strip and makecorpus
@author: juliewe
'''
import re #for regular expressions
from sys import argv #for command line args
import glob #for collecting filenames
from operator import itemgetter
import os

doccount = 0
inbody = False
topic = ""
title = ""
output = ""
split = ""
mybuffer = "\n"
parentdir = "./"
#inputfilename = '../smalltest'



option = "top"  #top = output most frequent documents (number in parameter)
parameter = 3
topics = {} # empty hash dictionary to store dictionary counts


#compile regular expressions to match
pattFirstline = re.compile('^<REUTERS.*')
pattLastline = re.compile('^</REUTERS.*')
pattTopicline = re.compile('^<TOPICS><D>(.*)</D></TOPICS>')
pattTitleline = re.compile('^<TITLE>(.*)</TITLE')
pattStartBody = re.compile('.*<BODY>(.*)')
pattEndBody = re.compile('(.*)</BODY>')
pattSGML = re.compile('(.*)<.*|^&#')
pattTOPICS = re.compile('.*TOPICS=\"YES\"')
pattLEWIS = re.compile('.*LEWISSPLIT=\"(.*)\" CGISPLIT')
pattLIT = re.compile('(.*)&lt;(.*)>(.*)')

pattTOPIC = re.compile('.*/(.*)')



def removeliteral(text):
    matchobj = pattLIT.match(text)
    if matchobj:
        left = matchobj.group(1)
#      mid = matchobj.group(2) #actually don't want tag at all
        right = matchobj.group(3)
        text = removeliteral(left) + removeliteral(right)        
    return text   

def fileoutput(text, output):
    matchobj = pattSGML.match(text)
    if matchobj:
        print "Found SGML in body"
        text = matchobj.group(1)
    if text:
        text = removeliteral(text)
        output.write(text+'\n')
        
def processtopic(topic):
    matchobj = pattSGML.match(topic)
    if matchobj:
        #SGML in line indicates multiple topics so discard
        print "Multiple topics so discard"
        topic = ""
    return topic
        
def checkdir(path):
    if os.access(path, os.F_OK):
        print"Directory already exists", path
    else:
        os.mkdir(path)
    return


def process(line, doccount, inbody, topic, title, split, output, mybuffer):
    matchobj = pattFirstline.match(line)
    if matchobj:
        doccount = doccount + 1
        inbody = False
        topic = ""
        title = ""
        mybuffer = ""
        print "Found start of file ", doccount
    #   print line
        if (pattTOPICS.match(line)):
            print "TOPICS = YES"
            lewisobj=pattLEWIS.match(line)
            if lewisobj:
                print lewisobj.group(1)
                if (lewisobj.group(1)=='TRAIN'):
                    split = 'train'
                else:
                    if (lewisobj.group(1) =='TEST'):
                        split = 'test'
                    else:
                        split = 'unused' #unused
        else:
            print "TOPICS = NO"
            split = "" # unused
    matchobj = pattLastline.match(line)
    if matchobj:
        print "Found end of file ", doccount 
        inbody = False
    matchobj = pattTopicline.match(line)
    if matchobj:
        topic = processtopic(matchobj.group(1))
        print "Topic", topic
        inbody = False
    matchobj = pattTitleline.match(line)
    if matchobj:
        title = matchobj.group(1)
        print "Title", title 
        inbody = False
    matchobj = pattStartBody.match(line)
    if matchobj:       
        print "Found start of body"
        text = matchobj.group(1)
        if topic:
            #open file to write to
            outputpath = parentdir+split+'/'+topic+'/'
            checkdir(outputpath)
            outputfilename = outputpath+topic+'_'+ str(doccount)
            output = open(outputfilename, 'w')
            #output.write(topic+'\n')
            fileoutput(title,output)
            if topic in topics: #update count of topic
                count = topics[topic] + 1
            else:
                count = 1
            topics[topic]=count
            inbody = True
        else:
            print "No topic so no output"    
        
    else:
        text = line
    matchobj = pattEndBody.match(line)
    if matchobj:
        text = matchobj.group(1)
        print "End of body found"
        if inbody :
    #        fileoutput(text, output)  #print last line
            inbody = False
            topic = ""
            title = ""
            split = ""
            mybuffer = ""        
            output.close()
    
    if inbody:
        fileoutput(mybuffer, output)
        mybuffer=text # use mybuffer to store line and discard last line
    return (doccount, inbody, topic, title, split, output, mybuffer)


if len(argv) > 1:parentdir = argv[1] #pass directory with inputfiles via command line
print parentdir
inputdir=parentdir+'sgmdata/*'
if len(argv) == 3: parameter = int(argv[2])
#if len(argv) == 3:outputdir = argv[2] #outputdir from command line



filelist = glob.glob(inputdir)
print filelist
for myfile in filelist:
    f = open(myfile, 'r')
    print "Processing ", myfile
    for line in f:
        (doccount,inbody, topic, title, split, output, mybuffer) = process(line.rstrip(), doccount, inbody, topic, title, split, output, mybuffer)
    f.close

#print topics
topictuples = sorted(topics.items(),key=itemgetter(1),reverse=True)
topiclist =[]
if parameter>len(topictuples):
    parameter=len(topictuples)
    print "Resetting parameter to max possible value", parameter
    #print parameter
while len(topiclist)<parameter:#get all topics
    #print len(topiclist)
    topiclist.append(topictuples[len(topiclist)][0])
print "Top ", parameter, "topics are", topiclist    


outputfiles = [parentdir+"r"+str(parameter)+"_training", parentdir+"r"+str(parameter)+"_testing"]
inputdirs = [parentdir+'train/',parentdir+'test/']
    
for i in [0,1]:#2 iterations - 1 for training and 1 for testing
    output = open(outputfiles[i],'w')
    filelist = glob.glob(inputdirs[i]+'*')
    #print filelist
    
    for f in filelist:
        #print f
        matchobj = pattTOPIC.match(f)
        if matchobj:
            t = matchobj.group(1)
            #print t
            if t in topiclist:
                output.write(inputdirs[i]+t+'\n')
        