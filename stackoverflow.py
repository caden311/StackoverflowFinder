#!/usr/bin/env python
import StringIO
import json
import string
import simplejson
import gzip
import sys
import re
import urllib, urllib2
import nltk

def main():
    Q=sys.argv[1]
    Q=Q.rstrip();
    OriginalQuestion=Q

    #find google top result URL and google Title/Body
    googleUrl=returnGoogleUrl(Q)
    googleTitle,googleBody=findGoogleTitleBody(googleUrl)


    #return matches found as well as original string without matches
    matchValue,Q=FindMatches(Q)
    matchValue=urllib.quote(matchValue)


    #find NN and other tokens
    qVal=FindTokens(Q)
    Q=urllib.quote(qVal);

    possibleQsWithoutQuotes=programmingDictionary(qVal)
    possibleQs=programmingDictionary(Q)

    val=[]

    #with dictionary

    for i in range(len(possibleQs)):
    #Get initial query items / then rank them based on views
        initialVal=CallQuery(possibleQs[i],matchValue,"0");
        val.append(rankItemsByViews(initialVal,possibleQs[i],matchValue))
    '''
    #without dictionary
    initialVal=CallQuery(Q,matchValue,"0");
    val=rankItemsByViews(initialVal,Q,matchValue)
    '''


    top1=0
    top2=0
    topItem="";
    title=""

    body=""

    #with dictionary

    for i in range(len(val)):
        val[i]['items'].sort(key=sortByViews,reverse=False)

    for j in range(len(val)):
        rank=1
        for i in range(len(val[j]['items'])):
            currScore=ScoreFunction(val[j]['items'][i],OriginalQuestion,qVal,rank);
            #print val[j]['items'][i]['link'];
            #print "score: "+str(currScore)
            if(currScore>top1):
                top1=currScore;
                topItem=val[j]['items'][i]
            rank+=1
    if(topItem!=""):
        title=topItem['title']
        print title
        print topItem['link']
        for ans in range(len(topItem['answers'])):
            if (topItem['answers'][ans]['is_accepted'] == 1):
                body=topItem['answers'][ans]['body']
                
    print "Google answer:"
    print googleTitle;
    print googleUrl;
    '''

    #without dictionary

    val['items'].sort(key=sortByViews,reverse=False)
    rank=1
    for i in range(len(val['items'])):
        currScore=ScoreFunction(val['items'][i],OriginalQuestion,qVal,rank);
        #print val['items'][i]['link'];
        if(currScore>top1):
            top1=currScore;
            topItem=val['items'][i]
        rank+=1
    if(topItem!=""):
        title=topItem['title']
        for ans in range(len(topItem['answers'])):
            if (topItem['answers'][ans]['is_accepted'] == 1):
                body=topItem['answers'][ans]['body']

    '''
   
   
