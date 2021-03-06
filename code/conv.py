#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Convolutional Neural Network library
# copyright (c) 2014 Vedran Vukotic
# gmail: vevukotic

# conv.py - forward and back propagation for convolutional layers


import numpy as np
from utils import *
from featuremaps import *

# connects two layers by performing convolutions
class convolutionalConnection:
	def __init__(self, prevLayer, currLayer, connectionMatrix, kernelWidth, kernelHeight, stepX, stepY, useLogistic = False):
		self.connections  = connectionMatrix
		self.prevLayer   = prevLayer
		self.currLayer  = currLayer
		self.kernelHeight = kernelHeight
		self.kernelWidth  = kernelWidth
		self.stepX        = stepX
		self.stepY        = stepY

		if useLogistic:
			self.act = logistic()
		else:
			self.act = tanh()

		if prevLayer.get_n()  != np.shape(self.connections)[0] or \
		   currLayer.get_n() != np.shape(self.connections)[1]:
		   	print "Connection matrix size = ", self.connections.shape
			print "first layer = ", self.prevLayer.get_n()
			print "second layer = ", self.currLayer.get_n()
		   	raise Exception("convolutionalConnection: connection matrix shape does not match number" \
			"of feature maps in connecting layers")

		if np.ceil((self.prevLayer.get_FM().shape[1] - self.kernelHeight) / self.stepY + 1) != self.currLayer.get_FM().shape[1] or \
		   np.ceil((self.prevLayer.get_FM().shape[2] - self.kernelWidth) / self.stepX + 1) != self.currLayer.get_FM().shape[2]:
		   	raise Exception("Feature maps size mismatch")

		# random init kernels
		self.nKernels = self.prevLayer.get_n() * self.currLayer.get_n()
	
		# compute number of units in each layer (required to initlize weights)
		nPrev = self.prevLayer.get_n() * self.prevLayer.get_FM().shape[1] * self.prevLayer.get_FM().shape[2] 
		nCurr = self.currLayer.get_n() * self.currLayer.get_FM().shape[1] * self.currLayer.get_FM().shape[2]

		# calculate interval for random weights initialization
		l, h = self.act.sampleInterval(nPrev, nCurr)
	
		# initialize kernels to random values
		nCombinations = self.prevLayer.get_n() * self.currLayer.get_n()
		self.k = np.random.uniform(low = l, high = h, size = [nCombinations, self.kernelHeight, self.kernelWidth])

		# initialize one bias per feature map
		self.biasWeights = np.random.uniform(low = l, high = h, size = [self.currLayer.get_n()])
	
	def propagate(self):
		FMs = np.zeros([self.currLayer.get_n(), self.currLayer.shape()[0], self.currLayer.shape()[1]])
		inFMs = self.prevLayer.get_FM()

		k = 0 # kernel index, there is one foreach i, j combination
		for j in range(self.currLayer.get_n()): # foreach FM in the current layer
			for i in range(self.prevLayer.get_n()): # foreach FM in the previous layer
				if self.connections[i, j] == 1:

					# foreach neuron in the feature map
					for y_out in range(self.currLayer.shape()[0]):
						for x_out in range(self.currLayer.shape()[1]):

							# iterate inside the visual field for that neuron
							for y_k in range(0, self.kernelHeight, self.stepY):
								for x_k in range(0, self.kernelWidth, self.stepX):
									FMs[j, y_out, x_out] += inFMs[i, y_out + y_k, x_out + x_k] * self.k[k, y_k, x_k]
							# add bias
							FMs[j, y_out, x_out] += 1 * self.biasWeights[j]
				# next kernel
				k += 1

			# compute sigmoid (of a matrix since it's faster than elementwise)
			FMs[j] = self.act.func(FMs[j])


		#print "out = ", FMs
		self.currLayer.set_FM(FMs)
		return FMs
	
	def bprop(self, ni, target = None, verbose = False):
		
		yi = self.prevLayer.get_FM() # get output of previous layer
		yj = self.currLayer.get_FM() # get output of current layer

		# TODO: A conv. layer cannot be an output, remove computing error part
		if not self.currLayer.isOutput:
			currErr = self.currLayer.get_FM_error()
		else:
			currErr = -(target - yj) * self.act.deriv(yj)
			self.currLayer.set_FM_error(currErr)
		#print "\ncurrent error = \n", currErr

		# compute error in previous layer
		prevErr = np.zeros([self.prevLayer.get_n(), self.prevLayer.shape()[0], self.prevLayer.shape()[1]])
		biasErr = np.zeros([self.currLayer.get_n()])

		k = 0 
		for j in range(self.currLayer.get_n()): # foreach FM in the current layer
			for i in range(self.prevLayer.get_n()): # foreach FM in the previous layer
				if self.connections[i, j] == 1:

					# foreach neuron in the feature map
					for y_out in range(self.currLayer.shape()[0]):
						for x_out in range(self.currLayer.shape()[1]):

							# iterate inside the visual field for that neuron
							for y_k in range(0, self.kernelHeight, self.stepY):
								for x_k in range(0, self.kernelWidth, self.stepX):
									#FMs[j, y_out, x_out] += inFMs[i, y_out + y_k, x_out + x_k] * self.k[k, y_k, x_k]dd
									prevErr[i, y_out + y_k, x_out + x_k] += self.k[k, y_k, x_k] * currErr[j, y_out, x_out]

							# add bias
							biasErr[j] += currErr[j, y_out, x_out] * self.k[k, y_k, x_k]
				# next kernel
				k += 1

		for i in range(self.prevLayer.get_n()):
			prevErr[i] = prevErr[i] * self.act.deriv(yi[i])

		for j in range(self.currLayer.get_n()):
			biasErr[j] = biasErr[j] * self.act.deriv(1)


		self.prevLayer.set_FM_error(prevErr)

		# compute weights update
		dw = np.zeros(self.k.shape)
		dwBias = np.zeros(self.currLayer.get_n())
		k = 0 
		for j in range(self.currLayer.get_n()): # foreach FM in the current layer
			for i in range(self.prevLayer.get_n()): # foreach FM in the previous layer
				if self.connections[i, j] == 1:

					# foreach neuron in the feature map
					for y_out in range(self.currLayer.shape()[0]):
						for x_out in range(self.currLayer.shape()[1]):

							# iterate inside the visual field for that neuron
							for y_k in range(0, self.kernelHeight, self.stepY):
								for x_k in range(0, self.kernelWidth, self.stepX):
									#FMs[j, y_out, x_out] += inFMs[i, y_out + y_k, x_out + x_k] * self.k[k, y_k, x_k]dd
									dw[k, y_k, x_k] +=  yi[i, y_out + y_k, x_out + x_k] * currErr[j, y_out, x_out]

							# add bias
							dwBias[j] += 1 * currErr[j, y_out, x_out]

				# next kernel
				k += 1


		# update weights
		self.k -= ni * dw
		self.biasWeights -= ni * dwBias

