#!/usr/bin/python

## @file
# Contains class RecorderPlayer

# import avango-guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

# import python libraries
import time
import math
from os import listdir


class RecorderPlayer(avango.script.Script):

  # input fields
  sf_record_key = avango.SFBool()
  sf_save_key = avango.SFBool()

  # constructor
  def __init__(self):
    self.super(RecorderPlayer).__init__()

  # constructor
  def my_constructor(self, SCENEGRAPH_NODE, SF_RECORD_KEY, SF_SAVE_KEY):

    # references
    self.SCENEGRAPH_NODE = SCENEGRAPH_NODE

    # variables
    self.recordings_list = []
    self.recording_list = []
    self.recorder_start_time = None
    self.player_start_time = None
    self.play_index = None
    self.play_reset_flag = False
    self.recording_index = None

    # init frame callbacks
    self.recorder_trigger = avango.script.nodes.Update(Callback = self.recorder_callback, Active = False)
    self.player_trigger = avango.script.nodes.Update(Callback = self.player_callback, Active = False)

    self.load_recorded_paths()

    # init field connections
    self.sf_record_key.connect_from(SF_RECORD_KEY)
    self.sf_save_key.connect_from(SF_SAVE_KEY)


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

      print "SAVING", self.recording_index


  def recorder_callback(self): # evaluated every frame when active

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

    #print "player", len(self.recording_list), self.play_index
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

      print "enable ", "recording ", self.recording_index


  def prior_recording(self):

    if self.recording_index != None:

      self.stop_player()
      self.stop_recorder() # evtl. stop recording

      self.recording_index -= 1

      if self.recording_index < 0:
        self.recording_index = len(self.recordings_list) - 1

      self.recording_list = self.recordings_list[self.recording_index]

      self.reset_player()

      print "enable ", "recording ", self.recording_index


  def load_recorded_paths(self):

    _entries = listdir("path_recordings/")

    for _entry in _entries:

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
      print "error while loading scene description file"

    else: # file succesfull loaded

      _recording_list = []

      for _line in _lines:
        _line = _line.split()

        _time = float(_line[0])
        _pos = avango.gua.Vec3(float(_line[1]), float(_line[2]), float(_line[3]))

        _quat	= avango.gua.make_rot_mat(float(_line[4]), float(_line[5]), float(_line[6]), float(_line[7])).get_rotate()
        #_quat	= avango.gua.Quat(float(_line[4]), avango.gua.Vec3(float(_line[5]), float(_line[6]), float(_line[7]))) # sucks

        _recording_list.append( [_time, _pos, _quat] )

      self.recordings_list.append(_recording_list)


  def start_recorder(self):

    print "RECORDING"

    self.stop_player()

    self.recording_list = [] # clear list

    self.recorder_start_time = time.time()

    self.recorder_trigger.Active.value = True # activate recorder callback


  def stop_recorder(self):

    if self.recorder_trigger.Active.value == True:
      # print "STOP RECORDING", len(self.recording_list)

      self.recorder_trigger.Active.value = False # deactivate recorder callback


  def save_recording(self):

    self.recording_index = len(self.recordings_list)

    _name = "path_recordings/path_" + str(self.recording_index)
    _file = open(_name,"w")

    _recording_list = []

    for _tupel in self.recording_list:
      _recording_list.append(_tupel)

      _time = _tupel[0]
      _pos = _tupel[1]
      _quat = _tupel[2]

      _file.write("{0} {1} {2} {3} {4} {5} {6} {7}\n".format(_time, _pos.x, _pos.y, _pos.z, _quat.get_angle(), _quat.get_axis().x, _quat.get_axis().y, _quat.get_axis().z))

    _file.close()

    self.recordings_list.append(_recording_list)


  def record_parameters(self, TIME_STEP):

    _mat = self.SCENEGRAPH_NODE.Transform.value

    self.recording_list.append( [TIME_STEP, _mat.get_translate(), _mat.get_rotate()] )


  def start_player(self):

    print "START PLAYING"

    self.play_index = 0
    self.play_reset_flag = False

    self.player_start_time = time.time()

    self.player_trigger.Active.value = True # activate player callback


  def stop_player(self):

    if self.player_trigger.Active.value == True:
      print "STOP_PLAYING"

      self.play_index = None

      self.player_trigger.Active.value = False # deactivate player callback


  def reset_player(self):

    if len(self.recording_list) > 0:
      print "RESET PLAYER"
      self.play_index = 0

      _values 	= self.recording_list[0]
      _pos		= _values[1]
      _quat		= _values[2]

      _mat = avango.gua.make_trans_mat(_pos) * \
              avango.gua.make_rot_mat(_quat.get_angle(), _quat.get_axis().x, _quat.get_axis().y, _quat.get_axis().z)

      self.SCENEGRAPH_NODE.Transform.value = _mat



  def play(self, TIME_STEP):

    if self.play_index != None:

      _last_recorded_time_step = self.recording_list[-1][0]

      if TIME_STEP > _last_recorded_time_step:
        self.play_reset_flag = True # object has finished it's animation

      else:
        _time_step1 = self.recording_list[self.play_index][0]
        #print "playing", _time_step1

        if TIME_STEP >= _time_step1:

          for _index in range(self.play_index, len(self.recording_list)):
            _time_step2 = self.recording_list[_index+1][0]
            #print "next timestep", _time_step2

            if TIME_STEP <= _time_step2:
              self.play_index = _index

              _factor = (TIME_STEP - _time_step1) / (_time_step2 - _time_step1)
              _factor = max(0.0,min(_factor,1.0))
              #print "FACTOR", _factor
              self.interpolate_between_frames(_factor) # interpolate position and orientation and scale

              break


  def interpolate_between_frames(self, FACTOR):

    _tupel1 = self.recording_list[self.play_index]
    _pos1 = _tupel1[1]
    _quat1 = _tupel1[2]

    _tupel2 = self.recording_list[self.play_index+1]
    _pos2	= _tupel2[1]
    _quat2 = _tupel2[2]

    _new_pos = _pos1.lerp_to(_pos2, FACTOR)
    _new_quat = _quat1.slerp_to(_quat2, FACTOR)

    _new_mat = avango.gua.make_trans_mat(_new_pos) * \
                avango.gua.make_rot_mat(_new_quat.get_angle(), _new_quat.get_axis().x, _new_quat.get_axis().y, _new_quat.get_axis().z)

    #print _new_mat.get_translate()
    self.SCENEGRAPH_NODE.Transform.value = _new_mat


