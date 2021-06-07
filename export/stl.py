'''
Created on Mar 25, 2013

@author: anizam
'''

"""an STL script to create rectangles. 
- first divide the traces into rectangles.
- create vertices on the border points. create extra vertices where two rectangles meet. mirror
the vertices on the opposite side. 


-SolidWorks cannot handle rectangular traces, so the trace of RD100 is broken down to triangles. 
    - identify a rectangle first. then break it into a subroutine to create two triangles.
    
    REF: http://code.activestate.com/recipes/578246-stl-writer/
"""

'=============================================='
"STL FORMAT"
"""solid name
facet normal ni nj nk
outer loop
vertex v1x v1y v1z
vertex v2x v2y v2z
vertex v3x v3y v3z
endloop
endfacet
endsolid name"""
'=============================================='

