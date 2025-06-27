from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random
import math
import time
import sys


mouse_x = 0
mouse_y = 0


# Game state
game_state = {
  "level": 1,
  "lives": 3,
  "score": 0,
  "meteors_destroyed": 0,
  "meteor_speed": 0.7,
  "game_over": False,
  "last_meteor_spawn": time.time(),
  "meteors_destroyed_this_jump": 0,
  "camera_mode": "third_person",
  "meteor_wave_active": False,
  "paused_time": 0,
  "planets_paused": False,
  "last_destroyed_pos": None,
  "showing_landing_info": False,
  "landing_info_time": 0,
  "current_planet_info": None,
  "boss_active": False,
  "boss_health": 0
}
# planets: name, color, radius, orbit_radius, speed, has_moons, moon_count
planets = [
  ("Mercury", (0.8, 0.8, 0.8), 8, 150, 5, False, 0),
  ("Venus", (1.0, 0.8, 0.4), 12, 250, 4, False, 0),
  ("Earth", (0.2, 0.5, 1.0), 13, 370, 3, True, 1),
  ("Mars", (1.0, 0.3, 0.2), 11, 500, 2.5, True, 2),
  ("Jupiter", (1.0, 0.9, 0.6), 25, 650, 2, True, 4),
  ("Saturn", (1.0, 0.8, 0.5), 22, 800, 1.5, True, 6),
  ("Uranus", (0.5, 1.0, 1.0), 18, 950, 1, True, 2),
  ("Neptune", (0.3, 0.4, 1.0), 18, 1050, 0.8, True, 2)
]
star_positions = []
meteors = []
MAX_METEORS = 5


spaceship = {
  "x": planets[2][3] , # Start at earth
  "y": 0,
  "z": 30,
  "jumping": False,
  "target_index": 2,
  "speed": 0.5,
  "attached_to_planet": True,
  "vertical_offset": 0,
  "max_vertical_offset": 50,
  "jump_start_time": 0,
  "jump_duration": 12.0,
  "current_jump_progress": 0.0
}
# Camera
camera_radius = 1300
camera_angle_deg = 45
camera_height = 800
fovY = 70


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
  glDisable(GL_LIGHTING)
  glMatrixMode(GL_PROJECTION)
  glPushMatrix()
  glLoadIdentity()
  gluOrtho2D(0, 1200, 0, 900)
  glMatrixMode(GL_MODELVIEW)
  glPushMatrix()
  glLoadIdentity()
  glColor3f(1, 1, 1)
  glRasterPos2f(x, y)
  for ch in text:
      glutBitmapCharacter(font, ord(ch))
  glPopMatrix()
  glMatrixMode(GL_PROJECTION)
  glPopMatrix()
  glMatrixMode(GL_MODELVIEW)
  glEnable(GL_LIGHTING)


def generateStars(count=400):
  global star_positions
  star_positions = [
      (
          random.uniform(-900, 900),
          random.uniform(-900, 900),
          random.uniform(-900, 900)
      ) for _ in range(count)
  ]


def drawSpaceship():
   glPushMatrix()
   glTranslatef(spaceship["x"], spaceship["y"], spaceship["z"] + spaceship["vertical_offset"])


   if spaceship["jumping"]:
       target_planet = planets[spaceship["target_index"]]
       _, _, _, orbit_radius, speed, _, _ = target_planet
       angle = math.atan2(spaceship["y"], spaceship["x"])
       glRotatef(math.degrees(angle), 0, 0, 1)


   glColor3f(1.0, 0.1 ,0.1)  # red
   glRotatef(1, 90, 0, 0)
   glutSolidCylinder(5, 15, 20, 5)


   glColor3f(0.6, 0.6, 0.6)  # Gray
   glTranslatef(0, 0, 15)
   glutSolidCone(5, 15, 20, 5)
   glPopMatrix()


