# mesh for visualization

import numpy as np 
import geometry
import os

class Mesh(object):
	def __init__(self, vertices, facet):
		""" 
		initial the mesh with vertices and facet in numpy array 
		para::vertices: (n, 3) numpy array
		para::facet: (m, 3) numpy array
		"""
		self.v_num = len(vertices)
		self.f_num = len(facet)
		self.positions = vertices.T 
		self.indices = facet.T 
		self.set_mesh_center()
		self.set_dist_max()
		self.set_normals()

	def set_mesh_center(self):
		# set the center as the centroid of the mesh
		self.center = geometry.get_trimesh_centroid(self.positions.T, self.indices.T)


	def set_dist_max(self):
		# the max distance from the center to the vertex of the mesh
		dist = np.array([np.linalg.norm(self.positions.T[k] - self.center) for k in range(self.v_num)])
		self.dist_max = dist.max()


	def set_normals(self):
		# set the vertex normals
		self.normals = geometry.get_vertex_normal_list(self.positions.T, self.indices.T).T

# test the mesh
if __name__ == "__main__":
	cur_path = os.path.dirname(os.path.abspath(__file__))
	sphere_path = os.path.join(cur_path, "sphere.obj")
	from utils import load_obj
	vertices, facet = load_obj(sphere_path)
	mesh = Mesh(vertices, facet)
	print "vertex number: ", mesh.v_num
	print "facet number: ", mesh.f_num
	print "positions' shape: ", mesh.positions.shape
	print "indices' shape: ", mesh.indices.shape
	print "center: ", mesh.center
	print "dist_max: ", mesh.dist_max
	print "normals' shape: ", mesh.normals.shape