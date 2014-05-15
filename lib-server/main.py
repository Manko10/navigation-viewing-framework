#!/usr/bin/python

## @file
# Server application for the distributed Navigation and Viewing Framework.

# import avango-guacamole libraries
import avango
import avango.gua

# import framework libraries
from SceneManager import *
from ApplicationManager import *
from RecorderPlayer import *

# import python libraries
import sys
import subprocess

# Command line parameters:
# main.py CONFIG_FILE SERVER_IP
# @param CONFIG_FILE The filname of the configuration file to parse.

## Main method for the server application
def start():

  # initialize materials
  avango.gua.load_shading_models_from("data/materials")
  avango.gua.load_materials_from("data/materials")

  # create loader class for geometry loading
  loader = avango.gua.nodes.GeometryLoader()

  # create scenegraph
  graph = avango.gua.nodes.SceneGraph(Name = "scenegraph")

  # get server ip 
  server_ip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0]
  server_ip = server_ip.strip(" \n")  
  server_ip = server_ip.rsplit(" ")
  server_ip = str(server_ip[-1])

  # initialize pseudo nettrans node as client processes are started in Platform class
  pseudo_nettrans = avango.gua.nodes.TransformNode(Name = "net")
  graph.Root.value.Children.value = [pseudo_nettrans]

  # initialize application manager
  application_manager = ApplicationManager(
      NET_TRANS_NODE = pseudo_nettrans
    , SCENEGRAPH = graph
    , CONFIG_FILE = sys.argv[1])

  # create distribution node and sync children from pseudo nettrans
  nettrans = avango.gua.nodes.NetTransform(
      Name = "net"
    , Groupname = "AVSERVER|{0}|7432".format(server_ip)
  )

  nettrans.Children.value = pseudo_nettrans.Children.value
  graph.Root.value.Children.value = [nettrans]

  # update nettrans node on all platforms
  for _nav in application_manager.navigation_list:
    _nav.platform.update_nettrans_node(nettrans)

  # initialize scene
  scene_manager = SceneManager(loader, nettrans)

  # initialize animation manager
  animation_manager = AnimationManager()
  animation_manager.my_constructor([ graph["/net/platform_0"] ])

  # distribute all nodes in the scenegraph
  distribute_all_nodes(nettrans, nettrans)

  # run application loop
  application_manager.run(locals(), globals())

## Registers a scenegraph node and all of its children at a NetMatrixTransform node for distribution.
# @param NET_TRANS_NODE The NetMatrixTransform node on which all nodes should be marked distributable.
# @param PARENT_NODE The node that should be registered distributable with all of its children.
def distribute_all_nodes(NET_TRANS_NODE, PARENT_NODE):

  # do not distribute the nettrans node itself
  if PARENT_NODE != NET_TRANS_NODE:
    NET_TRANS_NODE.distribute_object(PARENT_NODE)

  # iterate over children and make them distributable
  for _child in PARENT_NODE.Children.value:
    distribute_all_nodes(NET_TRANS_NODE, _child)


if __name__ == '__main__':
  start()