def drawStars():
  glPointSize(1.5)
  glBegin(GL_POINTS)
  glColor3f(1, 1, 1)
  for x, y, z in star_positions:
      glVertex3f(x, y, z)
  glEnd()


def setupLighting():
  glEnable(GL_LIGHTING)
  glEnable(GL_LIGHT0)


  light_position = [1.0, 1.0, 1.0, 0.0]
  ambient_light = [0.3, 0.3, 0.3, 1.0]
  diffuse_light = [1.0, 1.0, 1.0, 1.0]


  glLightfv(GL_LIGHT0, GL_POSITION, light_position)
  glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
  glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse_light)




def draw_solar_system():
   glPushMatrix()  # Push for solar system
   # Sun
   glColor3f(1.0, 0.9, 0.2)
   glutSolidSphere(30, 30, 30)


   current_time = time.time() - start_time
   if game_state["planets_paused"]:
       current_time = game_state["paused_time"]


   # orbits (no matrix needed)
   glColor3f(0.3, 0.3, 0.5)
   for planet in planets:
       _, _, _, orbit_radius, _, _, _ = planet
       glBegin(GL_LINE_LOOP)
       for angle in range(0, 360, 5):
           rad = math.radians(angle)
           x = orbit_radius * math.cos(rad)
           y = orbit_radius * math.sin(rad)
           glVertex3f(x, y, 0)
       glEnd()


   # Planets + Moons
   for i, (name, color, radius, orbit_radius, speed, has_moons, moon_count) in enumerate(planets):
       glPushMatrix()  # For planet


       angle = (current_time * speed) % 360
       glRotatef(angle, 0, 0, 1)
       glTranslatef(orbit_radius, 0, 0)
       glColor3fv(color)
       glutSolidSphere(radius, 20, 20)


       # Moons
       if has_moons:
           for j in range(moon_count):
               glPushMatrix()  # For moon
               moon_orbit = radius + 8 + j * 8
               moon_angle = (current_time * (speed * 3 + j * 2)) % 360
               glRotatef(moon_angle, 0, 0, 1)
               glTranslatef(moon_orbit, 0, 0)
               glColor3f(0.8, 0.8, 0.8)
               glutSolidSphere(3, 10, 10)
               glPopMatrix()  # For moon


       glPopMatrix()  # For planet


   glPopMatrix()  # For solar system




def draw_landing_info():
   if not game_state["showing_landing_info"]:
       return


   planet_info = game_state["current_planet_info"]
   if not planet_info:
       return


   planet_name = planet_info[0]
   planet_facts = {
       "Mercury": ["Brace for extreme heat and cold!",
                   "Surface temps swing from 430°C to -180°C. No atmosphere to slow descent—watch your thrusters!",
                   "Closest to the Sun; solar radiation is intense."],
       "Venus": ["Warning: Hostile environment detected.",
                 "Crushing pressure 92x Earth and acid clouds, suit integrity critical!",
                 "Thick CO2 atmosphere.Surface temp steady at 475°C. No GPS radar only."],
       "Earth": ["Welcome home, Commander", "Optimal gravity and breathable atmosphere detected",
                 "Environmental systems synced—enjoy the view"],
       "Mars": ["Red terrain ahead—initiate dust shields", "Thin CO₂ atmosphere; oxygen supply required.",
                "Evidence of water ice detected, potential for base camp."],
       "Jupiter": ["Danger: No solid surface, abort landing!", "Gas giant with crushing pressure and violent storms.",
                   "Magnetic field interference, navigation compromised."],
       "Saturn": ["Spectacular rings visible engage photo mode", "Another gas giant—landing impossible.",
                  "High wind speeds and dense atmosphere; use probes only."],
       "Uranus": ["Entering tilted atmosphere adjust pitch.",
                  "Ice giant with methane-rich clouds—expect blue-green hues.",
                  "Frigid temps around -224°C. Systems may lag."],
       "Neptune": ["Severe winds ahead stabilizers to max.", "Dark, cold, and supersonic winds over 2,000 km/h.",
                   "did you know neptune was discovered mathametically?!"]
   }


   # Save current state
   glMatrixMode(GL_PROJECTION)
   glPushMatrix()
   glLoadIdentity()
   gluOrtho2D(0, 1000, 0, 800)


   glMatrixMode(GL_MODELVIEW)
   glPushMatrix()
   glLoadIdentity()


   # Disable features for 2D rendering
   glDisable(GL_LIGHTING)
   glDisable(GL_DEPTH_TEST)
   glEnable(GL_BLEND)
   glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


   # Draw background
   glColor4f(0.1, 0.1, 0.2, 0.7)
   glBegin(GL_QUADS)
   glVertex2f(50, 580)
   glVertex2f(450, 580)
   glVertex2f(450, 380)
   glVertex2f(50, 380)
   glEnd()


   # Draw text
   y_pos = 580
   draw_text(70, y_pos, f"You've landed on {planet_name}!")
   for i, fact in enumerate(planet_facts.get(planet_name, [])):
       draw_text(70, 550 - (i * 30), fact)


   # Restore state
   glDisable(GL_BLEND)
   glEnable(GL_DEPTH_TEST)
   glEnable(GL_LIGHTING)
   glMatrixMode(GL_PROJECTION)
   glPopMatrix()
   glMatrixMode(GL_MODELVIEW)
   glPopMatrix()




