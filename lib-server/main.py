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
from Manipulation import *
from Portal import *
from PortalCamera import *
from PortalInteractionSpace import *
from Device import *

# import python libraries
import sys
import subprocess

# Command line parameters:
# main.py CONFIG_FILE
# @param CONFIG_FILE The filname of the configuration file to parse.
# @param START_CLIENTS Boolean saying if the client processes are to be started automatically.

class TimedRotate(avango.script.Script):
  TimeIn = avango.SFFloat()
  MatrixOut = avango.gua.SFMatrix4()

  @field_has_changed(TimeIn)
  def update(self):
    self.MatrixOut.value = avango.gua.make_trans_mat(0.0,1.2,0.0) * \
                           avango.gua.make_rot_mat(self.TimeIn.value*15.0, 0.0, 1.0, 0.0) * \
                           avango.gua.make_scale_mat(0.1)

## Main method for the server application
def start():

  # disable logger warningss
  logger = avango.gua.nodes.Logger(EnableWarning = False)

  # create scenegraph
  graph = avango.gua.nodes.SceneGraph(Name = "scenegraph")
  #graph.Root.value.GroupNames.value = ["all"]

  # get server ip 
  server_ip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0]
  server_ip = server_ip.strip(" \n")  
  server_ip = server_ip.rsplit(" ")
  server_ip = str(server_ip[-1])

  # initialize pseudo nettrans node as client processes are started in Platform class
  pseudo_nettrans = avango.gua.nodes.TransformNode(Name = "net")
  graph.Root.value.Children.value = [pseudo_nettrans]

  if sys.argv[2] == "True":
    start_clients = True 
  else:
    start_clients = False

  # initialize application manager
  application_manager = ApplicationManager(
      NET_TRANS_NODE = pseudo_nettrans
    , SCENEGRAPH = graph
    , CONFIG_FILE = sys.argv[1]
    , START_CLIENTS = start_clients)

  # create distribution node and sync children from pseudo nettrans
  nettrans = avango.gua.nodes.NetTransform(
      Name = "net"
    , Groupname = "AVSERVER|{0}|7432".format(server_ip)
  )
  #nettrans.GroupNames.value = ["all"]

  nettrans.Children.value = pseudo_nettrans.Children.value
  graph.Root.value.Children.value.remove(pseudo_nettrans)
  graph.Root.value.Children.value.append(nettrans)

  # update nettrans node on all platforms
  for _nav in application_manager.navigation_list:
    _nav.platform.update_nettrans_node(nettrans)

  # initialize scene
  scene_manager = SceneManager()
  scene_manager.my_constructor(nettrans, graph, application_manager.navigation_list)

  ######## TEST
  #videoloader = avango.gua.nodes.Video3DLoader()
  #video_geode = videoloader.load("kinect", "/opt/kinect-resources/kinect_surfaceLCD.ks")
  #nettrans.Children.value.append(video_geode)
  #nettrans.distribute_object(video_geode)

  #plodloader = avango.gua.nodes.PLODLoader()
  #plodloader.UploadBudget.value = 32
  #plodloader.RenderBudget.value = 2048
  #plodloader.OutOfCoreBudget.value = 4096
  #plod_geode = plodloader.create_geometry_from_file("point_cloud", "/mnt/pitoti/KDN_LOD/PITOTI_KDN_LOD/Spacemonkey_new.kdn")
  #nettrans.Children.value.append(plod_geode)
  #nettrans.distribute_object(plod_geode)
  ######## END TEST

  # initialize portal manager
  portal_manager = PortalManager()
  portal_manager.my_constructor(graph, application_manager.navigation_list)

  portal_camera = PortalCamera()
  portal_camera.my_constructor(portal_manager, application_manager.navigation_list[0], "device-portal-camera", "tracking-portal-camera")

  table_device = SpacemouseDevice()
  table_device.my_constructor("device-spacemouse", avango.gua.make_identity_mat())
  table_device.translation_factor = 0.05

  table_interaction_space = PortalInteractionSpace()
  table_interaction_space.my_constructor(table_device
                                       , application_manager.navigation_list[0].platform
                                       , avango.gua.Vec3(-2.016, 0.956, 1.651)
                                       , avango.gua.Vec3(-1.152, 1.021, 2.904))
  portal_camera.add_interaction_space(table_interaction_space)

  monkey_updater = TimedRotate()

  timer = avango.nodes.TimeSensor()
  monkey_updater.TimeIn.connect_from(timer.Time)
  graph["/net/Monkey/group/monkey1"].Transform.connect_from(monkey_updater.MatrixOut)

  # initialize animation manager
  #animation_manager = AnimationManager()
  #animation_manager.my_constructor([ graph["/net/platform_0"]]
  #                               , [ application_manager.navigation_list[0]])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace1/ceiling_light1"], graph["/net/SceneVRHyperspace1/ceiling_light2"], graph["/net/SceneVRHyperspace1/ceiling_light3"], graph["/net/SceneVRHyperspace1/ceiling_light4"], graph["/net/SceneVRHyperspace1/ceiling_light5"], graph["/net/SceneVRHyperspace1/ceiling_light6"]]
  #                               , [None, None, None, None, None, None])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace1/ceiling_light1"]]
  #                               , [None])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace1/ceiling_light1"], graph["/net/SceneVRHyperspace1/ceiling_light2"]]
  #                               , [None, None])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace1/ceiling_light1"], graph["/net/SceneVRHyperspace1/ceiling_light2"], graph["/net/SceneVRHyperspace1/ceiling_light3"], graph["/net/SceneVRHyperspace1/ceiling_light4"]]
  #                               , [None, None, None, None])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace1/steppo"]]
  #                               , [None])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace3/terrain_group"], graph["/net/SceneVRHyperspace4/terrain_group"]]
  #                               , [None, None])
  #animation_manager.my_constructor([graph["/net/SceneVRHyperspace3/terrain_group"]]
  #                               , [None])

  #manipulation_manager = ManipulationManager(nettrans, graph, scene_manager)

  ## distribute all nodes in the scenegraph
  distribute_all_nodes(nettrans, nettrans)

  # run application loop
  application_manager.run(locals(), globals())

## Registers a scenegraph node and all of its children at a NetMatrixTransform node for distribution.
# @param NET_TRANS_NODE The NetMatrixTransform node on which all nodes should be marked distributable.
# @param PARENT_NODE The node that should be registered distributable with all of its children.
def distribute_all_nodes(NET_TRANS_NODE, NODE):

  # do not distribute the nettrans node itself
  if NODE != NET_TRANS_NODE:
    NET_TRANS_NODE.distribute_object(NODE)
    #print "distribute", NODE, NODE.Name.value, NODE.Path.value

  # iterate over children and make them distributable
  for _child in NODE.Children.value:
    distribute_all_nodes(NET_TRANS_NODE, _child)


if __name__ == '__main__':
  start()