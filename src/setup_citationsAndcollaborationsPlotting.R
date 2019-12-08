library(jsonlite, quietly = TRUE)
library(utils, quietly = TRUE)
library(ggplot2, quietly = TRUE)
library(plotly, quietly = TRUE)
library(htmlwidgets, quietly = TRUE)
library(Rtsne, quietly = TRUE)
library(dplyr, quietly = TRUE)
library(networkD3, quietly = TRUE)
library(reticulate, quietly = TRUE)
library(cowplot, quietly = TRUE)
library(ggnetwork, quietly = TRUE)
library(igraph, quietly = TRUE)
library(RColorBrewer, quietly = TRUE)
library(sna, quietly = TRUE)
library(network, quietly = TRUE)
np = import('numpy')

cutNodes = function(nodes, trimCol = 'Last authors', minVal = 1){
    nodeTrim = nodes[nodes[[trimCol]] >= minVal, ]
    nodeTrim$id = c(0:(nrow(nodeTrim) - 1)) #reset node ID
    if(nrow(nodeTrim) == nrow(nodes)){
        print('Warning, no rows were removed in cutNodes()')
    }
    return(nodeTrim)
}

cutEdges = function(trimmedNodes, edges){

    edgeCut = edges[c(edges$Author1 %in% trimmedNodes$Author), ]
    edgeCutMerge = merge(trimmedNodes, edgeCut, by.x = c('Author'), by.y = c('Author1'))
    edgeCutMerge$id1 = edgeCutMerge$id
    edgeCutMerge = merge(trimmedNodes, edgeCutMerge, by.x = c('Author'), by.y = c('Author2'))
    edgeCutMerge$id1 = edgeCutMerge$id.x 
    edgeCutMerge$id2 = edgeCutMerge$id.y 
    edgeDFTrim = edgeCutMerge %>% dplyr::select(c('Author', 'Author.y', 'AuthorKeyword.x', 
        'nPapers', 'nCitations', 'id1', 'id2')) %>% dplyr::rename('Author2' = 'Author.y', 
            'AuthorKeyword' = 'AuthorKeyword.x')
    if(nrow(edgeDFTrim) == nrow(edges)){
        print('Warning: edges were not successfully trimmed (perhaps minVal == 0 from cutNodes?)')
    }
    return(edgeDFTrim)
}


#Bring 2 authors together
nodesTwoAuthors = function(name1, name2, basePath, resultPath, 
    cutNode = TRUE, trimCol = 'Last authors', minVal = 3, 
    nodeFileTag = c('_OneDegreeNodes.csv')){

    if(name1 == 'Albert Laszlo Barabasi'){
        name1File = 'AlbertLaszlo_Barabasi'
    } else {name1File = gsub(' ', '_', name1)}
    
    if(name2 == 'Albert Laszlo Barabasi'){
        name2File = 'AlbertLaszlo_Barabasi'
    } else {name2File = gsub(' ', '_', name2)}

    nodeDF1 = read_csv(file.path(basePath, resultPath, 
        paste0(name1File, nodeFileTag))) %>% dplyr::select(-c('id', 'X1')) %>% as.data.frame()
    nodeDF1$AuthorKeyword = paste0(nodeDF1$`Author`, ' - ', nodeDF1$`Major keyword`)
    nodeDF2 = as.data.frame(read_csv(file.path(basePath, resultPath, 
        paste0(name2File, nodeFileTag)))) %>% dplyr::select(-c('id', 'X1')) %>% as.data.frame()
    nodeDF2$AuthorKeyword = paste0(nodeDF2$`Author`, ' - ', nodeDF2$`Major keyword`)

    if(sum(nodeDF1$Author %in% nodeDF2$Author) == 0){
        print('Warning, there are no overlapping authors for the two collaboration networks')
    }

    nodeDFCombine = rbind(nodeDF1, nodeDF2) %>% unique() %>% as.data.frame()

    if(cutNode == TRUE){
        nodeDFCombine = cutNodes(nodeDFCombine, trimCol = trimCol, minVal = minVal)
        if(!(name1 %in% nodeDFCombine$Author)){
            print(paste(name1, 'was dropped after cutNodes(), will add him/her back',
                'for the purposes of maintaining a connected network'))
            addBack = nodeDF1[nodeDF1$Author == name1, ]
            addBack$id = 0
            nodeDFCombine = rbind(addBack, nodeDFCombine)
            nodeDFCombine$id = c(0:(nrow(nodeDFCombine) - 1)) #reset node ID
        }
        if(!(name2 %in% nodeDFCombine$Author)){
            print(paste(name2, 'was dropped after cutNodes(), will add him/her back',
                'for the purposes of maintaining a connected network'))
            addBack = nodeDF1[nodeDF1$Author == name1, ]
            addBack$id = 0
            nodeDFCombine = rbind(addBack, nodeDFCombine)
            nodeDFCombine$id = c(0:(nrow(nodeDFCombine) - 1)) #reset node ID
        }
    } else {nodeDFCombine$id = c(0:(nrow(nodeDFCombine) - 1))}

    return(nodeDFCombine)
}