def draw_meteors():
   for meteor in meteors:
       glPushMatrix()
       glTranslatef(*meteor['pos'])
       if meteor.get('is_boss', False):
           pulse = math.sin(time.time() * 5) * 0.1 + 1.0
           glColor3f(0.8, 0.2, 0.8)
           glutSolidSphere(meteor['size'] * pulse, 32, 32)
       else:
           glColor3f(0.8, 0.4, 0.1)
           glutSolidSphere(meteor['size'], 10, 10)
       glPopMatrix()  # Move this outside the else block


def updateSpaceship():
  global start_time
  if game_state["game_over"]:
      return
  if spaceship["jumping"]:
      target_planet = planets[spaceship["target_index"]]
      _, _, _, orbit_radius, speed, _, _ = target_planet


      angle = (game_state["paused_time"] * speed) % 360
      angle_rad = math.radians(angle)
      tx = orbit_radius * math.cos(angle_rad)
      ty = orbit_radius * math.sin(angle_rad)
      tz = 30


      # Calculate starting position (current planet)
      current_planet = planets[(spaceship["target_index"] - 1) % len(planets)]
      _, _, _, current_orbit, current_speed, _, _ = current_planet
      current_angle = (game_state["paused_time"] * current_speed) % 360
      current_angle_rad = math.radians(current_angle)
      sx = current_orbit * math.cos(current_angle_rad)
      sy = current_orbit * math.sin(current_angle_rad)
      sz = 30


      # Calculate progress (0 to 1) based on time since jump started
      jump_time = time.time() - spaceship["jump_start_time"]
      progress = min(jump_time / 12.0, 1.0)  # 8 second journey


      game_state["forward_direction"] = [
          tx - sx,
          ty - sy,
          0
      ]
      # Move along a curved path between planets
      if progress < 1.0:
          spaceship["x"] = sx + (tx - sx) * progress
          spaceship["y"] = sy + (ty - sy) * progress
          spaceship["z"] = sz + (tz - sz) * progress + math.sin(progress * math.pi) * 100


          # Small random meteor spawn chance during mid-jump
          if 0.3 < progress < 0.7 and random.random() < 0.02 and len(meteors) < 3:
              spawn_meteor()
      else:
          complete_jump()


  elif spaceship["attached_to_planet"]:
      # Follow planet's orbit in third-person view
      planet = planets[spaceship["target_index"]]
      _, _, _, orbit_radius, speed, _, _ = planet
      current_time = time.time() - start_time
      angle = current_time * speed % 360
      angle_rad = math.radians(angle)


      spaceship["x"] = orbit_radius * math.cos(angle_rad)
      spaceship["y"] = orbit_radius * math.sin(angle_rad)
      spaceship["z"] = 15




