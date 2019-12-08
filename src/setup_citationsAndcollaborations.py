""" Setup functions for collaboration networks. These functions are intentionally
    slowed to prevent over-querying. For well-connected authors, beware! It may 
    take a while """

import json, requests, re, time, sys, warnings
from unidecode import unidecode
import pandas as pd
from Bio import Entrez
from itertools import groupby, chain
from bs4 import BeautifulSoup

defaultAgent = {'User-Agent': 'SomeAgent 11.0'}

def entrezSearch(query, doze = 0.25):
    Entrez.email = 'insertemail@gmail.com'
    handle = Entrez.esearch(db = 'pubmed', 
                            sort = 'relevance', 
                            retmax = '1000',
                            retmode = 'xml', 
                            term = query)
    time.sleep(doze)
    results = Entrez.read(handle)
    return results


def fetchEntrezDetails(id_list, doze = 0.25):
    ids = ','.join(id_list)
    Entrez.email = 'insertemail@gmail.com'
    handle = Entrez.efetch(db = 'pubmed',
                           retmode = 'xml',
                           id = ids)
    time.sleep(doze)
    results = Entrez.read(handle)
    return results


def fetchAuthor(firstName, lastName, checkCitations = False, startYear = 2000,
    maxAnnualPapers = 30, addArXiv = True):
    """ Fetch Entrez results for an author, wiht a constructed query of 
        '{lastName}, {firstName}[Author]'. 
    
        Args:
            checkCitations: Boolean - Checking citations with Google Scholar
                is set to False, since GS quickly blocks programmatic queries. 
            startYear: Int - Starting year of publication
            maxAnnualPapers: Int -  number of permissible papers, per year. Some names
                are common, and yield many false positives. However, this limit only applies
                to non-last authors, as last authors (especially reputable ones wih big labs) 
                may have their names on many papers. Some of the 'extreme' collaborators
                probably should be neglected anyways if they're part of some core or
                service group (i.e. less likely to have a focused research topic). 
                This threshold could be adjusted to how much of a generalist is desired. 
                Its usually not the case that a specialized researcher, even with a big lab,
                could effectively collaborate so extensively as to publish > 2 or 3 
                papers per month. """

    firstName, lastName = unidecode(firstName), unidecode(lastName)
    properName = lastName + ', ' + firstName
    searchTerm = properName + '[Author]'
    results = entrezSearch(searchTerm)
    id_list = results['IdList']
    papers = fetchEntrezDetails(id_list)

    authorDict = dict()
    authorDict['First author'] = 0
    authorDict['Last author'] = 0
    authorDict['Coauthors'] = dict()
    authorDict['Papers'] = dict()
    authorDict['Publication year counter'] = dict()

    for _, paper in enumerate(papers['PubmedArticle']):
        pmid = str(paper['MedlineCitation']['PMID'])
        pmid = re.split(r'StringElement\(\'', pmid)
        pmid = re.sub(r'\'.*', '', pmid[0])
        allAuthors = []
        try:
            for author in paper['MedlineCitation']['Article']['AuthorList']:
                try:
                    coauthorSur, coauthorFore = author['LastName'], author['ForeName']
                    coauthorFore = re.sub(r'\ [A-Z]$', '', coauthorFore)
                    coauthorFore = re.sub(r'\-', ' ', coauthorFore)
                    coauthorFore, coauthorSur = unidecode(coauthorFore), unidecode(coauthorSur)
                    properCoName = coauthorSur + ', ' + coauthorFore
                    allAuthors.append(properCoName)
                except KeyError:
                    continue

            try:
                pubYear = int(paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['Year']) 
            except KeyError:
                pubYear = startYear - 1 #Skip paper   
            
            if len([x for x in allAuthors if x == properName]) > 0 and pubYear >= startYear:
                if pubYear not in authorDict['Publication year counter']:
                    authorDict['Publication year counter'][pubYear] = 0
                authorDict['Papers'][pmid] = dict()
                keyWords = str(paper['MedlineCitation']['KeywordList'])
                keySplit = re.split(r'StringElement\(\'', keyWords)
                keyList = [re.sub(r'\'.*', '', x) for x in keySplit]
                keyWords = [x for x in keyList if not 'ListElement' in x]
                authorDict['Papers'][pmid]['Keywords'] = keyWords
                authorDict['Papers'][pmid]['Year'] = paper['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate']['Year']    
                authorDict['Papers'][pmid]['Title'] = paper['MedlineCitation']['Article']['ArticleTitle']
                authorDict['Papers'][pmid]['Authors'] = allAuthors 

                if properName == allAuthors[0] and len(allAuthors) == 1:
                    authorDict['First author'] += 1
                    authorDict['Last author'] += 1
                elif properName == allAuthors[0] and len(allAuthors) > 1:
                    authorDict['First author'] += 1
                    authorDict['Publication year counter'][pubYear] += 1
                elif properName == allAuthors[-1] and len(allAuthors) > 1:
                    authorDict['Last author'] += 1
                else:
                    authorDict['Publication year counter'][pubYear] += 1

                if checkCitations == True:
                    try:
                        authorDict['Papers'][pmid]['Citations'] = extractCitationsGScholar(paper)
                    except:
                        continue
                else:
                    authorDict['Papers'][pmid]['Citations'] = 'n/a'
                
                for author in allAuthors:
                    if author != properName:
                        if author not in authorDict['Coauthors']:
                            authorDict['Coauthors'][author] = set()
                            authorDict['Coauthors'][author].add(pmid)
                        else:
                            authorDict['Coauthors'][author].add(pmid)        
        except KeyError:
            continue
        
    for coauthor in authorDict['Coauthors']:
        authorDict['Coauthors'][coauthor] = list(authorDict['Coauthors'][coauthor])
    
    if addArXiv == True:
        authorDict = arXivSearch(firstName, lastName, authorDict = authorDict)
    
    if any([x for x in authorDict['Publication year counter'].values() if x > maxAnnualPapers]):
        warnings.warn('Maximum annual number of papers exceeded for {0}, returning None'.format(properName), Warning)
        authorDict = None 
    
    return authorDict 


