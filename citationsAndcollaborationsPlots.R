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
colabPath = c('ref')

firstName = 'AlbertLaszlo'
lastName = 'Barabasi'
nodeDF = as.data.frame(read_csv(file.path(filePath, colabPath, paste0(firstName, '_', 
    lastName, '_OneDegreeNodes.csv'))))
edgeDF = as.data.frame(read_csv(file.path(filePath, colabPath, paste0(firstName, '_', 
    lastName, '_OneDegreeEdges.csv'))))
nodeDF$AuthorKeyword = paste0(nodeDF$`Author`, ' - ', nodeDF$`Major keyword`)
trimNodes = cutNodes(nodeDF, trimCol = 'Last authors', minVal = 3)
trimEdges = cutEdges(trimNodes, edgeDF)
networkColab = networkD3Colab(trimEdges, trimNodes)
htmlwidgets::saveWidget(networkColab, paste0('plots/', firstName, '_', lastName, '_colabNetwork.html'))

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
htmlwidgets::saveWidget(networkColab, paste0('plots/', firstName, '_', lastName, '_colabNetwork.html'))