def complete_jump():
       # Check if we've hit enough meteors
       if game_state.get("meteors_destroyed_this_jump", 0) < MAX_METEORS:
           game_over()
           return


       # jump completion
       spaceship["jumping"] = False
       spaceship["attached_to_planet"] = True
       game_state["showing_landing_info"] = True
       game_state["landing_info_time"] = time.time()
       game_state["current_planet_info"] = planets[spaceship["target_index"]]
       game_state["meteor_speed"] += 0.1
       game_state["meteor_wave_active"] = False
       game_state["meteors_destroyed_this_jump"] = 0  # Reset for next jump
       game_state["planets_paused"] = False
       meteors.clear()
       game_state["level"] += 1
       game_state["boss_active"] = False


       if spaceship["target_index"] == 1:
           game_state["visited_all_planets"] = True
       game_state["camera_mode"] = "third_person"


def spawn_meteor():
   if not spaceship["jumping"]:
       return
       # Check if we should spawn a boss (every 2 levels)
   if game_state["level"] % 2 == 0 and not game_state["boss_active"] and len(meteors) == 0:
           game_state["boss_active"] = True
           game_state["boss_health"] = 5  # Needs 5 clicks


           # Position boss meteor in the center of the screen
           meteors.append({
               'pos': [
                   spaceship["x"],
                   spaceship["y"],
                   spaceship["z"] + 100
               ],
               'dir': [0, 0, -0.02
               ],
               'size': 20,
               'is_boss': True
           })
           return


   spawn_distance = 300 + random.uniform(0, 200)
   spread = 120


   target_planet = planets[spaceship["target_index"]]
   _, _, _, orbit_radius, speed, _, _ = target_planet
   angle = (game_state["paused_time"] * speed) % 360
   angle_rad = math.radians(angle)
   tx = orbit_radius * math.cos(angle_rad)
   ty = orbit_radius * math.sin(angle_rad)


   forward_dir = [
       tx - spaceship["x"],
       ty - spaceship["y"],
       0
   ]
   forward_length = math.sqrt(forward_dir[0] ** 2 + forward_dir[1] ** 2)
   if forward_length > 0:
       forward_dir = [d / forward_length for d in forward_dir]




   pos = [
       spaceship["x"] + forward_dir[0] * spawn_distance + random.uniform(-spread, spread),
       spaceship["y"] + forward_dir[1] * spawn_distance + random.uniform(-spread, spread),
       spaceship["z"] + random.uniform(-40, 40)
   ]


   dir = [
       -forward_dir[0] * 0.3 + random.uniform(-0.05, 0.05),
       -forward_dir[1] * 0.3 + random.uniform(-0.05, 0.05),
       (spaceship["z"] - pos[2]) / 800
   ]


   meteors.append({
       'pos': pos,
       'dir': dir,
       'size': random.uniform(4, 7) ,
       'is_boss': False
   })