def arXivSearch(firstName, lastName, authorDict = None):
    """ Create, or update, an author dictionary with an ArXiv search. If an authorDict
        is specified, it must come from fetchAuthor() (the formatting must match).
        Although a publication year counter won't be used for ArXiv. This script is
        some ugly text parsing of a requests Beautiful object. Not elegant
        but seems to work fine. Maxes out at 200? I think """

    if authorDict is None:
        authorDict = dict()
        authorDict['First author'] = 0
        authorDict['Last author'] = 0
        authorDict['Coauthors'] = dict()
        authorDict['Papers'] = dict()
        authorDict['Publication year counter'] = dict()

    firstName, lastName = unidecode(firstName), unidecode(lastName)
    properName = lastName + ', ' + firstName
    url = 'https://arxiv.org/search/advanced?advanced=1&terms-0-operator=AND&terms-0-term={0}+{1}&terms-0-field=author&classification-physics_archives=all&classification-include_cross_list=include&date-filter_by=all_dates&date-year=&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order=-announced_date_first'.format(firstName, lastName)
    data = requests.get(url)
    soup = BeautifulSoup(data.text, features = 'html.parser')
    #papers = dict()

    for result in soup.find_all('li', class_ = ['arxiv-result']):
        paperID = re.findall('href\=\"(.*)\"\>arXiv', str(result))
        paperID = re.sub(r'https\:\/\/arxiv.org\/abs\/', 'arXiv:', paperID[0]) 
        authorDict['Papers'][paperID] = dict()
        resultSoup = BeautifulSoup(result.text, features = 'html.parser')
        lineBreaks = re.sub('\n', '', str(resultSoup))
        authors = re.findall(r'Authors\:(.*)Abstract\:', lineBreaks)
        authors = re.split(r'\, ', authors[0])
        authors = [re.sub(r'  ', '', x) for x in authors]
        authors = [re.sub(' [A-z]\.? ', ' ', x) for x in authors]
        properAuthors = [re.sub('^(.*) (.*)$', '\\2, \\1', x) for x in authors]
        title = re.findall('              (.*)          Authors\:', str(lineBreaks))
        keyWords = re.findall('data\-tooltip\=\"(.*)\"', str(result))

        authorDict['Papers'][paperID]['Title'] = title[0]
        authorDict['Papers'][paperID]['Authors'] = properAuthors
        authorDict['Papers'][paperID]['Keywords'] = keyWords
        authorDict['Papers'][paperID]['Citations'] = 'n/a'
        pubYear = int(re.findall('Submitted\<\/span\>.*(\d\d\d\d)', str(result))[0])
        authorDict['Papers'][paperID]['Year'] = pubYear
        if pubYear not in authorDict['Publication year counter']:
            authorDict['Publication year counter'][pubYear] = 0

        if properName == properAuthors[0] and len(properAuthors) == 1:
            authorDict['First author'] += 1
            authorDict['Last author'] += 1
        elif properName == properAuthors[0] and len(properAuthors) > 1:
            authorDict['First author'] += 1
            authorDict['Publication year counter'][pubYear] += 1
        elif properName == properAuthors[-1] and len(properAuthors) > 1:
            authorDict['Last author'] += 1
        else:
            authorDict['Publication year counter'][pubYear] += 1

        for author in properAuthors:
            if author != properName:
                if author not in authorDict['Coauthors']:
                    authorDict['Coauthors'][author] = set()
                    authorDict['Coauthors'][author].add(paperID)
                else:
                    authorDict['Coauthors'][author] = set( authorDict['Coauthors'][author])
                    authorDict['Coauthors'][author].add(paperID) 

        for coauthor in authorDict['Coauthors']:
            authorDict['Coauthors'][coauthor] = list(authorDict['Coauthors'][coauthor])

    return authorDict