#EdgesTwoAuthors() needs an output from nodesTwoAuthors
edgesTwoAuthors = function(nodeDF, name1, name2, basePath, resultPath, 
    edgeFileTag = c('_OneDegreeEdges.csv')){

    if(name1 == 'Albert Laszlo Barabasi'){
        name1File = 'AlbertLaszlo_Barabasi'
    } else {name1File = gsub(' ', '_', name1)}
    
    if(name2 == 'Albert Laszlo Barabasi'){
        name2File = 'AlbertLaszlo_Barabasi'
    } else {name2File = gsub(' ', '_', name2)}

    edgeDF1 = as.data.frame(read_csv(file.path(basePath, resultPath, 
    paste0(name1File, edgeFileTag)))) %>% dplyr::select(-c('X1')) %>% as.data.frame()
    edgeDF2 = as.data.frame(read_csv(file.path(basePath, resultPath, 
        paste0(name2File, edgeFileTag)))) %>% dplyr::select(-c('X1')) %>% as.data.frame()
        
    edgeDFCombine = rbind(edgeDF1, edgeDF2) %>% select(-c('id1', 'id2')) %>% unique() %>%
        as.data.frame()
    edgeDFCombine = edgeDFCombine[c(edgeDFCombine$Author1 %in% nodeDF$Author), ]
    edgeCutMerge = merge(nodeDF, edgeDFCombine, by.x = c('Author'), by.y = c('Author1'))
    edgeCutMerge$id1 = edgeCutMerge$id
    edgeCutMerge = merge(nodeDF, edgeCutMerge, by.x = c('Author'), by.y = c('Author2'))
    edgeCutMerge$id1 = edgeCutMerge$id.x 
    edgeCutMerge$id2 = edgeCutMerge$id.y 
    edgeDFCombine = edgeCutMerge %>% dplyr::select(c('Author', 'Author.y', 'AuthorKeyword.x', 
        'nPapers', 'nCitations', 'id1', 'id2')) %>% dplyr::rename('Author2' = 'Author.y', 
            'AuthorKeyword' = 'AuthorKeyword.x') %>% unique()
    #Remove new redundant "reverse" order
    edgeDFTrim = edgeDFCombine[!(edgeDFCombine$Author == name2 & 
        (edgeDFCombine$Author2 == name1)), ]

    return(edgeDFTrim)
}

#Build D3 network of collaborations
networkD3Colab = function(edges, nodes, Source = 'id1', Target = 'id2', 
    Value = 'nPapers', nodeID = 'AuthorKeyword', nodeSize = 'Total papers', 
    Group = 'Major keyword', height = 1200, width = 1800, fontSize = 16,
    opacity = 0.8, opacityNoHover = 0, charge = -100, bounded = FALSE, 
    zoom = TRUE){

    net = forceNetwork(Links = edges, Nodes = nodes, Source = Source, 
        Target = Target, Value = Value, NodeID = nodeID, Nodesize = nodeSize, 
        Group = Group, height = height, width = width, fontSize = fontSize,
        opacity = opacity, opacityNoHover = opacityNoHover, charge = charge,
        bounded = bounded, zoom = zoom)

    return(net)
}

