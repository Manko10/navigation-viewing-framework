#!/usr/bin/python

## @file
# Contains class Platform.

# import avango-guacamole libraries
import avango
import avango.gua
import avango.script
import avango.daemon
from   avango.script import field_has_changed

# import framework libraries
from SlotManager import *
from Slot        import *
from ConsoleIO   import *

# import python libraries
import subprocess
import os


## Internal representation of a platform which is controlled by an input device.
#
# Users can stick themselves to a platform and explore the scene on it.

class Platform(avango.script.Script):

  # input and output field
  ## @var sf_abs_mat
  # Matrix representing the current translation and rotation of the platform in the scene.
  sf_abs_mat = avango.gua.SFMatrix4()
  sf_abs_mat.value = avango.gua.make_identity_mat()

  ## @var timer
  # A timer instance to get the current time in seconds.
  timer = avango.nodes.TimeSensor()

  sf_scale = avango.SFFloat()
  sf_scale.value = 1.0

  ## @var hosts_visited
  # List of hostnames on which a client daemon was already launched. Used to avoid double launching.
  hosts_visited = []
  
  ## Default constructor.
  def __init__(self):
    self.super(Platform).__init__()

    ## @var start_clients
    # Debug flag saying if client processes should be started.
    self.start_clients = False

    ## @var start_time
    # Time when a decoupling notifier was displayed.
    self.start_time = None

    ## @var screens
    # List of ScreenNode instances which are appended to this platform.
    self.screens = []
    

  ## Custom constructor.
  # @param NET_TRANS_NODE Reference to the net matrix node in the scenegraph for distribution.
  # @param SCENEGRAPH Reference to the scenegraph.
  # @param PLATFORM_SIZE Physical size of the platform in meters. Passed in an two-element list: [width, depth]
  # @param INPUT_MAPPING_INSTANCE An instance of InputMapping which accumulates the device inputs for this platform.
  # @param PLATFORM_ID The id number assigned to this platform, starting from 0.
  # @param TRANSMITTER_OFFSET The matrix offset that is applied to the values delivered by the tracking system.
  # @param NO_TRACKING_MAT Matrix which should be applied if no tracking is available.
  # @param DISPLAYS The names of the displays that belong to this navigation.
  # @param AVATAR_TYPE A string that determines what kind of avatar representation is to be used ["joseph", "joseph_table", "kinect"].
  # @param SLOT_MANAGER Reference to the one and only SlotManager instance in the setup.
  # @param CONFIG_FILE The path to the config file that is used.
  # @param AVATAR_MATERIAL String containing the material to be used for avatars of this platform.
  def my_constructor(
      self
    , NET_TRANS_NODE
    , SCENEGRAPH
    , PLATFORM_SIZE
    , INPUT_MAPPING_INSTANCE
    , PLATFORM_ID
    , TRANSMITTER_OFFSET
    , NO_TRACKING_MAT
    , DISPLAYS
    , AVATAR_TYPE
    , SLOT_MANAGER
    , CONFIG_FILE
    , AVATAR_MATERIAL):

    ## @var NET_TRANS_NODE
    # Reference to the net matrix node in the scenegraph for distribution.
    self.NET_TRANS_NODE = NET_TRANS_NODE

    ## @var platform_id
    # The id number of this platform, starting from 0.
    self.platform_id = PLATFORM_ID   

    ## @var INPUT_MAPPING_INSTANCE
    # Reference to an InputMapping which accumulates the device inputs for this platform.
    self.INPUT_MAPPING_INSTANCE = INPUT_MAPPING_INSTANCE

    ## @var width
    # Physical width of the platform in meters.
    self.width = PLATFORM_SIZE[0]

    ## @var depth
    # Physical depth of the platform in meters.
    self.depth = PLATFORM_SIZE[1]

    ## @var transmitter_offset
    # The transmitter offset to be applied.
    self.transmitter_offset = TRANSMITTER_OFFSET

    ## @var no_tracking_mat
    # The matrix to be applied when no tracking information is available for users.
    self.no_tracking_mat = NO_TRACKING_MAT

    ## @var displays 
    # List of names of the displays that belong to this navigation.
    self.displays = DISPLAYS

    ## @var avatar_type
    # A string that determines what kind of avatar representation is to be used.
    self.avatar_type = AVATAR_TYPE

    ## @var slot_list
    # A list of Slot instances that are associated to this platform.
    self.slot_list = []

    ## @var avatar_material
    # String containing the material to be used for avatars of this platform.
    self.avatar_material = AVATAR_MATERIAL

    # extend scenegraph with platform node
    ## @var platform_transform_node
    # Scenegraph node representing this platform's transformation.
    self.platform_transform_node = avango.gua.nodes.TransformNode(Name = "platform_" + str(PLATFORM_ID))
    self.platform_transform_node.Transform.connect_from(self.sf_abs_mat)
    NET_TRANS_NODE.Children.value.append(self.platform_transform_node)

    self.platform_scale_transform_node = avango.gua.nodes.TransformNode(Name = "scale")
    self.platform_transform_node.Children.value = [self.platform_scale_transform_node]

    # get own ip adress
    _server_ip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0]
    _server_ip = _server_ip.strip(" \n")
    _server_ip = _server_ip.rsplit(" ")
    _server_ip = str(_server_ip[-1])

    # get own hostname
    _hostname = open('/etc/hostname', 'r').readline()
    _hostname = _hostname.strip(" \n")

    # open ssh connection for all hosts associated to display
    for _display in self.displays:
      # append a screen node to platform
      _screen = _display.create_screen_node("screen_" + str(self.displays.index(_display)))
      self.platform_scale_transform_node.Children.value.append(_screen)
      self.screens.append(_screen)
      
      _screen_visualization = _display.create_screen_visualization()
      self.platform_scale_transform_node.Children.value.append(_screen_visualization)

      _string_num = 0
      # create a slot for each displaystring
      for _displaystring in _display.displaystrings:
        
        if _display.shutter_timings == []:
          # create mono slot
          _slot = Slot(_display,
                       _string_num,
                       self.displays.index(_display),
                       False,
                       self.platform_scale_transform_node)
          self.slot_list.append(_slot)
          SLOT_MANAGER.register_slot(_slot, _display)
        else:
          # create stereo slot
          _slot = Slot(_display,
                       _string_num,
                       self.displays.index(_display),
                       True,
                       self.platform_scale_transform_node)
          self.slot_list.append(_slot)
          SLOT_MANAGER.register_slot(_slot, _display)

        _string_num += 1


      _directory_name = os.path.dirname(os.path.dirname(__file__))

      if self.start_clients:
        # run ClientDaemon on host if necessary
        if _display.hostname not in Platform.hosts_visited and \
           _display.hostname != _hostname:
          _ssh_run = subprocess.Popen(["ssh", _display.hostname, _directory_name + "/start-client-daemon.sh"])
          Platform.hosts_visited.append(_display.name)

        # run client process on host
        # command line parameters: server ip, platform id, display name, screen number
        _ssh_run = subprocess.Popen(["ssh", _display.hostname, _directory_name + \
            "/start-client.sh " + _server_ip + " " + str(self.platform_id) + " " + \
            _display.name + " " + str(self.displays.index(_display))]
          , stderr=subprocess.PIPE)
      else:
        print_warning("Start of client on " + _display.hostname + " disabled for debugging reasons.")

    # connect to input mapping instance
    self.sf_abs_mat.connect_from(INPUT_MAPPING_INSTANCE.sf_abs_mat)
    self.sf_scale.connect_from(INPUT_MAPPING_INSTANCE.sf_scale)

    # create four boundary planes
    _loader = avango.gua.nodes.GeometryLoader()

    ## @var left_border
    # Geometry scenegraph node of the platform's left border
    self.left_border = _loader.create_geometry_from_file('left_border_geometry',
                                                         'data/objects/plane.obj',
                                                         'data/materials/PlatformBorder.gmd',
                                                         avango.gua.LoaderFlags.DEFAULTS)
    self.left_border.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.left_border.Transform.value = avango.gua.make_trans_mat(-self.width/2, 1.0, self.depth/2) * \
                                       avango.gua.make_rot_mat(90, 1, 0, 0) * \
                                       avango.gua.make_rot_mat(270, 0, 0, 1) * \
                                       avango.gua.make_scale_mat(self.depth, 1, 2)
    self.left_border.GroupNames.value = ["do_not_display_group", "platform_group_" + str(PLATFORM_ID)]
    self.platform_scale_transform_node.Children.value.append(self.left_border)    
    
    ## @var right_border
    # Geometry scenegraph node of the platform's left border
    self.right_border = _loader.create_geometry_from_file('right_border_geometry',
                                                         'data/objects/plane.obj',
                                                         'data/materials/PlatformBorder.gmd',
                                                         avango.gua.LoaderFlags.DEFAULTS)
    self.right_border.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.right_border.Transform.value = avango.gua.make_trans_mat(self.width/2, 1.0, self.depth/2) * \
                                        avango.gua.make_rot_mat(90, 1, 0, 0) * \
                                        avango.gua.make_rot_mat(90, 0, 0, 1) * \
                                        avango.gua.make_scale_mat(self.depth, 1, 2)
    self.right_border.GroupNames.value = ["do_not_display_group", "platform_group_" + str(PLATFORM_ID)]
    self.platform_scale_transform_node.Children.value.append(self.right_border)    

    ## @var front_border
    # Geometry scenegraph node of the platform's front border
    self.front_border = _loader.create_geometry_from_file('front_border_geometry',
                                                         'data/objects/plane.obj',
                                                         'data/materials/PlatformBorder.gmd',
                                                         avango.gua.LoaderFlags.DEFAULTS)
    self.front_border.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.front_border.Transform.value = avango.gua.make_trans_mat(0, 1, 0) * \
                                        avango.gua.make_rot_mat(90, 1, 0, 0) * \
                                        avango.gua.make_scale_mat(self.width, 1, 2)
    self.front_border.GroupNames.value = ["do_not_display_group", "platform_group_" + str(PLATFORM_ID)]
    self.platform_scale_transform_node.Children.value.append(self.front_border)

    ## @var back_border
    # Geometry scenegraph node of the platform's back border
    self.back_border = _loader.create_geometry_from_file('back_border_geometry',
                                                         'data/objects/plane.obj',
                                                         'data/materials/PlatformBorder.gmd',
                                                         avango.gua.LoaderFlags.DEFAULTS)
    self.back_border.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.back_border.Transform.value = avango.gua.make_trans_mat(0.0, 1.0, self.depth) * \
                                        avango.gua.make_rot_mat(90, 1, 0, 0) * \
                                        avango.gua.make_rot_mat(180, 0, 0, 1) * \
                                        avango.gua.make_scale_mat(self.width, 1, 2)
    self.back_border.GroupNames.value = ["do_not_display_group", "platform_group_" + str(PLATFORM_ID)]
    self.platform_scale_transform_node.Children.value.append(self.back_border)

    # create coupling notification plane
    self.create_coupling_plane()

    # create coupling status notifications
    self.create_coupling_status_overview()

  ## Toggles visibility of left platform border.
  # @param VISIBLE A boolean value if the border should be set visible or not.
  def display_left_border(self, VISIBLE):
    if VISIBLE:
      self.left_border.GroupNames.value[0] = "display_group"
    else:
      self.left_border.GroupNames.value[0] = "do_not_display_group"

  ## Toggles visibility of right platform border.
  # @param VISIBLE A boolean value if the border should be set visible or not.
  def display_right_border(self, VISIBLE):
    if VISIBLE:
      self.right_border.GroupNames.value[0] = "display_group"
    else:
      self.right_border.GroupNames.value[0] = "do_not_display_group"

  ## Toggles visibility of front platform border.
  # @param VISIBLE A boolean value if the border should be set visible or not.
  def display_front_border(self, VISIBLE):
    if VISIBLE:
      self.front_border.GroupNames.value[0] = "display_group"
    else:
      self.front_border.GroupNames.value[0] = "do_not_display_group"

  ## Toggles visibility of back platform border.
  # @param VISIBLE A boolean value if the border should be set visible or not.
  def display_back_border(self, VISIBLE):
    if VISIBLE:
      self.back_border.GroupNames.value[0] = "display_group"
    else:
      self.back_border.GroupNames.value[0] = "do_not_display_group"
         

  @field_has_changed(sf_scale)
  def sf_scale_values_changed(self):

    _scale = self.sf_scale.value
    
    self.platform_scale_transform_node.Transform.value = avango.gua.make_scale_mat(_scale)


  ## Creates a plane in front of the user used for displaying coupling messages.
  def create_coupling_plane(self):
    
    _loader = avango.gua.nodes.GeometryLoader()

    ## @var message_plane_node
    # Transform node combining coupling and decoupling message geometry nodes.
    self.message_plane_node = avango.gua.nodes.TransformNode(Name = "message_plane_node")

    # set transform values and extend scenegraph
    self.handle_message_plane_node()

    ## @var coupling_plane_node
    # Geometry node representing a plane for displaying messages to users.
    # Visibility will be toggled by StatusManager.
    self.coupling_plane_node = _loader.create_geometry_from_file('notification_geometry',
                                                                 'data/objects/plane.obj',
                                                                 'data/materials/CouplingPlane.gmd',
                                                                 avango.gua.LoaderFlags.LOAD_MATERIALS)
    self.coupling_plane_node.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.coupling_plane_node.Transform.value = avango.gua.make_scale_mat(0.6 * self.screens[0].Width.value, 0.1, 0.2 * self.screens[0].Height.value)

    self.coupling_plane_node.GroupNames.value = ["do_not_display_group", "platform_group_" + str(self.platform_id)]

    self.message_plane_node.Children.value.append(self.coupling_plane_node)

    ## @var decoupling_notifier
    # Geometry node representing a plane showing the color of a navigation that was recently decoupled.
    # Actual material and visibility will be toggled by StatusManager.
    self.decoupling_notifier = _loader.create_geometry_from_file('decoupling_notifier',
                                                                 'data/objects/plane.obj',
                                                                 'data/materials/AvatarWhiteShadeless.gmd',
                                                                 avango.gua.LoaderFlags.LOAD_MATERIALS)
    self.decoupling_notifier.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.decoupling_notifier.Transform.value =  avango.gua.make_trans_mat(0.0, 0.0, -0.2 * self.screens[0].Height.value) * \
                                                avango.gua.make_scale_mat(self.screens[0].Height.value * 0.1, self.screens[0].Height.value * 0.1, self.screens[0].Height.value * 0.1)

    self.decoupling_notifier.GroupNames.value = ["do_not_display_group", "platform_group_" + str(self.platform_id)]

    self.message_plane_node.Children.value.append(self.decoupling_notifier)


  ## Creates an overview of the user's current couplings in his or her field of view.
  def create_coupling_status_overview(self):
    
    _loader = avango.gua.nodes.GeometryLoader()
 
    # create transformation node
    ## @var coupling_status_node
    # Scenegraph transformation node for coupling icons in the user's field of view.
    self.coupling_status_node = avango.gua.nodes.TransformNode(Name = "coupling_status")
    self.coupling_status_node.GroupNames.value = ["display_group", "platform_group_" + str(self.platform_id)]

    # sets the necessary attributes for correct positioning of coupling status notifiers
    self.handle_coupling_status_attributes()

    # create icon indicating the own color
    ## @var own_color_geometry
    # Plane visible to the user indictating his or her own avatar color.
    self.own_color_geometry = _loader.create_geometry_from_file('own_notifier',
                                                                'data/objects/plane.obj',
                                                                'data/materials/' + self.avatar_material + 'Shadeless.gmd',
                                                                avango.gua.LoaderFlags.LOAD_MATERIALS)
    self.own_color_geometry.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.own_color_geometry.ShadowMode.value = avango.gua.ShadowMode.OFF

    self.coupling_status_node.Children.value.append(self.own_color_geometry)

    self.update_coupling_status_overview()

  ## Updates the Transform fields of coupling_status_node's children.
  # Can only be called after create_coupling_status_overview()
  def update_coupling_status_overview(self):

    # get all children nodes
    _children_nodes = self.coupling_status_node.Children.value

    # write transformation for all children with respect to y increments
    for i in range(0, len(_children_nodes)):
      _current_node = _children_nodes[i]

      # set translation of notifiers properly
      _current_trans = avango.gua.Vec3(self.start_trans)
      _current_trans.y += i * self.y_increment

      # make coupling notifiers smaller
      if i != 0:
        _scale = self.start_scale * 0.6
      else:
        _scale = self.start_scale

      _current_node.Transform.value = avango.gua.make_trans_mat(_current_trans) * \
                                      avango.gua.make_rot_mat(90, 1, 0, 0) * \
                                      avango.gua.make_scale_mat(_scale, _scale, _scale)

  ## Correctly places and appends the message plane node in and to the scenegraph.
  def handle_message_plane_node(self):
    self.message_plane_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0) * \
                                              avango.gua.make_rot_mat(90, 1, 0, 0)
    # append to primary screen
    self.screens[0].Children.value.append(self.message_plane_node)
    

  ## Handles all the specialized settings for the coupling status overview.
  def handle_coupling_status_attributes(self):
    self.coupling_status_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0)
    
    # append to primary screen
    self.screens[0].Children.value.append(self.coupling_status_node)

    ## @var start_trans
    # Translation of the first coupling status notifier (own color).
    self.start_trans = avango.gua.Vec3(-0.45 * self.screens[0].Width.value, 0.4 * self.screens[0].Height.value, 0.0)

    ## @var start_scale
    # Scaling of the first coupling status notifier (own color).
    self.start_scale = 0.05 * self.screens[0].Height.value
      
    ## @var y_increment
    # Y offset for all coupling status notifiers after the own color.
    self.y_increment = -self.start_scale


  ## Displays the coupling plane with the "Coupling" texture.
  def show_coupling_plane(self):

    # display coupling plane
    self.coupling_plane_node.Material.value = "data/materials/CouplingPlane.gmd"
    self.coupling_plane_node.GroupNames.value[0] = "display_group"

    # hide decoupling notifier if it isn't already
    self.decoupling_notifier.GroupNames.value[0] = "do_not_display_group"

  ## Hides the coupling plane.
  def hide_coupling_plane(self):
    self.coupling_plane_node.GroupNames.value[0] = "do_not_display_group"

  ## Displays coupling status notifiers for all navigations in COUPLED_NAVIGATION_LIST
  # @param COUPLED_NAVIGATION_LIST List of Navigation instances that are now coupled.
  def display_coupling(self, COUPLED_NAVIGATION_LIST):

    _loader = avango.gua.nodes.GeometryLoader()

    # check for every user that could be updated
    for _nav in COUPLED_NAVIGATION_LIST:
      if _nav.platform != self:
            
        # check if desired plane is not already present
        _new_node_needed = True

        for _node in self.coupling_status_node.Children.value:
          if (_node.Name.value == ('coupl_notifier_' + str(_nav.platform.platform_id))):
            _new_node_needed = False
            break

        # if the desired plane is not yet present, create and draw it
        if _new_node_needed:
          _plane = _loader.create_geometry_from_file('coupl_notifier_' + str(_nav.platform.platform_id),
                                                     'data/objects/plane.obj',
                                                     'data/materials/' +_nav.trace_material + 'Shadeless.gmd',
                                                     avango.gua.LoaderFlags.LOAD_MATERIALS)
          _plane.ShadowMode.value = avango.gua.ShadowMode.OFF
          self.NET_TRANS_NODE.distribute_object(_plane)
          self.coupling_status_node.Children.value.append(_plane)
      
      # update the offsets of the notifiers to have a proper display
      self.update_coupling_status_overview()

  ## Updates the nettrans node. Used to replace pseudo nettrans.
  # @param NET_TRANS_NODE The new nettrans node to be set.
  def update_nettrans_node(self, NET_TRANS_NODE):
    self.NET_TRANS_NODE = NET_TRANS_NODE

  ## Removes a platform indicator from the coupling display and shows a message to all other platforms.
  # @param NAVIGATION The Navigation instance to be removed from all couplings.
  # @param SHOW_NOTIFICATION Boolean saying if a notification should be displayed to all other platforms involved.
  def remove_from_coupling_display(self, NAVIGATION, SHOW_NOTIFICATION):

    _loader = avango.gua.nodes.GeometryLoader()

    # if the platform has a notifier for being coupled with NAVIGATION, remove this node from the scenegraph
    for _node in self.coupling_status_node.Children.value:
      if (_node.Name.value == ('coupl_notifier_' + str(NAVIGATION.platform.platform_id))):
        self.coupling_status_node.Children.value.remove(_node)
        self.update_coupling_status_overview()
        
        if SHOW_NOTIFICATION:
          # display notification that a user was decoupled
          self.coupling_plane_node.GroupNames.value[0] = "display_group"
          self.coupling_plane_node.Material.value = "data/materials/DecouplingPlane.gmd"

          # display color of decoupled navigation
          self.decoupling_notifier.GroupNames.value[0] = "display_group"
          self.decoupling_notifier.Material.value = 'data/materials/' + NAVIGATION.trace_material + 'Shadeless.gmd'

          # add user to watchlist such that the notifications are removed again after a certain
          # amount of time
          self.start_time = self.timer.Time.value

        break

  ## Evaluated every frame.
  def evaluate(self):

    # if a time update is required
    if self.start_time != None:
      
      # hide decoupling notifiers again after a certain amount of time
      if self.timer.Time.value - self.start_time > 3.0:

        # hide message plane and reset its material
        self.coupling_plane_node.GroupNames.value[0] = "do_not_display_group"

        # hide decoupling notifier
        self.decoupling_notifier.GroupNames.value[0] = "do_not_display_group"

        self.start_time = None