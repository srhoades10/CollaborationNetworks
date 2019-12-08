""" Query pubmed and Arxiv to generate citation/collaboration networks.

    Examples herein include Albert-Laszlo Barabasi, my (much sparser) 
    network, and former Nobel Prize winners Randy Schekman and James Rothman.
    
    Default parameters are to limit the number of citations, and keep to within
    the past 5 years. First papers are extracted, followed by a search for
    coauthors. A network is then built from all authors (nodes), and their
    coauthorships (links).
    
    Author: Seth Rhoades """

import json, requests, re, time, sys, os
sys.path.append('./src')
import setup_citationsAndcollaborations as util
import pandas as pd
defaultAgent = {'User-Agent': 'SomeAgent 11.0'}

checkCitations = False
overwrite = False
resultDir = 'collaborationResults'

firstNames = ['Albert Laszlo', 'Seth', 'Schekman', 'Rothman']
lastNames = ['Barabasi', 'Rhoades', 'Randy', 'James']

for firstName, lastName in zip(firstNames, lastNames):
    try:
        fileFirstName = re.sub(r'\ ', '', firstName)
        fileLastName = re.sub(r'\ ', '', lastName)

        if ('{0}_{1}_Papers.json'.format(fileFirstName, fileLastName) not in os.listdir(resultDir)
            or overwrite == True):
            
            authorDict = util.fetchAuthor(firstName = firstName, lastName = lastName, 
                checkCitations = checkCitations, maxAnnualPapers = 36)
            with open('{0}/{1}_{2}_Papers.json'.format(resultDir, fileFirstName, fileLastName), 'w') as fout:
                json.dump(authorDict, fout, indent = 4)
                fout.write('\n')

        if ('{0}_{1}_ColabNet.json'.format(fileFirstName, fileLastName) not in os.listdir(resultDir)
            or overwrite == True):
            
            with open('{0}/{1}_{2}_Papers.json'.format(resultDir, fileFirstName, fileLastName), 'r') as fin:
                authorDict = json.load(fin)
            authorNet = util.oneDegreeAuthors(authorDict, firstName = firstName, 
                lastName = lastName, checkCitations = checkCitations, maxAnnualPapers = 36)
            with open('{0}/{1}_{2}_ColabNet.json'.format(resultDir, fileFirstName, fileLastName), 'w') as fout:
                json.dump(authorNet, fout, indent = 4)
                fout.write('\n')

        with open('{0}/{1}_{2}_ColabNet.json'.format(resultDir, fileFirstName, fileLastName), 'r') as fin:
            authorNet = json.load(fin)

        if ('{0}_{1}_OneDegreeNodes.csv'.format(fileFirstName, fileLastName) not in os.listdir(resultDir)
            or overwrite == True):

            nodeDF, edgeDF = util.buildCoauthorNodesEdges(authorNet)
            nodeDF.to_csv('{0}/{1}_{2}_OneDegreeNodes.csv'.format(resultDir, fileFirstName, fileLastName))
            edgeDF.to_csv('{0}/{1}_{2}_OneDegreeEdges.csv'.format(resultDir, fileFirstName, fileLastName))

    except Exception as err:
        print(str(err), '\n\n')
        continue
