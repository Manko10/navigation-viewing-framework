#!/usr/bin/python

## @file
# Contains class RecorderPlayer

# import avango-guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

# import framework libraries
from ConsoleIO import *

# import python libraries
import time
import math
from os import listdir


class RecorderPlayer(avango.script.Script):

  # input fields
  sf_record_key = avango.SFBool()
  sf_save_key = avango.SFBool()
  sf_trigger_key = avango.SFBool()
  sf_play_mode_key = avango.SFBool()
  sf_record_mode_key = avango.SFBool()

  # constructor
  def __init__(self):
    self.super(RecorderPlayer).__init__()

  # constructor
  def my_constructor(self
                   , SCENEGRAPH_NODE
                   , NAVIGATION
                   , SF_RECORD_KEY
                   , SF_SAVE_KEY
                   , SF_TRIGGER_KEY
                   , SF_PLAY_MODE_CHANGE
                   , SF_RECORD_MODE_CHANGE):

    # references
    self.SCENEGRAPH_NODE = SCENEGRAPH_NODE
    self.NAVIGATION = NAVIGATION

    # variables
    self.recordings_list = []
    self.recording_list = []
    self.recorder_start_time = None
    self.in_keyframe_recording = False
    self.player_start_time = None
    self.play_index = None
    self.play_reset_flag = False
    self.recording_index = None

    self.record_mode = "ALL_FRAMES"
    #self.record_mode = "KEYFRAMES"

    self.play_mode = "CONTINUOUS"
    #self.play_mode = "DISCRETE"

    # init frame callbacks
    self.recorder_trigger = avango.script.nodes.Update(Callback = self.recorder_callback, Active = False)
    self.player_trigger = avango.script.nodes.Update(Callback = self.player_callback, Active = False)

    self.load_recorded_paths()

    # init field connections
    self.sf_record_key.connect_from(SF_RECORD_KEY)
    self.sf_save_key.connect_from(SF_SAVE_KEY)
    self.sf_trigger_key.connect_from(SF_TRIGGER_KEY)
    self.sf_play_mode_key.connect_from(SF_PLAY_MODE_CHANGE)
    self.sf_record_mode_key.connect_from(SF_RECORD_MODE_CHANGE)


  # callbacks
  @field_has_changed(sf_record_key)
  def sf_record_key_changed(self):

    if self.sf_record_key.value == True: # key pressed

      if self.recorder_trigger.Active.value == True:
        self.stop_recorder()

      else:
        self.start_recorder()


  @field_has_changed(sf_save_key)
  def sf_save_key_changed(self):

    if self.sf_save_key.value == True: # key pressed
      self.save_recording()

      print_message("Saving recording " + str(self.recording_index))

  @field_has_changed(sf_trigger_key)
  def sf_trigger_key_changed(self):

    if self.sf_trigger_key.value == True and \
       self.in_keyframe_recording:
      
      print "Capture keyframe"
      _time_step = time.time() - self.recorder_start_time
      self.record_parameters(_time_step)

  @field_has_changed(sf_play_mode_key)
  def sf_play_mode_key_changed(self):
    
    if self.sf_play_mode_key.value == True:

      if self.play_mode == "CONTINUOUS":
        self.play_mode = "DISCRETE"
        print_message("Play mode switched to DISCRETE.")
      else:
        self.play_mode = "CONTINUOUS"
        print_message("Play mode switched to CONTINUOUS.")

  @field_has_changed(sf_record_mode_key)
  def sf_record_mode_key_changed(self):
    
    if self.sf_record_mode_key.value == True:

      if self.record_mode == "ALL_FRAMES":
        self.record_mode = "KEYFRAMES"
        print_message("Record mode switched to KEYFRAMES.")
      else:
        self.record_mode = "ALL_FRAMES"
        print_message("Record mode switched to ALL_FRAMES.")


  def recorder_callback(self): # evaluated every frame when active

    if self.record_mode == "ALL_FRAMES":
      _time_step = time.time() - self.recorder_start_time
      self.record_parameters(_time_step)


  def player_callback(self): # evaluated every frame when active

    _time_step = time.time() - self.player_start_time

    self.play(_time_step)

    if self.play_reset_flag == True:
      self.stop_player()
      self.next_recording()
      self.start_player() # restart player

  # functions
  def play_key(self):

    if len(self.recording_list) > 0:

      if self.player_trigger.Active.value == True:
        self.stop_player()

      else:
        self.start_player()


  def next_recording(self):

    if self.recording_index != None:

      self.stop_player()
      self.stop_recorder() # evtl. stop recording

      self.recording_index += 1

      if self.recording_index > len(self.recordings_list) - 1:
        self.recording_index = 0

      self.recording_list = self.recordings_list[self.recording_index]

      self.reset_player()

      print_message("Switch to recording " + str(self.recording_index))


  def prior_recording(self):

    if self.recording_index != None:

      self.stop_player()
      self.stop_recorder() # evtl. stop recording

      self.recording_index -= 1

      if self.recording_index < 0:
        self.recording_index = len(self.recordings_list) - 1

      self.recording_list = self.recordings_list[self.recording_index]

      self.reset_player()

      print_message("Switch to recording " + str(self.recording_index))


  def load_recorded_paths(self):

    _entries = listdir("path_recordings/")

    for _entry in _entries:

      if _entry.endswith("~"):
        continue

      _path = "path_recordings/{0}".format(_entry)

      self.load_path_from_file(_path)


    if len(self.recordings_list) > 0:

      self.recording_list = self.recordings_list[0]
      self.recording_index = 0


  def load_path_from_file(self, PATH):

    try:
      _file = open(PATH,"r")
      _lines = _file.readlines()
      _file.close()

    except IOError:
      print_error("Error while loading path description file.", True)

    else: # file succesfully loaded

      # check if the recording is for handled scenegraph node
      if _lines[0].replace("\n", "") != self.SCENEGRAPH_NODE.Path.value:
        #print_warning("Return at " + _lines[0].replace("\n", ""))
        return
      
      # remove scenegraph path from list to parse
      _lines.pop(0)

      _recording_list = []

      for _line in _lines:
        _line = _line.split()

        _time = float(_line[0])
        _pos = avango.gua.Vec3(float(_line[1]), float(_line[2]), float(_line[3]))

        _quat	= avango.gua.make_rot_mat(float(_line[4]), float(_line[5]), float(_line[6]), float(_line[7])).get_rotate()
        #_quat	= avango.gua.Quat(float(_line[4]), avango.gua.Vec3(float(_line[5]), float(_line[6]), float(_line[7]))) # sucks

        _scale = avango.gua.Vec3(float(_line[8]), float(_line[9]), float(_line[10]))

        _recording_list.append( [_time, _pos, _quat, _scale] )

      self.recordings_list.append(_recording_list)


  def start_recorder(self):

    print_message("Start recording")

    self.stop_player()

    self.recording_list = [] # clear list

    self.recorder_start_time = time.time()
    self.last_keyframe_time = time.time()

    if self.record_mode == "KEYFRAMES":
      _time_step = time.time() - self.recorder_start_time
      self.record_parameters(_time_step)
      self.in_keyframe_recording = True

    self.recorder_trigger.Active.value = True # activate recorder callback


  def stop_recorder(self):

    if self.recorder_trigger.Active.value == True:

      if self.record_mode == "KEYFRAMES":
        _time_step = time.time() - self.recorder_start_time
        self.record_parameters(_time_step)
        self.in_keyframe_recording = True

      print_message("Stop recording of " + str(len(self.recording_list)) + " control points.")

      self.recorder_trigger.Active.value = False # deactivate recorder callback

      self.recorder_start_time = None
      self.in_keyframe_recording = False


  def save_recording(self):

    self.recording_index = len(self.recordings_list)

    _path = self.SCENEGRAPH_NODE.Path.value
    _path = _path.replace("/", "-")

    _name = "path_recordings/" + _path +"_path_" + str(self.recording_index)
    _file = open(_name,"w")

    _recording_list = []

    _file.write(self.SCENEGRAPH_NODE.Path.value + "\n")

    for _tupel in self.recording_list:
      _recording_list.append(_tupel)

      _time = _tupel[0]
      _pos = _tupel[1]
      _quat = _tupel[2]
      _scale = _tupel[3]

      _file.write("{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10}\n".format(
        _time, _pos.x, _pos.y, _pos.z, _quat.get_angle(), _quat.get_axis().x, _quat.get_axis().y, _quat.get_axis().z, _scale.x, _scale.y, _scale.z
      ))

    _file.close()

    self.recordings_list.append(_recording_list)


  def record_parameters(self, TIME_STEP):

    _mat = self.SCENEGRAPH_NODE.Transform.value

    self.recording_list.append( [TIME_STEP, _mat.get_translate(), _mat.get_rotate(), _mat.get_scale()] )


  def start_player(self):

    print_message("Start playing")

    self.play_index = 0
    self.play_reset_flag = False

    self.player_start_time = time.time()

    self.player_trigger.Active.value = True # activate player callback


  def stop_player(self):

    if self.player_trigger.Active.value == True:
      print_message("Stop playing")

      self.play_index = None

      self.player_trigger.Active.value = False # deactivate player callback


  def reset_player(self):

    if len(self.recording_list) > 0:
      print_message("Reset player")

      self.play_index = 0

      _values 	= self.recording_list[0]
      _pos		= _values[1]
      _quat		= _values[2]
      _scale  = _values[3]

      _mat =  avango.gua.make_trans_mat(_pos) * \
              avango.gua.make_rot_mat(_quat.get_angle(), _quat.get_axis().x, _quat.get_axis().y, _quat.get_axis().z) * \
              avango.gua.make_scale_mat(_scale)

      self.SCENEGRAPH_NODE.Transform.value = _mat



  def play(self, TIME_STEP):

    if self.play_index != None:

      _last_recorded_time_step = self.recording_list[-1][0]

      if TIME_STEP > _last_recorded_time_step:
        self.play_reset_flag = True # object has finished it's animation

      else:
        _time_step1 = self.recording_list[self.play_index][0]

        if TIME_STEP >= _time_step1:

          for _index in range(self.play_index, len(self.recording_list)):
            _time_step2 = self.recording_list[_index+1][0]
            _time_step1 = self.recording_list[_index][0]

            if TIME_STEP <= _time_step2:
              self.play_index = _index

              _factor = (TIME_STEP - _time_step1) / (_time_step2 - _time_step1)
              _factor = max(0.0,min(_factor,1.0))

              if self.play_mode == "DISCRETE":
                if _factor < 0.5:
                  _factor = 0.0
                else:
                  _factor = 1.0

              self.interpolate_between_frames(_factor) # interpolate position and orientation and scale

              if self.NAVIGATION != None and TIME_STEP < 0.1:
                self.NAVIGATION.trace.clear(self.NAVIGATION.get_current_world_pos())

              break


  def interpolate_between_frames(self, FACTOR):

    _tupel1 = self.recording_list[self.play_index]
    _pos1 = _tupel1[1]
    _quat1 = _tupel1[2]
    _scale1 = _tupel1[3]

    _tupel2 = self.recording_list[self.play_index+1]
    _pos2	= _tupel2[1]
    _quat2 = _tupel2[2]
    _scale2 = _tupel2[3]

    _new_pos = _pos1.lerp_to(_pos2, FACTOR)
    _new_quat = _quat1.slerp_to(_quat2, FACTOR)
    _new_scale = _scale1.lerp_to(_scale2, FACTOR)

    _new_mat =  avango.gua.make_trans_mat(_new_pos) * \
                avango.gua.make_rot_mat(_new_quat.get_angle(), _new_quat.get_axis().x, _new_quat.get_axis().y, _new_quat.get_axis().z) * \
                avango.gua.make_scale_mat(_new_scale)

    self.SCENEGRAPH_NODE.Transform.value = _new_mat

    if self.NAVIGATION != None:
      self.NAVIGATION.inputmapping.set_abs_mat(_new_mat)