def update_meteors():
   global game_state
   current_time = time.time()


   meteors[:] = [m for m in meteors if
                 (m['pos'][0] - spaceship["x"]) ** 2 +
                 (m['pos'][1] - spaceship["y"]) ** 2 < 800 ** 2]
   # Check for collisions
   for meteor in meteors[:]:
       # Calculate distance to spaceship
       distance = math.sqrt(
           (meteor['pos'][0] - spaceship["x"]) ** 2 +
           (meteor['pos'][1] - spaceship["y"]) ** 2 +
           (meteor['pos'][2] - spaceship["z"]) ** 2
       )


       if distance < (meteor['size'] + 20):
           meteors.remove(meteor)
           game_state["lives"] -= 1
           if game_state["lives"] <= 0:
               game_over()
           break  # Only process one collision per frame
   for meteor in meteors:
       if meteor.get('is_boss', False):
           speed_factor = 0.5
       else:
           speed_factor = game_state["meteor_speed"]
       meteor['pos'][0] += meteor['dir'][0] * speed_factor
       meteor['pos'][1] += meteor['dir'][1] * speed_factor
       meteor['pos'][2] += meteor['dir'][2] * (speed_factor * 0.7)


   # Spawn boss only once when conditions are met
   if (game_state["level"] % 2 == 0 and
           not game_state["boss_active"] and
           len(meteors) == 0 and
           spaceship["jumping"] and
           game_state["meteor_wave_active"]):
       spawn_meteor()
       game_state["boss_active"] = True
       game_state["last_meteor_spawn"] = current_time
       return  # Skip normal meteor


   if (spaceship["jumping"] and
           game_state["meteor_wave_active"] and
           len(meteors) < 5 and
           current_time - game_state.get("last_meteor_spawn", 0) > 1.5):  # Spawn interval


       jump_progress = (current_time - spaceship["jump_start_time"]) / spaceship["jump_duration"]


       if 0.1 < jump_progress < 0.9:
           spawn_meteor()
           # 50% chance to spawn second meteor
           if random.random() < 0.5:
               spawn_meteor()
           game_state["last_meteor_spawn"] = current_time




def destroy_meteor(x, y):
   viewport = glGetIntegerv(GL_VIEWPORT)
   modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
   projection = glGetDoublev(GL_PROJECTION_MATRIX)


   winX = x
   winY = viewport[3] - y  # Flip y coordinate


   for meteor in meteors[:]:
       meteor_win = gluProject(
           meteor['pos'][0], meteor['pos'][1], meteor['pos'][2],
           modelview, projection, viewport
       )


       if meteor_win:
           # Keep your original hit radius logic but add boss detection
           hit_radius = 200 if meteor.get('is_boss', False) else 100
           distance = math.sqrt(
               (winX - meteor_win[0]) ** 2 +
               (winY - meteor_win[1]) ** 2
           )


           if distance < hit_radius:
               game_state["last_destroyed_pos"] = meteor['pos']


               if meteor.get('is_boss', False):
                   # Boss meteor logic from friend's code
                   game_state["boss_health"] = game_state.get("boss_health", 3) - 1


                   if game_state["boss_health"] <= 0:
                       meteors.remove(meteor)
                       game_state["boss_active"] = False
                       game_state["score"] += 50
                       game_state["meteors_destroyed"] += 1
                       game_state["meteors_destroyed_this_jump"] += 1
                       return True
               else:
                   # Your original meteor destruction logic
                   meteors.remove(meteor)
                   game_state["score"] += 10
                   game_state["meteors_destroyed"] += 1
                   game_state["meteors_destroyed_this_jump"] += 1
                   return True
   return False


def game_over():
  global game_state
  game_state["game_over"] = True
  spaceship["jumping"] = False
  spaceship["attached_to_planet"] = True
  game_state["meteor_wave_active"] = False
  meteors.clear()


def reset_to_planet(planet_index):
  global spaceship, game_state
  spaceship["target_index"] = planet_index
  spaceship["attached_to_planet"] = True
  spaceship["jumping"] = False
  planet = planets[planet_index]
  _, _, _, orbit_radius, speed, _, _ = planet
  angle = (time.time() - start_time) * speed % 360
  angle_rad = math.radians(angle)
  spaceship["x"] = orbit_radius * math.cos(angle_rad)
  spaceship["y"] = orbit_radius * math.sin(angle_rad)
  spaceship["z"] = 30
  game_state["meteor_wave_active"] = False
  game_state["planets_paused"] = False