class AnimationManager(avango.script.Script):

  # input fields
  sf_record = avango.SFBool()
  sf_save = avango.SFBool()
  sf_play = avango.SFBool()
  sf_next = avango.SFBool()
  sf_prior = avango.SFBool()
  sf_auto_animation = avango.SFBool()
  sf_roll_removal = avango.SFBool()

  def __init__(self):
    self.super(AnimationManager).__init__()

  # constructor
  def my_constructor(self, SCENEGRAPH_NODE_LIST):
    self.super(AnimationManager).__init__()

    # variables
    self.input_list = []
    self.input_length = 15

    self.enable_flag = True
    self.auto_animation_flag = False
    self.roll_removal_flag = True

    self.last_input_time = 0.0
    self.lf_time = time.time()
    self.global_scale = 1.0 # (inside/outside plane)
    
    # parameters
    self.auto_animation_threshold = 10.0 # in sec
    self.key_velocity = 0.04

    self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
    self.keyboard_sensor.Station.value = "device-keyboard0"
        
    # init field connections

    self.sf_play.connect_from(self.keyboard_sensor.Button19) # Y
    self.sf_auto_animation.connect_from(self.keyboard_sensor.Button20) # X
    self.sf_roll_removal.connect_from(self.keyboard_sensor.Button21) # C    
    
    self.sf_next.connect_from(self.keyboard_sensor.Button22) # V
    self.sf_prior.connect_from(self.keyboard_sensor.Button23) # B

    self.sf_record.connect_from(self.keyboard_sensor.Button24) # N
    self.sf_save.connect_from(self.keyboard_sensor.Button25) # M

    self.path_recorder_player = RecorderPlayer()
    self.path_recorder_player.my_constructor(SCENEGRAPH_NODE_LIST[0], self.sf_record, self.sf_save)

    self.always_evaluate(True)

  # callbacks
  @field_has_changed(sf_play)
  def sf_play_changed(self):

    if self.sf_play.value == True: # button pressed

      self.play_key()


  @field_has_changed(sf_record)
  def sf_record_changed(self):

    #print "record key", self.sf_record.value

    if self.sf_record.value == True: # button pressed

      if self.enable_flag == False:
        self.enable_flag = True


  @field_has_changed(sf_next)
  def sf_next_changed(self):

    if self.sf_next.value == True: # button pressed

      self.path_recorder_player.next_recording()

      self.last_input_time = time.time()

      self.enable_flag = True


  @field_has_changed(sf_prior)
  def sf_prior_changed(self):

    if self.sf_prior.value == True: # button pressed

      self.path_recorder_player.prior_recording()

      self.last_input_time = time.time()

      self.enable_flag = True


  @field_has_changed(sf_auto_animation)
  def sf_auto_animation_changed(self):
      
    if self.sf_auto_animation.value == True: # button pressed

      self.auto_animation_flag = not self.auto_animation_flag

      print "auto-animation enabled: ", self.roll_removal_flag

      if self.auto_animation_flag == False and self.path_recorder_player.player_trigger.Active.value == True: # disable auto animation
        print "stop auto animation"
        self.play_key()


  @field_has_changed(sf_roll_removal)
  def sf_roll_removal_changed(self):
      
    if self.sf_roll_removal.value == True: # button pressed

      self.roll_removal_flag = not self.roll_removal_flag
      
      print "roll disabled: ", self.roll_removal_flag


  def evaluate(self):
    pass
    '''
    if self.auto_animation_flag == True:

      if self.enable_flag == True:

        if (time.time() - self.last_input_time) > self.auto_animation_threshold and self.path_recorder_player.player_trigger.Active.value == False: # enable auto animation
          #print "start auto animation"
          self.play_key()
                                            
      else:
        pass
        #if _input_mat != avango.gua.make_identity_mat() and self.path_recorder_player.player_trigger.Active.value == True: # disable auto animation
        #  #print "stop auto animation"
        #  self.play_key()

    if self.enable_flag == True:

      if (time.time() - self.last_input_time) > self.auto_animation_threshold and self.path_recorder_player.player_trigger.Active.value == False: # enable auto animation
        #print "start auto animation"
        self.play_key()

    else:

      if _input_mat != avango.gua.make_identity_mat() and self.path_recorder_player.player_trigger.Active.value == True: # disable auto animation
        #print "stop auto animation"
        self.play_key()
    '''


  def filter_channel(self, VALUE, OFFSET, MIN, MAX, NEG_THRESHOLD, POS_THRESHOLD):

    VALUE = VALUE - OFFSET
    MIN = MIN - OFFSET
    MAX = MAX - OFFSET

    #print "+", VALUE, MAX, POS_THRESHOLD
    #print "-", VALUE, MIN, NEG_THRESHOLD

    if VALUE > 0:
      _pos = MAX * POS_THRESHOLD * 0.01

      if VALUE > _pos: # above positive threshold
        VALUE = min( (VALUE - _pos) / (MAX - _pos), 1.0) # normalize interval

      else: # beneath positive threshold
        VALUE = 0

    elif VALUE < 0:
      _neg = MIN * NEG_THRESHOLD * 0.01

      if VALUE < _neg:
        VALUE = max( (VALUE - _neg) / abs(MIN - _neg), -1.0)

      else: # above negative threshold
        VALUE = 0

    return VALUE


  def set_start_mat(self, MATRIX):

    self.OutTransform.value = MATRIX


  def play_key(self):

    self.path_recorder_player.play_key()

    if self.path_recorder_player.player_trigger.Active.value == True:
      self.enable_flag = False

    else:
      self.enable_flag = True

      self.last_input_time = time.time()
      
  
  def get_euler_angles(self, MATRIX):

    quat = MATRIX.get_rotate()
    qx = quat.x
    qy = quat.y
    qz = quat.z
    qw = quat.w
    
    sqx = qx * qx
    sqy = qy * qy
    sqz = qz * qz
    sqw = qw * qw
    
    unit = sqx + sqy + sqz + sqw # if normalised is one, otherwise is correction factor
    test = (qx * qy) + (qz * qw)
    
    if test > (0.49999 * unit): # singularity at north pole
      head = 2.0 * math.atan2(qx,qw)
      roll = math.pi/2.0
      pitch = 0.0
      
    elif test < (-0.49999 * unit): # singularity at south pole
      head = -2.0 * math.atan2(qx,qw)
      roll = math.pi/-2.0
      pitch = 0.0
    
    else:
      head = math.atan2(2.0 * qy * qw - 2.0 * qx * qz, 1.0 - 2.0 * sqy - 2.0 * sqz)
      roll = math.asin(2.0 * test)
      pitch = math.atan2(2.0 * qx * qw - 2.0 * qy * qz, 1.0 - 2.0 * sqx - 2.0 * sqz)
      
    if head < 0.0:
      head += 2.0 * math.pi
    
    return [head, pitch, roll]