def programmingDictionary(Q):
    possibleQs=[]
    possibleQs.append(Q);
    temp=Q
    if(re.match('.*item.*',temp)):
        temp=temp.replace("item","element",1)
        possibleQs.append(temp);
        temp=Q
    if(re.match('.*element.*',temp)):
        temp=temp.replace("element","item",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*create.*',temp)):
        temp=temp.replace("create","initialize",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*initialize.*',temp)):
        temp=temp.replace("initialize","create",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*size.*',temp)):
        temp=temp.replace("size","length",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*length.*',temp)):
        temp=temp.replace("length","size",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*combine.*',temp)):
        temp=temp.replace("combine","concatenate",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*int.*',temp)):
        temp=temp.replace("int","integer",1);
        possibleQs.append(temp)
        temp=Q
    if(re.match('.*integer.*',temp)):
        temp=temp.replace("integer","int",1);
        possibleQs.append(temp)
        temp=Q

    return possibleQs
   
def rankItemsByViews(val,Q,matchValue):
    high=0
    stop=True
    highList=[];
    while(stop):
        for items in range(len(val['items'])):
            high=val['items'][items]['view_count']
            highList.append(high)
        if(len(highList)>15):
            highList.sort();
            val=CallQuery(Q,matchValue,str(highList[len(highList)-5]));
            highList=[]; 
        elif(len(highList)<=15):
            stop=False 

    return val;
    
def LengthOfAnswer(json):
    for i in range(len(json['answers'])):
        if (json['answers'][i]['is_accepted'] == 1):
            bodyText=json['answers'][i]['body']
            if(len(bodyText)<40):
                return 2;
    return 0;    
    
def ScoreFunction(json,OriginalQuestion,Q,currRank):
    score=0
    score+=currRank
    score+=itemsInTitle(json['title'].split(),Q.split())    
    score+=containsCode(json);
    score+=LengthOfAnswer(json)
    return score

def containsCode(json):
    for i in range(len(json['answers'])):
        if (json['answers'][i]['is_accepted'] == 1):
            bodyText=json['answers'][i]['body']
            if("<code>" in bodyText):
                return 4;
    return 0


def itemsInTitle(titleArr,qArr):
    score=0 
    index=0
    fixedArr=[]
    for word in range(len(titleArr)):
        val=(titleArr[word]).encode('utf-8')
        val2=val.translate(None,string.punctuation);
        fixedArr.append(val2.lower());

    for i in range(len(fixedArr)):
        if(index<len(qArr)):
            if(fixedArr[i]==qArr[index]):
                index+=1

    if(index==len(qArr)):
        score+=5 
    return score


def sortByViews(json):
    try:
        return int(json['view_count'])
    except:
        return 0

def FindTokens(Q):
    tokens=nltk.word_tokenize(Q)
    tagged=nltk.pos_tag(tokens)
    qVal="";
    for i in range(len(tagged)):
        if(re.match('\d+',tagged[i][0])):
            qVal+=" "+tagged[i][0];
        if(tagged[i][1] == "NN" or tagged[i][1]=="JJ" or tagged[i][1]=="NNS" or tagged[i][1]=="NNP" or tagged[i][1]=="VB" or tagged[i][1]=="RP" or tagged[i][1] =="VBD" or tagged[i][1]=="VBG"):
            qVal+=" "+tagged[i][0];
    return qVal


def FindMatches(Q):
    matcher=re.match( r'(.*)(c\+\+|html|css|php|perl|python|c\#|mysql|swift|javascript|java|lua|\.net)(.*)',Q,re.I)
    matchValue=" "
    matcher2=re.findall(r'(graph|iteration|loops|\sc\s|arrayList|stack|hashtable|data-structure|hash|list|dictionary|nlp|nltk)',Q,re.I)
    if matcher:
        if matcher.group(2) is not None:
            matchValue=re.escape(matcher.group(2))
            Q=re.sub(matchValue,"",Q,re.I);
    if matcher2:
        if matcher2 is not None:
           for matches in matcher2:
               matchValue=matchValue+";"+matches
    if(re.match('.*sort.*',Q)):
        matchValue=matchValue+";sorting";
    if(re.match('.*array.*',Q)):
        matchValue=matchValue+";arrays";
    if(re.match('.*\sswitch\s.*',Q)):
        matchValue=matchValue+";switch-statement";
    if(re.match('.*visiual basic.*',Q)):
        matchValue=matchValue+";vb.net";
    if(re.match('.*float.*',Q)):
        matchValue=matchValue+";floating-point";

    return matchValue,Q

    

def CallQuery(Q,matchValue,viewCount):
    myRequest='https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity&accepted=True&views='+viewCount+'&tagged='+matchValue+'&q='+Q+'&site=stackoverflow&filter=!OfZM.T3md)apQzbDubBc67ZSWQFcv-.kpfm1VG*U)hy'

    #print "my r"+myRequest;

    request=urllib2.Request(myRequest)
    request.add_header('Accept-encoding','gzip')
    response=urllib2.urlopen(request)

    if( response.info().get('Content-Encoding')=='gzip'):
        buf=StringIO.StringIO(response.read())
        f=gzip.GzipFile(fileobj=buf)
        data=f.read()
        return json.loads(data)

def returnGoogleUrl(q):
    query=urllib.urlencode({'q' :'%s site:stackoverflow.com'%(q)});

    url='http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s'\
    %(query)

    search_results=urllib.urlopen(url);

    json=simplejson.loads(search_results.read())
    results=json['responseData']['results']

    return str(results[0]['url'])

def findGoogleTitleBody(googleUrl):
    googleMatch=re.search(r'\d+\/(.*)', googleUrl, re.I)
    googleBody=""
    googleTitle=""
    if(googleMatch):
        if(googleMatch.group(1) is not None):
            theTitle=googleMatch.group(1)
  #          title=re.sub(r'sharp','#',theTitle);
            googleResult=CallUrlQuery(theTitle)
            if(googleResult['items']):
                googleTitle=googleResult['items'][0]['title']
                if('answers' in googleResult['items'][0]):
                    for ans in range(len(googleResult['items'][0]['answers'])):
                        if (googleResult['items'][0]['answers'][ans]['is_accepted'] == 1):
                            googleBody=googleResult['items'][0]['answers'][ans]['body']

    return googleTitle,googleBody
     
def CallUrlQuery(title):
    myRequest='https://api.stackexchange.com/2.2/search/advanced?order=desc&sort=activity&title='+title+'&site=stackoverflow&filter=!OfZM.T3md)apQzbDubBc67ZSWQFcv-.kpfm1VG*U)hy'

    #print "my r"+myRequest;

    request=urllib2.Request(myRequest)
    request.add_header('Accept-encoding','gzip')
    response=urllib2.urlopen(request)

    if( response.info().get('Content-Encoding')=='gzip'):
        buf=StringIO.StringIO(response.read())
        f=gzip.GzipFile(fileobj=buf)
        data=f.read()
        return json.loads(data)


if __name__=='__main__':
    main()

