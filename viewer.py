# based on https://github.com/stephane-lb/tinyobjviewer
from __future__ import print_function
import nanogui
import random
import math
import time
import gc

from nanogui import Color, Screen, Window, GroupLayout, BoxLayout, \
                    ToolButton, Label, Button, Widget, \
                    PopupButton, CheckBox, MessageDialog, VScrollPanel, \
                    ImagePanel, ImageView, ComboBox, ProgressBar, Slider, \
                    TextBox, ColorWheel, Graph, GridLayout, \
                    Alignment, Orientation, TabWidget, IntBox, GLShader, GLCanvas, \
                    Arcball
from nanogui import gl, glfw, entypo
from utils import *
import os
from mesh import Mesh
import numpy as np

class CameraParameters(object):
	def __init__(self):
		self.arcball = Arcball()
		self.zoom = 1.
		self.viewAngle = 45.
		self.dnear = 0.05
		self.dfar = 100.
		self.eye = np.array([0., 0., 5.], dtype=np.float64)
		self.center = np.array([0., 0., 0.], dtype=np.float64)
		self.up = np.array([0., 1., 0.], dtype=np.float64)
		self.modelTranslation = np.zeros(3, dtype=np.float64)
		self.modelTranslation_start = np.zeros(3, dtype=np.float64)
		self.modelZoom = 1.

