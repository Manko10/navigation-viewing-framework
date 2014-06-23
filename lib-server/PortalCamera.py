#!/usr/bin/python

## @file
# Contains class PortalCamera.

# import avango-guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

# import framework libraries
from Portal import *
from TrackingReader import *

# import python libraries
# ...

## A PortalCamera is a physical device to interactively caputure, view
# and manipulate Portal instances in the scene.
class PortalCamera(avango.script.Script):
 
  ## @var sf_tracking_mat
  # Tracking matrix of the PortalCamera within the platform coordinate system.
  sf_tracking_mat = avango.gua.SFMatrix4()

  ##
  #
  sf_border_mat = avango.gua.SFMatrix4()

  # button fields
  ## @var sf_focus_button
  # Boolean field to check if the focus button was pressed.
  sf_focus_button = avango.SFBool()

  ## @var sf_capture_button
  # Boolean field to check if the capture button was pressed.
  sf_capture_button = avango.SFBool()

  ## @var sf_next_rec_button
  # Boolean field to check if the next recording button was pressed.
  sf_next_rec_button = avango.SFBool()

  ## @var sf_prior_rec_button
  # Boolean field to check if the prior recording button was pressed.
  sf_prior_rec_button = avango.SFBool()

  ## @var sf_scale_up_button
  # Boolean field to check if the scale up button was pressed.
  sf_scale_up_button = avango.SFBool()

  ## @var sf_scale_down_button
  # Boolean field to check if the scale down button was pressed.
  sf_scale_down_button = avango.SFBool()

  ## @var sf_close_button
  # Boolean field to check if the close button was pressed.
  sf_close_button = avango.SFBool()

  ## @var sf_open_button
  # Boolean field to check if the open button was pressed.
  sf_open_button = avango.SFBool() 

  ## @var sf_delete_button
  # Boolean field to check if the delete button was pressed.
  sf_delete_button = avango.SFBool()

  ## @var sf_gallery_button
  # Boolean field to check if the gallery button was pressed.
  sf_gallery_button = avango.SFBool()

  ## @var sf_2D_mode_button
  # Boolean field to check if the 2D mode button was pressed.
  sf_2D_mode_button = avango.SFBool()

  ## @var sf_3D_mode_button
  # Boolean field to check if the 3D mode button was pressed.
  sf_3D_mode_button = avango.SFBool()

  ## @var sf_negative_parallax_on_button
  # Boolean field to check if the negative parallax on button was pressed.
  sf_negative_parallax_on_button = avango.SFBool()

  ## @var sf_negative_parallax_off_button
  # Boolean field to check if the negative parallax off button was pressed.
  sf_negative_parallax_off_button = avango.SFBool()


  ## Default constructor.
  def __init__(self):
    self.super(PortalCamera).__init__()

    ## @var captured_portals
    # List of Portal instances belonging to this PortalCamera.
    self.captured_portals = []

    ## @var current_portal
    # Portal instance which is currently displayed above the PortalCamera.
    self.current_portal = None

    ## @var portal_width
    # Width of the portals displayed in this PortalCamera.
    self.portal_width = 0.3

    ## @var portal_height
    # Height of the portals displayed in this PortalCamera.
    self.portal_height = 0.3

    ##
    #
    self.capture_viewing_mode = "3D"

    ##
    #
    self.capture_parallax_mode = "True"

    ##
    #
    self.gallery_activated = False

    ##
    #
    self.gallery_focus_portal_index = 0

    ##
    #
    self.gallery_magnification_factor = 1.5


  ## Custom constructor.
  # @param PORTAL_MANAGER Reference to the PortalManager used for Portal creation and management.
  # @param NAVIGATION Navigation instance to which this PortalCamera belongs to.
  # @param CAMERA_INPUT_NAME Name of the PortalCamera's input sensor as registered in daemon.
  # @param CAMERA_TRACKING_NAME Name of the PortalCamera's tracking target as registered in daemon.
  def my_constructor(self, PORTAL_MANAGER, NAVIGATION, CAMERA_INPUT_NAME, CAMERA_TRACKING_NAME):
    
    ## @var PORTAL_MANAGER
    # Reference to the PortalManager used for Portal creation and management.
    self.PORTAL_MANAGER = PORTAL_MANAGER

    ## @var NAVIGATION
    # Navigation instance to which this PortalCamera belongs to.
    self.NAVIGATION = NAVIGATION

    ## @var PLATFORM_NODE
    # Platform scenegraph node to which this PortalCamera should be appended to.
    self.PLATFORM_NODE = self.NAVIGATION.platform.platform_scale_transform_node

    ## @var device_sensor
    # Device sensor for the PortalCamera's button inputs.
    self.device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
    self.device_sensor.Station.value = CAMERA_INPUT_NAME

    # init field connections
    self.sf_focus_button.connect_from(self.device_sensor.Button0)
    self.sf_capture_button.connect_from(self.device_sensor.Button1)
    self.sf_next_rec_button.connect_from(self.device_sensor.Button5)
    self.sf_prior_rec_button.connect_from(self.device_sensor.Button4)
    self.sf_scale_up_button.connect_from(self.device_sensor.Button9)
    self.sf_scale_down_button.connect_from(self.device_sensor.Button10)
    self.sf_close_button.connect_from(self.device_sensor.Button2)
    self.sf_open_button.connect_from(self.device_sensor.Button3)
    self.sf_delete_button.connect_from(self.device_sensor.Button15)
    self.sf_gallery_button.connect_from(self.device_sensor.Button6)
    self.sf_2D_mode_button.connect_from(self.device_sensor.Button7)
    self.sf_3D_mode_button.connect_from(self.device_sensor.Button8)
    self.sf_negative_parallax_on_button.connect_from(self.device_sensor.Button12)
    self.sf_negative_parallax_off_button.connect_from(self.device_sensor.Button13)

    ## @var tracking_reader
    # TrackingTargetReader to process the tracking input of the PortalCamera.
    self.tracking_reader = TrackingTargetReader()
    self.tracking_reader.my_constructor(CAMERA_TRACKING_NAME)
    self.sf_tracking_mat.connect_from(self.tracking_reader.sf_abs_mat)

    _loader = avango.gua.nodes.TriMeshLoader()

    ## @var camera_frame
    # Geometry node containing the PortalCamera's portal frame.
    self.camera_frame = _loader.create_geometry_from_file("portal_camera", "data/objects/screen.obj", "data/materials/ShadelessRed.gmd", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
    self.camera_frame.ShadowMode.value = avango.gua.ShadowMode.OFF
    self.camera_frame.GroupNames.value = ["do_not_display_group"]
    self.PLATFORM_NODE.Children.value.append(self.camera_frame)

    self.camera_frame.Transform.connect_from(self.sf_border_mat)

    ##
    #
    self.viewing_mode_indicator = _loader.create_geometry_from_file('viewing_mode_indicator',
                                                                    'data/objects/plane.obj',
                                                                    'data/materials/CameraMode' + self.capture_viewing_mode + '.gmd',
                                                                    avango.gua.LoaderFlags.LOAD_MATERIALS)
    self.viewing_mode_indicator.Transform.value = avango.gua.make_trans_mat(-self.portal_width * 1.5, self.portal_height * 1.5, 0.0) * \
                                                  avango.gua.make_rot_mat(90, 1, 0, 0) * \
                                                  avango.gua.make_scale_mat(self.portal_height * 0.3, 1.0, self.portal_height * 0.3)
    self.viewing_mode_indicator.ShadowMode.value = avango.gua.ShadowMode.OFF

    self.camera_frame.Children.value.append(self.viewing_mode_indicator)

    ##
    #
    self.last_open_portal_index = None

    ##
    #
    self.start_drag_portal_mat = None

    ##
    #
    self.start_drag_scene_mat = None

    # set evaluation policy
    self.always_evaluate(True)

  ## Evaluated every frame.
  def evaluate(self):

    # update portal and camera frame matrix
    self.sf_border_mat.value  = self.tracking_reader.sf_abs_mat.value * \
                                avango.gua.make_trans_mat(0.0, self.portal_height/2, 0.0) * \
                                avango.gua.make_scale_mat(self.portal_width, self.portal_height, 1.0)

    # always hide red camera frame when a portal is displayed
    if self.current_portal != None:
      self.camera_frame.GroupNames.value = ["do_not_display_group"]

    # apply scale changes 
    if self.sf_scale_up_button.value == True and \
       self.current_portal != None:
      
      self.current_portal.set_scale(self.current_portal.scale * 0.985)
      
    if self.sf_scale_down_button.value == True and \
       self.current_portal != None:

      self.current_portal.set_scale(self.current_portal.scale * 1.015)


    # update matrices in drag mode
    if self.start_drag_portal_mat != None and self.start_drag_scene_mat != None:

      _current_portal_mat = self.tracking_reader.sf_abs_mat.value
      _diff_mat = _current_portal_mat * avango.gua.make_inverse_mat(self.start_drag_portal_mat)
      _diff_mat = avango.gua.make_trans_mat(_diff_mat.get_translate() * self.current_portal.scale) * \
                  avango.gua.make_rot_mat(_diff_mat.get_rotate())
      self.current_portal.scene_matrix_node.Transform.value = _diff_mat * self.start_drag_scene_mat

    # update matrices in gallery mode
    if self.gallery_activated:

      if len(self.captured_portals) == 0:
        self.gallery_activated = False
        return

      _i = -self.gallery_focus_portal_index
      self.current_portal = self.captured_portals[self.gallery_focus_portal_index]

      for _portal in self.captured_portals:
        _station_mat = self.NAVIGATION.device.sf_station_mat.value
        _station_vec = _station_mat.get_translate()

        _modified_station_mat = avango.gua.make_trans_mat(_station_vec.x + self.gallery_magnification_factor * (self.portal_width + 0.05) * _i, _station_vec.y + self.gallery_magnification_factor * self.portal_height, _station_vec.z)

        _matrix = self.NAVIGATION.platform.platform_scale_transform_node.WorldTransform.value * \
                  avango.gua.make_trans_mat(_station_vec) * \
                  avango.gua.make_rot_mat(_station_mat.get_rotate()) * \
                  avango.gua.make_trans_mat(_station_vec * -1) * \
                  _modified_station_mat * \
                  avango.gua.make_scale_mat(self.gallery_magnification_factor * self.portal_width, self.gallery_magnification_factor * self.portal_height, 1.0)

        _portal.portal_matrix_node.Transform.disconnect()
        _portal.portal_matrix_node.Transform.value = _matrix
        _portal.set_visibility(True)
        _i += 1

      # check for camera hitting portal

      _camera_vec = self.camera_frame.WorldTransform.value.get_translate()

      for _portal in self.captured_portals:

        _portal_vec = _portal.portal_matrix_node.WorldTransform.value.get_translate()

        if _camera_vec.x > _portal_vec.x - (self.portal_width/2) and \
           _camera_vec.x < _portal_vec.x + (self.portal_width/2) and \
           _camera_vec.y > _portal_vec.y - 0.1 and \
           _camera_vec.y < _portal_vec.y + 0.1 and \
           _camera_vec.z > _portal_vec.z - 0.05 and \
           _camera_vec.z < _portal_vec.z + 0.05:

          for _portal_2 in self.captured_portals:
            
            if _portal_2 != _portal:
              _portal_2.set_visibility(False)
            
            _portal_2.portal_matrix_node.Transform.connect_from(self.camera_frame.WorldTransform)

          _grabbed_portal_index = self.captured_portals.index(_portal)
          self.last_open_portal_index = _grabbed_portal_index
          self.gallery_activated = False
          self.current_portal = _portal
          return

  ## Called whenever sf_focus_button changes.
  @field_has_changed(sf_focus_button)
  def sf_focus_button_changed(self):

    if self.sf_focus_button.value == True:

      try:
        self.camera_frame.GroupNames.value = []
      except:
        pass

    else:

      try:
        self.camera_frame.GroupNames.value = ["do_not_display_group"]
      except:
        pass

  ## Called whenever sf_capture_button changes.
  @field_has_changed(sf_capture_button)
  def sf_capture_button_changed(self):
    if self.sf_capture_button.value == True:

      if self.current_portal == None:
        _portal = self.PORTAL_MANAGER.add_portal(self.camera_frame.WorldTransform.value, 
                                                 self.camera_frame.WorldTransform.value,
                                                 1.0,
                                                 1.0,
                                                 self.capture_viewing_mode,
                                                 "PERSPECTIVE",
                                                 self.capture_parallax_mode,
                                                 "data/materials/ShadelessBlue.gmd")
        self.captured_portals.append(_portal)
        _portal.portal_matrix_node.Transform.connect_from(self.camera_frame.WorldTransform)
        self.current_portal = _portal

      else:

        self.start_drag_portal_mat = self.tracking_reader.sf_abs_mat.value
        self.start_drag_scene_mat = self.current_portal.scene_matrix_node.Transform.value

    # capture button released
    else:

      self.start_drag_portal_mat = None
      self.start_drag_scene_mat = None

  ## Called whenever sf_next_rec_button changes.
  @field_has_changed(sf_next_rec_button)
  def sf_next_rec_button_changed(self):
    if self.sf_next_rec_button.value == True:

      if self.gallery_activated:
        self.gallery_focus_portal_index = min(self.gallery_focus_portal_index + 1, len(self.captured_portals) - 1)
        return
      
      if self.current_portal != None:
        self.current_portal.set_visibility(False)

        _current_index = self.captured_portals.index(self.current_portal)
        _current_index += 1
        _current_index = _current_index % len(self.captured_portals)

        self.current_portal = self.captured_portals[_current_index]
        self.current_portal.set_visibility(True)


  ## Called whenever sf_prior_rec_button changes.
  @field_has_changed(sf_prior_rec_button)
  def sf_prior_rec_button_changed(self):
    if self.sf_prior_rec_button.value == True:

      if self.gallery_activated:
        self.gallery_focus_portal_index = max(self.gallery_focus_portal_index - 1, 0)
        return
      
      if self.current_portal != None:
        self.current_portal.set_visibility(False)

        _current_index = self.captured_portals.index(self.current_portal)
        _current_index -= 1
        _current_index = _current_index % len(self.captured_portals)

        self.current_portal = self.captured_portals[_current_index]
        self.current_portal.set_visibility(True)

  ## Called whenever sf_close_button changes.
  @field_has_changed(sf_close_button)
  def sf_close_button_changed(self):
    if self.sf_close_button.value == True:

      if self.current_portal != None:
        self.current_portal.set_visibility(False)
        self.last_open_portal_index = self.captured_portals.index(self.current_portal)
        self.current_portal = None

  ## Called whenever sf_open_button changes.
  @field_has_changed(sf_open_button)
  def sf_open_button_changed(self):
    if self.sf_open_button.value == True:

      if self.current_portal == None and len(self.captured_portals) > 0:
       self.current_portal = self.captured_portals[self.last_open_portal_index]
       self.current_portal.set_visibility(True)

  ## Called whenever sf_delete_button changes.
  @field_has_changed(sf_delete_button)
  def sf_delete_button_changed(self):
    if self.sf_delete_button.value == True:

      if self.current_portal != None:
        _portal_to_delete = self.current_portal
        self.gallery_focus_portal_index = max(self.captured_portals.index(_portal_to_delete) - 1, 0)
        self.last_open_portal_index = max(self.captured_portals.index(_portal_to_delete) - 1, 0)

        self.captured_portals.remove(_portal_to_delete)
        self.PORTAL_MANAGER.remove_portal(_portal_to_delete.id)
        self.current_portal = None

  ## Called whenever sf_gallery_button changes.
  @field_has_changed(sf_gallery_button)
  def sf_gallery_button_changed(self):
    if self.sf_gallery_button.value == True:

      if self.gallery_activated == False:
        self.gallery_activated = True
      
      else:
        self.gallery_activated = False
        self.last_open_portal_index = self.gallery_focus_portal_index
        self.current_portal = None

        for _portal in self.captured_portals:
          _portal.set_visibility(False)
          _portal.portal_matrix_node.Transform.connect_from(self.camera_frame.WorldTransform)

      
  ## Called whenever sf_2D_mode_button changes.
  @field_has_changed(sf_2D_mode_button)
  def sf_2D_mode_button_changed(self):
    if self.sf_2D_mode_button.value == True:
      
      if self.current_portal != None:
        if self.current_portal.viewing_mode == "3D":
          self.current_portal.switch_viewing_mode()
      else:
        self.capture_viewing_mode = "2D"
        self.viewing_mode_indicator.Material.value = 'data/materials/CameraMode2D.gmd'

  ## Called whenever sf_3D_mode_button changes.
  @field_has_changed(sf_3D_mode_button)
  def sf_3D_mode_button_changed(self):
    if self.sf_3D_mode_button.value == True:
      
      if self.current_portal != None:
        if self.current_portal.viewing_mode == "2D":
          self.current_portal.switch_viewing_mode()
      else:
        self.capture_viewing_mode = "3D"
        self.viewing_mode_indicator.Material.value = 'data/materials/CameraMode3D.gmd'


  ## Called whenever sf_negative_parallax_on_button changes.
  @field_has_changed(sf_negative_parallax_on_button)
  def sf_negative_parallax_on_button_changed(self):
    if self.sf_negative_parallax_on_button.value == True:
      
      if self.current_portal != None:
        if self.current_portal.negative_parallax == "False":
          self.current_portal.switch_negative_parallax()
      else:
        self.capture_parallax_mode = "True"


  ## Called whenever sf_negative_parallax_off_button changes.
  @field_has_changed(sf_negative_parallax_off_button)
  def sf_negative_parallax_off_button_changed(self):
    if self.sf_negative_parallax_off_button.value == True:
      
      if self.current_portal != None:
        if self.current_portal.negative_parallax == "True":
          self.current_portal.switch_negative_parallax()
      else:
        self.capture_parallax_mode = "False"