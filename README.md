# Publication Collaboration Networks

Programmatic queries of Entrez and Arxiv to build and visualize collaboration networks on published papers. 

First, create lists of papers, co-authors, and the edges and nodes between authors
via _citationsAndcollaborations.py_. First and last names are a matched pair of
lists. It is recommended to cap the number of papers queried in a given year, as
too many will not render well with plotly anyways. 

Second, create a network visualization using networkD3 in _citationsAndcollaborationsPlots.R_. Swap in first and last names as needed, so long as the authors have first been compiled with the _.py_ script.