def oneDegreeAuthors(authorDict, firstName, lastName, checkCitations = False, 
    maxAnnualPapers = 30):
    """ Build a comprehensive coauthor dictionary which orginates from a primary
        author. Assume structure from the result produced with fetchAuthor """
    
    firstName, lastName = unidecode(firstName), unidecode(lastName)
    properName = lastName + ', ' + firstName
    fullColab = dict()
    fullColab[properName] = authorDict 

    for coauthor in list(authorDict['Coauthors'].keys()):
        try:
            coauthorSur = re.findall(r'^(.*)\,', coauthor)[0]
            coauthorFore = re.findall(r'\, (.*)', coauthor)[0]
            coauthorFore = re.sub(r'\ [A-Z]$', '', coauthorFore)
            coauthorFore, coauthorSur = unidecode(coauthorFore), unidecode(coauthorSur)
            properCoName = coauthorSur + ', ' + coauthorFore
            coauthorDict = fetchAuthor(firstName = coauthorFore, lastName = coauthorSur, 
                checkCitations = checkCitations, maxAnnualPapers = maxAnnualPapers)
            if coauthorDict is not None:
                fullColab[properCoName] = coauthorDict
        except Exception as err:
            errStr = str(err)
            #print(errStr)
            continue 

    return fullColab


def extractCitationsGScholar(entrezArticle, doze = 1.):
    """ Extract the number of citations from an eztrez.Bio search, with the DOI
        plugged into Google Scholar. Takes the first article (though a DOI should
        only specify one) and extracts the 'Cited by x', if citations exist. If
        cited by doesn't exist, return 0 (we have faith that Google Scholar keeps
        close tabs on citations, although this may not always be true). The 
        url for Google Scholar search is hard-coded in this function, and may
        not be future-proof. Must come from a paper['PubmedArticle'] value in
        Entrez. """

    articleIDs = entrezArticle['PubmedData']['ArticleIdList']
    articleIDsSplit = re.split(r'StringElement\(\'', str(articleIDs))
    doi = [x for x in articleIDsSplit if "'IdType': 'doi'" in x][0]
    doi1 = re.findall(r'^(.*)\/', doi)[0]
    doi2 = re.findall(r'^.*\/(.*)\'\, ', doi)[0]
    url = 'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C22&q=http%3A%2F%2Fdx.doi.org%2F{0}%2F{1}'.format(doi1, doi2)
    urlGet = requests.get(url, headers = defaultAgent)
    print(urlGet.text)
    cites = re.findall(r'Cited by (\d+)', str(urlGet.text))
    if len(cites) == 1:
        citesNum = int(cites[0])
    else:
        citesNum = 0
    time.sleep(doze)

    return citesNum