class AnimationManager(avango.script.Script):

  # input fields
  sf_record = avango.SFBool()
  sf_save = avango.SFBool()
  sf_play = avango.SFBool()
  sf_next = avango.SFBool()
  sf_prior = avango.SFBool()
  sf_trigger = avango.SFBool()
  sf_play_mode_change = avango.SFBool()
  sf_record_mode_change = avango.SFBool()

  def __init__(self):
    self.super(AnimationManager).__init__()

  # constructor
  def my_constructor(self, SCENEGRAPH_NODE_LIST, NAVIGATION_LIST):
 
    # sensor
    self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
    self.keyboard_sensor.Station.value = "device-keyboard0"
        
    # init field connections

    self.sf_play.connect_from(self.keyboard_sensor.Button21) # F3
    
    self.sf_next.connect_from(self.keyboard_sensor.Button22) # F4
    self.sf_prior.connect_from(self.keyboard_sensor.Button23) # F5

    self.sf_record.connect_from(self.keyboard_sensor.Button24) # F6
    self.sf_save.connect_from(self.keyboard_sensor.Button25) # F7

    self.sf_trigger.connect_from(self.keyboard_sensor.Button20) # F2

    self.sf_play_mode_change.connect_from(self.keyboard_sensor.Button28) # F10
    self.sf_record_mode_change.connect_from(self.keyboard_sensor.Button29) # F11

    self.path_recorder_players = []

    for _i in range(len(SCENEGRAPH_NODE_LIST)):
      _path_recorder_player = RecorderPlayer()
      _path_recorder_player.my_constructor(SCENEGRAPH_NODE_LIST[_i]
                                             , NAVIGATION_LIST[_i]
                                             , self.sf_record
                                             , self.sf_save
                                             , self.sf_trigger
                                             , self.sf_play_mode_change
                                             , self.sf_record_mode_change)
      self.path_recorder_players.append(_path_recorder_player)

    self.always_evaluate(True)

  # callbacks
  @field_has_changed(sf_play)
  def sf_play_changed(self):

    if self.sf_play.value == True: # button pressed
      
      self.play_key()

  @field_has_changed(sf_next)
  def sf_next_changed(self):

    if self.sf_next.value == True: # button pressed

      self.path_recorder_players[0].next_recording()
      self.play_key()

  @field_has_changed(sf_prior)
  def sf_prior_changed(self):

    if self.sf_prior.value == True: # button pressed

      self.path_recorder_players[0].prior_recording()
      self.play_key()


  # functions
  def play_key(self):

    self.path_recorder_players[0].play_key()