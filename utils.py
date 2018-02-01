# providing the useful tools about mesh
# functions including:
# 	open mesh(only support .obj)
#	save mesh(only support .obj)
#	...

import numpy as np 

def load_obj(meshpath):
	"""
	given the path of the mesh xxx.obj
	return vertices and facet (numpy (n,3) array, (m,3) array, n=#vertices, m=#faces)
	"""
	vertices = []
	facet = []
	with open(meshpath,'r') as f:
		for line in f:
			if line.startswith('v '):
				values = line.split()
				vertex = [float(values[k]) for k in range(1,4)]
				vertices.append(vertex)
			if line.startswith('f'):
				values = line.split()
				face = [int((values[k].split('/'))[0])-1 for k in range(1,4)]
				facet.append(face)
	vertices = np.array(vertices, dtype=np.float64)
	facet = np.array(facet,dtype='int32')
	return vertices,facet

def save_obj(meshpath, vertices, facet):
	""" save the mesh as the desired path: xxx.obj, return True if whole process finish """
	with open(meshpath, 'w') as f:
		# write the vertices
		for k in range(len(vertices)):
			towrite = 'v' + ' ' + str(vertices[k][0]) + ' ' + str(vertices[k][1]) +' ' + str(vertices[k][2]) + '\n'
			f.write(towrite)
		# write the facet
		for k in range(len(facet)):
			towrite = 'f' + ' ' + str(facet[k][0] + 1) + ' ' + str(facet[k][1] + 1) + ' ' + str(facet[k][2] + 1) + '\n'
			f.write(towrite)
	return True