class Viewer(Screen):
	def __init__(self):
		super(Viewer, self).__init__((800, 600), "Mesh Viewer", False)
		self.m_camera = CameraParameters()
		self.m_translate = False
		self.m_translateStart = np.array([0, 0], dtype=np.int32)
		self.m_phong_shader = GLShader()
		self.initShaders()
		# set a default value of the mesh
		cur_path = os.path.dirname(os.path.abspath(__file__))
		sphere_path = os.path.join(cur_path, "sphere.obj")
		vertices, facet = load_obj(sphere_path)
		self.mesh = Mesh(vertices, facet)
		self.refresh_mesh()
		self.refresh_trackball_center()
		# store temp mesh
		self.mesh_temp = None

		window = Window(self, "Demo")
		window.setPosition((15, 15))
		window.setLayout(GroupLayout())
		

		Label(window, "Mesh IO", "sans-bold")
		valid = [("obj", "3D model format")]
		b_select = Button(window, "select")
		def cb_select():
			result = nanogui.file_dialog(valid, False)
			print("select file: %s" % result)
			if result == "":
				return
			vertices, facet = load_obj(result)
			self.mesh_temp = Mesh(vertices, facet)
			print("read in ok")
			#self.refresh_mesh()
			#self.refresh_trackball_center()
		b_select.setCallback(cb_select)
		# since python wrapper doesn't have mProcessEvents, seperate select and load
		b_load = Button(window, "load")
		def cb_load():
			self.mesh = self.mesh_temp
			self.refresh_mesh()
			self.refresh_trackball_center()
			print("load ok")
			self.mesh_temp = None
		b_load.setCallback(cb_load)
		
		b_save = Button(window, "save")
		def cb_save():
			result = nanogui.file_dialog(valid, True)
			print("save file: %s" % result)
			save_obj(result, self.mesh.positions.T, self.mesh.indices.T)
		b_save.setCallback(cb_save)
		
		self.performLayout()
	

	def refresh_mesh(self):
		self.m_phong_shader.bind()
		self.m_phong_shader.uploadIndices(self.mesh.indices)
		self.m_phong_shader.uploadAttrib("position", self.mesh.positions)
		self.m_phong_shader.uploadAttrib("normal", self.mesh.normals)

	def refresh_trackball_center(self):
		self.mesh.set_mesh_center()
		m_center = self.mesh.center
		self.m_camera.arcball = Arcball()
		self.m_camera.arcball.setSize(self.size())
		self.mesh.set_dist_max()
		self.m_camera.modelZoom = 2./ self.mesh.dist_max
		self.m_camera.modelTranslation = -m_center

	def keyboardEvent(self, key, scanmode, action, modifiers):
		if super(Viewer, self).keyboardEvent(key, scanmode, action, modifiers):
			return True
		if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
			self.setVisible(False)
			return True
		return False

	def getScreenCoord(self, rel):
		pos = self.mousePos()
		return np.array([
			2. * float(pos[0]) / self.width() - 1.,
			1. - 2. * float(pos[1]) / self.height()
		], dtype=np.float64)

	def drawContents(self):
		if self.mesh is None:
			return
		self.m_phong_shader.bind()
		model, view, proj = self.computeCameraMatrices()
		mv = np.dot(view, model)
		self.m_phong_shader.setUniform("MV", mv)
		self.m_phong_shader.setUniform("P", proj)
		gl.Enable(gl.DEPTH_TEST)
		gl.Disable(gl.CULL_FACE)
		self.m_phong_shader.drawIndexed(gl.TRIANGLES, 0, self.mesh.f_num)

	def scrollEvent(self, p, rel):
		#scrollEvent(self: nanogui.Widget, p: numpy.ndarray[int32[2, 1]], rel: numpy.ndarray[float32[2, 1]]) -> bool
		if not super(Viewer, self).scrollEvent(p, rel):
			if rel[1] > 0:
				temp = self.m_camera.zoom * 1.1
			else:
				temp = self.m_camera.zoom * 0.9 
			self.m_camera.zoom = max(0.1, temp)
		return True


	def mouseMotionEvent(self, p, rel, button, modifiers):
		#mouseMotionEvent(self: nanogui.Widget, p: numpy.ndarray[int32[2, 1]], rel: numpy.ndarray[int32[2, 1]], button: int, modifiers: int) -> bool
		if not super(Viewer, self).mouseMotionEvent(p, rel, button, modifiers):
			if (not self.m_camera.arcball.motion(p)) and self.m_translate:
				model, view, proj = self.computeCameraMatrices()
				zval = nanogui.project(self.mesh.center, np.dot(view, model), proj, 
					self.size())[2]
				pos1 = nanogui.unproject(np.array([p[0], self.size()[1] - p[1], 
					zval]), np.dot(view, model), proj, self.size())
				pos0 = nanogui.unproject(np.array([self.m_translateStart[0],
					self.size()[1] - self.m_translateStart[1],
					zval]), np.dot(view, model), proj, self.size())
				self.m_camera.modelTranslation = self.m_camera.modelTranslation_start + (
					pos1 - pos0)
		return True

	def mouseButtonEvent(self, p, button, down, modifiers):
		#mouseButtonEvent(self: nanogui.Widget, p: numpy.ndarray[int32[2, 1]], button: int, down: bool, modifiers: int) -> bool
		if not super(Viewer, self).mouseButtonEvent(p, button, down, modifiers):
			if button == glfw.MOUSE_BUTTON_1 and modifiers == 0:
				self.m_camera.arcball.button(p, down)
			else:
				if button == glfw.MOUSE_BUTTON_2 or (button == glfw.MOUSE_BUTTON_1 and 
					modifiers == glfw.MOD_SHIFT):
					self.m_camera.modelTranslation_start = self.m_camera.modelTranslation
					self.m_translate = True
					self.m_translateStart = p
		if button == glfw.MOUSE_BUTTON_1 and not down:
			self.m_camera.arcball.button(p, False)
		if not down:
			self.m_translate = False
		return True

	def initShaders(self):

		self.m_phong_shader.init(
			"phong_shader",
			# vertex shader
			"""#version 330
			uniform mat4 MV;
			uniform mat4 P;
			in vec3 position;
			in vec3 normal;
			out vec3 fcolor;
			out vec3 fnormal;
			out vec3 view_dir;
			out vec3 light_dir;
			void main(){
				vec4 vpoint_mv = MV * vec4(position, 1.0);
				gl_Position = P * vpoint_mv;
				fcolor = vec3(0.7);
				fnormal = mat3(transpose(inverse(MV))) * normal;
				light_dir = vec3(0.0, 3.0, 3.0) - vpoint_mv.xyz;
				view_dir = -vpoint_mv.xyz;
			}""",
			# fragment shader
			"""#version 330
			in vec3 fcolor;
			in vec3 fnormal;
			in vec3 view_dir;
			in vec3 light_dir;
			out vec4 color;
			void main(){
				vec3 c = vec3(0.0);
				c += vec3(1.0) * vec3(0.18, 0.1, 0.1);
				vec3 n = normalize(fnormal);
				vec3 v = normalize(view_dir);
				vec3 l = normalize(light_dir);
				float lambert = dot(n,l);
				if(lambert>0.0){
					c += vec3(lambert);
					//vec3 r = reflect(-l,n);
					//c += vec3(pow(max(dot(r,v), 0.0), 90.0));
				}
				c *= fcolor;
				color = vec4(c, 1.0);
			}"""
		)

	def computeCameraMatrices(self):
		view = nanogui.lookAt(self.m_camera.eye, self.m_camera.center, self.m_camera.up)
		fH = np.tan(self.m_camera.viewAngle / 360. * np.pi) * self.m_camera.dnear
		fW = fH * float(self.size()[0]) / float(self.size()[1])
		proj = nanogui.frustum(-fW, fW, -fH, fH, self.m_camera.dnear, self.m_camera.dfar)
		model = self.m_camera.arcball.matrix()
		model = np.dot(model, nanogui.scale(np.full(3, self.m_camera.zoom *
			self.m_camera.modelZoom)))
		model = np.dot(model, nanogui.translate(self.m_camera.modelTranslation))
		return model, view, proj

if __name__ == "__main__":
	nanogui.init()
	test = Viewer()
	test.drawAll()
	test.setVisible(True)
	nanogui.mainloop()
	del test
	gc.collect()
	nanogui.shutdown()