def buildCoauthorNodesEdges(authorColabDict, majorKeywords = ['bioinformatics',
    'network', 'cancer', 'aging', 'circadian', 'omics', 'neuro', 'computer',
    'genetics', 'microbiome', 'computational', 'cardio', 'social', 'epidemic',
    'sleep', 'pharamcology', 'mitochondria', 'metabolism', 'inflammation',
    'systems', 'chrono', 'diabetes', 'immunology', 'diet', 'bacteria', 'math', 
    'physics', 'graph', 'complex', 'machine learning', 'artificial intelligence']):
    """ Build a node and edge list of coauthors from the output of oneDegreeAuthors.
        Nodes are authors, quantiative values per author include number of first
        and last author'ed papers. Edge weights defined by the number of shared
        authorships and the number of citations.
        
        Nodes: Author | Total Papers | First Authors | Last Authors | Citations | Major keyword | id
        Edges: Author1 | Author2 | nPapers | nCitations | id1 | id2

        Most abundant keyword, and if a keyword is found from the manual set of 
        words in majorKeywords (unsure how to best group similar keywords, 
        large state space, need embeddings or something fancy).
    """
    nodeDF = []
    for author in authorColabDict:
        totalPapers = len(authorColabDict[author]['Papers'])
        fAuthors = authorColabDict[author]['First author']
        lAuthors = authorColabDict[author]['Last author']
            
        citationList = []
        keyWordList = []
        for paper in authorColabDict[author]['Papers']:
            keywords = authorColabDict[author]['Papers'][paper]['Keywords']
            if 'Citations' in authorColabDict[author]['Papers'][paper]:
                citationList.append(authorColabDict[author]['Papers'][paper]['Citations'])
            if len(keywords) > 0:
                keywords = [x.lower() for x in keywords]
                keyWordList += keywords
        citations = sum([x for x in citationList if x != 'n/a'])

        keyWordList = [x for x in keyWordList if x != '[]']
        if len(keyWordList) > 0:
            sortKeywordsDict = [dict({i : len(list(c))}) for i,c in groupby(sorted(keyWordList))]
            keyWordList = [re.sub(r'\ .*$', '', i).lower() for i,c in groupby(sorted(keyWordList))]
            majorWord = ''
            for word in keyWordList:
                for ref in majorKeywords:
                    if re.findall('{0}'.format(ref), word): #Pulling the first most prevalent word in the majorKeywords
                        majorWord = ref 
                        break
            maxCount = max([list(x.values())[0] for x in sortKeywordsDict])
            maxKey = [list(x.keys())[0] for x in sortKeywordsDict if list(x.values())[0] == maxCount][0]
        else:
            maxKey = ''

        authorSur = re.findall(r'^(.*)\,', author)[0]
        authorFore = re.findall(r'\, (.*)', author)[0]
        fullName = authorFore + ' ' + authorSur   
        nodeDF.append([fullName, totalPapers, fAuthors, lAuthors, citations, maxKey, majorWord])
    
    nodeDF = pd.DataFrame(nodeDF)
    nodeDF.columns = ['Author', 'Total papers', 'First authors', 'Last authors', 
        'Citations', 'Max keyword', 'Major keyword']
    nodeDF['id'] = list(range(len(nodeDF)))

    authorIDs = dict(zip(nodeDF['Author'], nodeDF['id']))
    edgeDF = []
    colabsSet = set()
    for author1 in authorColabDict:
        for author2 in authorColabDict[author1]['Coauthors']:
            if author2 in authorColabDict:
                colabStr = ''.join(sorted([author1, author2]))
                if colabStr not in colabsSet:
                    nPapers = len(authorColabDict[author1]['Coauthors'][author2])
                    coCitations = []
                    for paper in authorColabDict[author1]['Coauthors'][author2]:
                        if 'Citations' in authorColabDict[author1]['Papers'][paper]:
                            coCitations.append(authorColabDict[author1]['Papers'][paper]['Citations'])
                    nCitations = sum([x for x in coCitations if x != 'n/a'])

                    authorSur1 = re.findall(r'^(.*)\,', author1)[0]
                    authorFore1 = re.findall(r'\, (.*)', author1)[0]
                    fullName1 = authorFore1 + ' ' + authorSur1
                    authorSur2 = re.findall(r'^(.*)\,', author2)[0]
                    authorFore2 = re.findall(r'\, (.*)', author2)[0]
                    fullName2 = authorFore2 + ' ' + authorSur2
                    
                    edgeDF.append([fullName1, fullName2, nPapers, nCitations])
                    colabsSet.add(colabStr)
        
    edgeDF = pd.DataFrame(edgeDF)
    edgeDF.columns = ['Author1', 'Author2', 'nPapers', 'nCitations']
    edgeDF['id1'] = [authorIDs[x] for x in edgeDF['Author1']]
    edgeDF['id2'] = [authorIDs[x] for x in edgeDF['Author2']]
    
    return nodeDF, edgeDF