def reset_game():
  global game_state, spaceship, meteors, start_time
  # Reset game state
  game_state = {
      "level": 1,
      "lives": 3,
      "score": 0,
      "meteors_destroyed": 0,
      "meteor_speed": 0.7,
      "game_over": False,
      "last_meteor_spawn": time.time(),
      "meteors_destroyed_this_jump": 0,
      "camera_mode": "third_person",
      "meteor_wave_active": False,
      "paused_time": 0,
      "planets_paused": False,
      "last_destroyed_pos": None,
      "showing_landing_info": False,
      "landing_info_time": 0,
      "current_planet_info": None,
      "boss_active": False,
      "boss_health": 0
  }
  # Reset spaceship
  spaceship = {
      "x": planets[2][3],
      "y": 0,
      "z": 30,
      "jumping": False,
      "target_index": 2,
      "speed": 1.5,
      "attached_to_planet": True,
      "vertical_offset": 0,
      "max_vertical_offset": 50,
      "jump_start_time": 0,
      "jump_duration": 8.0,
      "current_jump_progress": 0.0
  }
  meteors = []
  start_time = time.time()
  reset_to_planet(2)


def keyboardListener(key, x, y):
  global game_state, spaceship
  try:
      key = key.decode('utf-8').lower()
  except:
      key = key.lower()
  if key == ' ' and game_state["showing_landing_info"]:  # Space key
      game_state["showing_landing_info"] = False


  elif key == 'j':
      if game_state["showing_landing_info"]:
          game_state["showing_landing_info"] = False
      elif not spaceship["jumping"] and not game_state["meteor_wave_active"]:
          spaceship["target_index"] = (spaceship["target_index"] + 1) % len(planets)
          spaceship["jumping"] = True
          spaceship["attached_to_planet"] = False
          game_state["meteors_destroyed_this_jump"] = 0
          game_state["meteor_wave_active"] = True
          game_state["planets_paused"] = True
          game_state["paused_time"] = time.time() - start_time
          game_state["camera_mode"] = "first_person"
          spaceship["jump_start_time"] = time.time()


      # Initialize camera look-at direction
      target_planet = planets[spaceship["target_index"]]
      _, _, _, orbit_radius, speed, _, _ = target_planet
      angle = (game_state["paused_time"] * speed) % 360
      angle_rad = math.radians(angle)
      tx = orbit_radius * math.cos(angle_rad)
      ty = orbit_radius * math.sin(angle_rad)


      # Set initial forward direction
      game_state["forward_direction"] = [
          tx - spaceship["x"],
          ty - spaceship["y"],
          0
      ]
  elif key == 'r' and game_state["game_over"]:
      reset_game()
      return
  elif game_state["game_over"]:
      return
  glutPostRedisplay()




def specialKeyListener(key, x, y):
  global camera_radius, camera_angle_deg


  if game_state["camera_mode"] == "third_person" and not spaceship["jumping"]:
      if key == GLUT_KEY_LEFT:
          camera_angle_deg += 5
      elif key == GLUT_KEY_RIGHT:
          camera_angle_deg -= 5
      elif key == GLUT_KEY_UP:
          camera_radius = max(200, camera_radius - 10)
      elif key == GLUT_KEY_DOWN:
          camera_radius = min(1300, camera_radius + 10)


  glutPostRedisplay()


def mouseMotion(x, y):
  global mouse_x, mouse_y
  mouse_x = x
  mouse_y = y


def mouseClick(button, state, x, y):
   if (button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and
           spaceship["jumping"] and not game_state["game_over"]):
       if destroy_meteor(x, y):
           glutPostRedisplay()




