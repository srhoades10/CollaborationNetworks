#Visualize colaboration networks using networkD3. Attempts are made to color nodes
# ... by common paper keywords
#
# Author: Seth Rhoades

library(jsonlite, quietly = TRUE)
library(utils, quietly = TRUE)
library(dplyr, quietly = TRUE)
library(readr, quietly = TRUE)
source('src/setup_citationsAndcollaborationsPlotting.R')

filePath = c('.')
colabPath = c('collaborationResults')
firstName = 'Albert Lazslo'
lastName = 'Barabasi'
nodeDF = as.data.frame(read_csv(file.path(filePath, colabPath, paste0(firstName, '_', 
    lastName, '_OneDegreeNodes.csv'))))
edgeDF = as.data.frame(read_csv(file.path(filePath, colabPath, paste0(firstName, '_', 
    lastName, '_OneDegreeEdges.csv'))))
nodeDF$AuthorKeyword = paste0(nodeDF$`Author`, ' - ', nodeDF$`Major keyword`)
trimNodes = cutNodes(nodeDF, trimCol = 'Last authors', minVal = 3)
trimEdges = cutEdges(trimNodes, edgeDF)
networkColab = networkD3Colab(trimEdges, trimNodes)
networkColab
htmlwidgets::saveWidget(networkColab, paste0(firstName, '_', lastName, '_colabNetwork.html'))

firstName = 'Seth'
lastName = 'Rhoades'
nodeDF = as.data.frame(read_csv(file.path(filePath, colabPath, paste0(firstName, '_', 
    lastName, '_OneDegreeNodes.csv'))))
edgeDF = as.data.frame(read_csv(file.path(filePath, colabPath, paste0(firstName, '_', 
    lastName, '_OneDegreeEdges.csv'))))
nodeDF$AuthorKeyword = paste0(nodeDF$`Author`, ' - ', nodeDF$`Major keyword`)
trimNodes = cutNodes(nodeDF, trimCol = 'Last authors', minVal = 3)
trimEdges = cutEdges(trimNodes, edgeDF)
networkColab = networkD3Colab(trimEdges, trimNodes)
networkColab
htmlwidgets::saveWidget(networkColab, paste0(firstName, '_', lastName, '_colabNetwork.html'))

#Bring 2 authors together
nodeDFs = nodesTwoAuthors('Randy Schekman', 'James Rothman', filePath, colabPath, 
    cutNode = TRUE, minVal = 1)
edgeDFs = edgesTwoAuthors(nodeDFs, 'Randy Schekman', 'James Rothman', filePath, colabPath)
network2Colab = networkD3Colab(edgeDFs, nodeDFs)
htmlwidgets::saveWidget(network2Colab, paste0(expDir, '_', dimReduce, '_3DScatter.html'))
