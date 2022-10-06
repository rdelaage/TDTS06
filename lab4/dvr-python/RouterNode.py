#!/usr/bin/env python
import GuiTextArea, RouterPacket, F
from copy import deepcopy

class RouterNode():
	myID = None
	myGUI = None
	sim = None
	costs = None

    # Access simulator variables with:
    # self.sim.POISONREVERSE, self.sim.NUM_NODES, etc.

    # --------------------------------------------------
	def __init__(self, ID, sim, costs):
		self.myID = ID
		self.sim = sim
		self.myGUI = GuiTextArea.GuiTextArea("	Output window for Router #" + str(ID) + "  ")

		self.costs = deepcopy(costs)
		
		# feed distance vector from ourself (Dx(y), y in N)
		self.distanceVector = deepcopy(costs)
		
		self.neighbors = []
		self.routes = ["-"] * sim.NUM_NODES
		#route to ourself is ourself
		self.routes[ID] = ID
		
		#find neighbors node
		for i in range(sim.NUM_NODES):
			# this node is a neighbor if we don't have an infinite cost and this is not ourself
			if self.costs[i] != sim.INFINITY and i != ID:
				self.neighbors.append(i)
				#neighbor so direct route
				self.routes[i] = i

		self.distanceTable = {}
			
		for neighbor in self.neighbors:
			self.distanceTable[neighbor] = [0] * sim.NUM_NODES
			# feed distance vector for each neighbor node (Dw(y) y in N)
			for i in range(sim.NUM_NODES):
				#we don't know distance from w to y so Dw(y) = INFINITY
				self.distanceTable[neighbor][i] = sim.INFINITY

		# send our distance vector to all neighbors
		for neighbor in self.neighbors:
			self.sendUpdate(RouterPacket.RouterPacket(ID, neighbor, self.distanceVector))

    # --------------------------------------------------
	def recvUpdate(self, pkt):
		# action only if the packet is sended to us
		if pkt.destid == self.myID:
			#save the distance vector in our distance table
			self.distanceTable[pkt.sourceid] = pkt.mincost
			
			newDistanceVector = deepcopy(self.distanceVector)
			newRoutes = deepcopy(self.routes)
			#for each node of the graph update our distance vector with Dx(y) = minv{c(x,v) + Dv(y)}
			for iNode in range(self.sim.NUM_NODES):
				#initialiaze minimum distance to iNode to our cost to iNode
				minDistance = self.costs[iNode]
				minRoute = self.routes[iNode]
				
				#calculate minimum distance to iNode through all neighbors
				for neighbor in self.neighbors:
					#the distance to iNode through this neighbor is = to the cost to go to this neighbor + the distance from this neighbor to iNode
					distanceThroughNeighbor = self.costs[neighbor] + self.distanceTable[neighbor][iNode]
					if distanceThroughNeighbor < minDistance:
						#only update minimum distance to iNode if we have a smaller cost
						minDistance = distanceThroughNeighbor
						minRoute = neighbor
				
				#update the distance vector with the minimum value
				newDistanceVector[iNode] = minDistance
				newRoutes[iNode] = minRoute
				
			
			#check if the distance vector was changed
			changed = False
			for iNode in range(self.sim.NUM_NODES):
				if newDistanceVector[iNode] != self.distanceVector[iNode]:
					changed = True
			
			#if the distance vector was changed we update it and send the update to all the neighbors
			if changed:
				self.distanceVector = newDistanceVector
				self.routes = newRoutes
				for neighbor in self.neighbors:
					self.sendUpdate(RouterPacket.RouterPacket(self.myID, neighbor, self.distanceVector))


    # --------------------------------------------------
	def sendUpdate(self, pkt):
		self.sim.toLayer2(pkt)


    # --------------------------------------------------
	def printDistanceTable(self):
		self.myGUI.println("Current table for " + str(self.myID) +
				   "  at time " + str(self.sim.getClocktime()))
		if self.sim.NUM_NODES == 5:
			self.myGUI.println("Distancetable:\nto node |   0 |   1 |   2 |   3 |   4 |\n-------------------------------")
		elif self.sim.NUM_NODES == 4:
			self.myGUI.println("Distancetable:\nto node |   0 |   1 |   2 |   3 |\n-------------------------")
		elif self.sim.NUM_NODES == 3:
			self.myGUI.println("Distancetable:\nto node |   0 |   1 |   2 |\n-------------------")
			
		for neighbor in self.distanceTable:
			line = "n°    " + str(neighbor) + " |"
			for i in range(self.sim.NUM_NODES):
				line += f" {self.distanceTable[neighbor][i]} |"
			self.myGUI.println(line)
			
		if self.sim.NUM_NODES == 5:
			self.myGUI.println("distance vector and route:\nto node |   0 |   1 |   2 |   3 |   4 |\n-------------------------------")
		elif self.sim.NUM_NODES == 4:
			self.myGUI.println("distance vector and route:\nto node |   0 |   1 |   2 |   3 |\n-------------------------")
		elif self.sim.NUM_NODES == 3:
			self.myGUI.println("distance vector and route:\nto node |   0 |   1 |   2 |\n-------------------")
			
		line = "dist    |"
		for i in range(self.sim.NUM_NODES):
			line += f" {self.distanceVector[i]} |"
		self.myGUI.println(line)
			
		line = "route   |"
		for i in range(self.sim.NUM_NODES):
			line += f" {self.routes[i]} |"
		self.myGUI.println(line)


    # --------------------------------------------------
	def updateLinkCost(self, dest, newcost):
		pass