def setupCamera():
   glMatrixMode(GL_PROJECTION)
   glLoadIdentity()
   gluPerspective(fovY, 1.25, 0.5, 2000)
   glMatrixMode(GL_MODELVIEW)
   glLoadIdentity()


   if game_state["camera_mode"] == "first_person" and spaceship["jumping"]:
       if "forward_direction" in game_state:
           fd = game_state["forward_direction"]
           fd_length = math.sqrt(fd[0] ** 2 + fd[1] ** 2 + fd[2] ** 2)
           if fd_length > 0:
               fd = [d / fd_length for d in fd]
               head_position = [
                   spaceship["x"] + fd[0] * 5,
                   spaceship["y"] + fd[1] * 5,
                   spaceship["z"] + spaceship["vertical_offset"] + 5
               ]
               look_at = [
                   head_position[0] + fd[0],
                   head_position[1] + fd[1],
                   head_position[2] + fd[2]
               ]
               gluLookAt(
                   *head_position,
                   *look_at,
                   0, 0, 1
               )
               return


       # Fallback if no forward direction
       head_position = [
           spaceship["x"],
           spaceship["y"],
           spaceship["z"] + spaceship["vertical_offset"] + 10
       ]
       gluLookAt(
           *head_position,
           head_position[0], head_position[1], head_position[2] + 100,
           0, 0, 1
       )
   else:
       # Third-person view
       angle_rad = math.radians(camera_angle_deg)
       cam_x = camera_radius * math.cos(angle_rad)
       cam_y = camera_radius * math.sin(angle_rad)
       cam_z = camera_height
       gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)
def idle():
  updateSpaceship()
  update_meteors()
  glutPostRedisplay()


def showScreen():
  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
  glLoadIdentity()
  glViewport(0, 0, 1200, 900)
  setupCamera()
  glClearColor(0.01, 0.01, 0.05, 1.0)


  drawStars()
  draw_solar_system()
  drawSpaceship()
  draw_meteors()


  # Display HUD
  draw_text(20, 770, f"Level: {game_state['level']} - {planets[spaceship['target_index']][0]}")
  draw_text(20, 740, f"Lives: {game_state['lives']}")
  draw_text(20, 710, f"Score: {game_state['score']}")
  draw_text(20, 680, f"HIT ATLEAST 5 METEORS TO PROGRESS TO NEXT LEVEL!")
  draw_text(20, 650, f"Meteors this jump: {game_state['meteors_destroyed_this_jump']}")


  if spaceship["jumping"]:
      draw_text(400, 50, "CLICK ON METEORS TO DESTROY THEM!", GLUT_BITMAP_TIMES_ROMAN_24)
  if game_state["boss_active"]:
       draw_text(400, 100, f"BOSS HEALTH: {game_state['boss_health']}", GLUT_BITMAP_TIMES_ROMAN_24)


  if game_state["game_over"]:
      if game_state.get("visited_all_planets", False):
          # Special completion message
          glDisable(GL_LIGHTING)
          draw_text(250, 450, "CONGRATULATIONS!", GLUT_BITMAP_TIMES_ROMAN_24)
          draw_text(200, 400, "You have visited all planets of the solar system!", GLUT_BITMAP_HELVETICA_18)
          draw_text(350, 350, f"Final Score: {game_state['score']}", GLUT_BITMAP_HELVETICA_18)
          draw_text(350, 300, "Press R to play again", GLUT_BITMAP_HELVETICA_18)
          glEnable(GL_LIGHTING)
      else:
        draw_text(400, 400, "GAME OVER - Press 'R' to restart", GLUT_BITMAP_TIMES_ROMAN_24)
  if game_state["showing_landing_info"]:
      draw_landing_info()


  glutSwapBuffers()




def main():
  glutInit(sys.argv)
  glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
  glutInitWindowSize(1100, 800)
  glutInitWindowPosition(0, 0)
  glutCreateWindow(b"Planet Hopper - Click to Destroy Meteors")


  glutMotionFunc(mouseMotion)
  glutPassiveMotionFunc(mouseMotion)
  glutMouseFunc(mouseClick)


  glEnable(GL_DEPTH_TEST)
  glEnable(GL_COLOR_MATERIAL)
  glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)


  setupLighting()
  generateStars()
  glutDisplayFunc(showScreen)
  glutKeyboardFunc(keyboardListener)
  glutSpecialFunc(specialKeyListener)
  glutIdleFunc(idle)
  # Start at Earth
  reset_to_planet(2)
  glutMainLoop()


if __name__ == "__main__":
  start_time = time.time()
  main()
